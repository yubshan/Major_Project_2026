"""Ground-truth ray sensors and occupancy-grid observation updates."""

from __future__ import annotations

import math

import numpy as np

from modules.navigation.occupancy_grid import OccupancyGrid
from shared.bresenham import bresenham_line
from shared.coordinate_system import CELL_SIZE_CM, FREE, GRID_HEIGHT, GRID_WIDTH, OCCUPIED

SENSOR_ANGLES = {
    "us_front": 0,
    "us_left45": 45,
    "us_left90": 90,
    "us_right45": -45,
    "us_right90": -90,
}


def raycast(
    ground_truth: np.ndarray,
    start: tuple[int, int],
    angle_degrees: float,
    max_range_cells: int,
) -> tuple[list[tuple[int, int]], bool]:
    radians = math.radians(angle_degrees)
    end = (
        round(start[0] - max_range_cells * math.sin(radians)),
        round(start[1] + max_range_cells * math.cos(radians)),
    )
    visible = []
    hit = False
    for row, col in bresenham_line(start, end)[1:]:
        if not (0 <= row < GRID_HEIGHT and 0 <= col < GRID_WIDTH):
            hit = True
            break
        visible.append((row, col))
        if ground_truth[row, col] == OCCUPIED:
            hit = True
            break
    return visible, hit


def sense(
    ground_truth: np.ndarray,
    robot: tuple[int, int],
    heading: int,
    max_range_cells: int,
    timestamp_ms: int,
) -> dict:
    packet: dict = {
        "timestamp_ms": timestamp_ms,
        "max_range_cm": max_range_cells * CELL_SIZE_CM,
        "hits": {},
        "rays": {},
    }
    for name, relative_angle in SENSOR_ANGLES.items():
        cells, hit = raycast(ground_truth, robot, heading + relative_angle, max_range_cells)
        distance_cells = len(cells) if hit else max_range_cells
        packet[name] = float(distance_cells * CELL_SIZE_CM)
        packet["hits"][name] = hit
        packet["rays"][name] = cells

    # A compact forward-facing 8x8-compatible depth representation.
    tof = []
    packet["tof_rays"] = []
    packet["tof_hits"] = []
    tof_columns = []
    for col_index in range(8):
        relative = -28 + col_index * 8
        cells, hit = raycast(ground_truth, robot, heading + relative, max_range_cells)
        tof_columns.append(float((len(cells) if hit else max_range_cells) * CELL_SIZE_CM))
        packet["tof_rays"].append(cells)
        packet["tof_hits"].append(hit)
    for row_index in range(8):
        # Rows represent vertical pixels; a 2D floor map shares horizontal depth.
        tof.append(list(tof_columns))
    packet["tof_grid"] = tof
    return packet


def apply_observation(grid: OccupancyGrid, packet: dict, robot: tuple[int, int]) -> int:
    """Apply explicit hit/no-hit rays and return the number of newly known cells."""
    before = int(np.count_nonzero(grid.data != 2))
    grid.set_cell(*robot, FREE)
    for name in SENSOR_ANGLES:
        cells = packet["rays"][name]
        if not cells:
            continue
        endpoint = cells[-1]
        grid.update_ray(robot, endpoint, obstacle_detected=bool(packet["hits"][name]))
    for cells, hit in zip(packet.get("tof_rays", []), packet.get("tof_hits", [])):
        if cells:
            grid.update_ray(robot, cells[-1], obstacle_detected=bool(hit))
    return int(np.count_nonzero(grid.data != 2)) - before
