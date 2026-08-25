"""Versioned policy observation shared by training and runtime inference."""

import numpy as np

from modules.decision_logic.contracts import DETECTION_RESULT, PROXIMITY
from shared.coordinate_system import GRID_HEIGHT, GRID_WIDTH
from simulation_brain.planning import reachable_frontiers


OBSERVATION_SCHEMA = "house-rescue-v2"
GRID_VALUES = GRID_HEIGHT * GRID_WIDTH
FRONTIER_SLICE = slice(GRID_VALUES + 9, GRID_VALUES + 13)
OBSERVATION_SIZE = GRID_VALUES + 17


def deterministic_frontier_action(observation: np.ndarray) -> int:
    """Convert the strongest absolute frontier sector to a relative movement action."""
    sector = int(np.argmax(observation[FRONTIER_SLICE]))
    desired_heading = (0, 90, 180, 270)[sector]
    heading = int(round(float(observation[GRID_VALUES + 2]) * 270.0)) % 360
    turn = (desired_heading - heading) % 360
    return {0: 0, 90: 1, 180: 2, 270: 3}[turn]


def build_observation(
    controller,
    *,
    victim_confirmed: bool | None = None,
    previous_collision: bool = False,
) -> np.ndarray:
    """Build the 2,517-value v2 observation without leaking hidden geometry."""
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
    detection = controller.blackboard.get(DETECTION_RESULT, {})
    confidence_value = float(detection.get("confidence", 0.0)) if isinstance(detection, dict) else 0.0
    confidence = np.asarray([np.clip(confidence_value, 0.0, 1.0)], dtype=np.float32)
    if victim_confirmed is None:
        victim_confirmed = confidence_value >= controller.config.victim_confirm_threshold
    relative = np.zeros(2, dtype=np.float32)
    if victim_confirmed:
        victim = controller.scenario.victim
        relative[:] = (
            (victim[0] - row) / (GRID_HEIGHT - 1),
            (victim[1] - col) / (GRID_WIDTH - 1),
        )
    collision = np.asarray([float(previous_collision)], dtype=np.float32)
    observation = np.concatenate(
        (grid, pose, proximity, coverage, sector_counts, confidence, relative, collision),
        dtype=np.float32,
    )
    if observation.shape != (OBSERVATION_SIZE,):
        raise RuntimeError(f"Invalid {OBSERVATION_SCHEMA} observation shape: {observation.shape}")
    return observation
