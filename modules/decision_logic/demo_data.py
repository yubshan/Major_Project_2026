"""Deterministic demo fixtures for the decision-logic module."""

import numpy as np

from modules.decision_logic.contracts import now_ms
from shared.coordinate_system import (
    FREE,
    GRID_CENTER_X,
    GRID_CENTER_Y,
    GRID_HEIGHT,
    GRID_WIDTH,
    OCCUPIED,
    UNKNOWN,
)


def get_mock_detection(scenario: str) -> dict:
    """Return a detection packet for a named demo scenario."""
    timestamp = now_ms()
    scenarios = {
        "no_human": (0.0, 0.0, 0.08),
        "weak_signal": (80.0, 30.0, 0.52),
        "strong_detection": (120.0, -40.0, 0.91),
        "approaching": (50.0, 10.0, 0.74),
    }
    try:
        human_x, human_y, confidence = scenarios[scenario]
    except KeyError as exc:
        raise ValueError(
            f"Unknown detection scenario {scenario!r}; choose from {tuple(scenarios)}"
        ) from exc
    return {
        "human_x": human_x,
        "human_y": human_y,
        "confidence": confidence,
        "timestamp_ms": timestamp,
    }


def _grid(explore_fraction: float = 0.0) -> np.ndarray:
    grid = np.full((GRID_HEIGHT, GRID_WIDTH), UNKNOWN, dtype=np.int8)
    if explore_fraction <= 0:
        return grid

    half = int(GRID_WIDTH * explore_fraction / 2)
    row_start, row_end = GRID_CENTER_Y - half, GRID_CENTER_Y + half
    col_start, col_end = GRID_CENTER_X - half, GRID_CENTER_X + half
    grid[row_start:row_end, col_start:col_end] = FREE
    for row, col in (
        (row_start + 2, col_start + 5),
        (row_start + 3, col_start + 5),
        (row_end - 3, col_end - 4),
    ):
        grid[row, col] = OCCUPIED
    return grid


def _proximity(front: int, left45: int, left90: int, right45: int, right90: int) -> dict:
    return {
        "us_front": front,
        "us_left45": left45,
        "us_left90": left90,
        "us_right45": right45,
        "us_right90": right90,
    }


def get_mock_nav_state(scenario: str) -> dict:
    """Return navigation state for a named demo scenario."""
    timestamp = now_ms()
    scenarios = {
        "start": {
            "robot_pose": {
                "x": 0.0, "y": 0.0, "heading": 0.0, "timestamp_ms": timestamp
            },
            "occupancy_grid": _grid(),
            "planned_path": [],
            "target_waypoint": None,
            "proximity": {**_proximity(120, 100, 90, 110, 95), "timestamp_ms": timestamp},
        },
        "exploring": {
            "robot_pose": {
                "x": 30.0, "y": 10.0, "heading": 45.0, "timestamp_ms": timestamp
            },
            "occupancy_grid": _grid(0.4),
            "planned_path": [],
            "target_waypoint": None,
            "proximity": {**_proximity(80, 70, 60, 85, 90), "timestamp_ms": timestamp},
        },
        "obstacle_ahead": {
            "robot_pose": {
                "x": 20.0, "y": 0.0, "heading": 0.0, "timestamp_ms": timestamp
            },
            "occupancy_grid": _grid(0.3),
            "planned_path": [],
            "target_waypoint": None,
            "proximity": {**_proximity(12, 30, 60, 25, 55), "timestamp_ms": timestamp},
        },
        "target_locked": {
            "robot_pose": {
                "x": 0.0, "y": 0.0, "heading": 30.0, "timestamp_ms": timestamp
            },
            "occupancy_grid": _grid(0.5),
            "planned_path": [
                (GRID_CENTER_Y - step, GRID_CENTER_X + step) for step in range(6)
            ],
            "target_waypoint": (GRID_CENTER_Y - 5, GRID_CENTER_X + 8),
            "proximity": {**_proximity(90, 80, 70, 85, 75), "timestamp_ms": timestamp},
        },
        "near_victim": {
            "robot_pose": {
                "x": 110.0, "y": -35.0, "heading": 315.0, "timestamp_ms": timestamp
            },
            "occupancy_grid": _grid(0.6),
            "planned_path": [],
            "target_waypoint": None,
            "proximity": {**_proximity(55, 50, 45, 60, 65), "timestamp_ms": timestamp},
        },
    }
    try:
        return scenarios[scenario]
    except KeyError as exc:
        raise ValueError(
            f"Unknown navigation scenario {scenario!r}; choose from {tuple(scenarios)}"
        ) from exc
