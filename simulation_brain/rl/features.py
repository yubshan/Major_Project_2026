"""Policy observation shared by training and runtime inference."""

import numpy as np

from modules.decision_logic.contracts import PROXIMITY
from shared.coordinate_system import GRID_HEIGHT, GRID_WIDTH
from simulation_brain.planning import reachable_frontiers


def build_observation(controller) -> np.ndarray:
    """Build a 2513-value observation without hidden map or victim information."""
    grid = controller.occupancy.data.astype(np.float32).flatten() / 2.0
    row, col = controller.robot
    pose = np.asarray(
        [row / (GRID_HEIGHT - 1), col / (GRID_WIDTH - 1), controller.heading / 270.0],
        dtype=np.float32,
    )
    packet = controller.blackboard.get(PROXIMITY, {})
    max_range = max(1.0, float(packet.get("max_range_cm", 1.0)))
    proximity = np.asarray(
        [packet.get(name, max_range) / max_range for name in (
            "us_front", "us_left45", "us_left90", "us_right45", "us_right90"
        )],
        dtype=np.float32,
    )
    coverage = np.asarray([controller.metrics.coverage_pct / 100.0], dtype=np.float32)
    sector_counts = np.zeros(4, dtype=np.float32)
    for cell, _, _ in reachable_frontiers(controller.occupancy.data, controller.robot):
        dr, dc = cell[0] - row, cell[1] - col
        if dc >= abs(dr):
            sector_counts[0] += 1
        elif -dr >= abs(dc):
            sector_counts[1] += 1
        elif -dc >= abs(dr):
            sector_counts[2] += 1
        else:
            sector_counts[3] += 1
    if sector_counts.max() > 0:
        sector_counts /= sector_counts.max()
    return np.concatenate((grid, pose, proximity, coverage, sector_counts), dtype=np.float32)

