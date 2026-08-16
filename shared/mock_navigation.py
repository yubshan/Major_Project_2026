# shared/mock_navigation.py
#
# Purpose : Provides pre-built navigation states (robot pose, occupancy grids, paths,
#           and sensor proximity readings) so Teammate B can test decision rules
#           without the Navigation module or Pygame simulator running.
#
# Owner   : Teammate A (Navigation Lead)  ← reviewed & filled by decision_logic branch
# Used by : modules/decision_logic/ (behavior tree nodes + RL env + demo_runner)

import numpy as np
from shared.coordinate_system import (
    GRID_WIDTH, GRID_HEIGHT, GRID_CENTER_X, GRID_CENTER_Y,
    FREE, OCCUPIED, UNKNOWN,
)

# ---------------------------------------------------------------------------
# Blackboard keys written by the real navigator:
#   "navigation/robot_pose"       → {x, y, heading}
#   "navigation/occupancy_grid"   → numpy 50×50 int8 (FREE=0, OCCUPIED=1, UNKNOWN=2)
#   "navigation/planned_path"     → list of (row, col) tuples | []
#   "navigation/target_waypoint"  → (row, col) | None
#   "sensor/proximity"            → {us_front, us_left45, us_left90,
#                                     us_right45, us_right90}  (cm, 0 = invalid)
# ---------------------------------------------------------------------------

def _blank_grid() -> np.ndarray:
    """50×50 grid entirely UNKNOWN."""
    return np.full((GRID_HEIGHT, GRID_WIDTH), UNKNOWN, dtype=np.int8)


def _partially_explored_grid(explore_fraction: float = 0.4) -> np.ndarray:
    """Grid with a square explored region around the centre."""
    grid = _blank_grid()
    half = int((GRID_WIDTH * explore_fraction) / 2)
    r0 = GRID_CENTER_Y - half
    r1 = GRID_CENTER_Y + half
    c0 = GRID_CENTER_X - half
    c1 = GRID_CENTER_X + half
    grid[r0:r1, c0:c1] = FREE
    # Scatter some walls
    for pos in [(r0 + 2, c0 + 5), (r0 + 3, c0 + 5), (r1 - 3, c1 - 4)]:
        grid[pos] = OCCUPIED
    return grid


def get_mock_nav_state(scenario: str) -> dict:
    """
    Return a fake navigation state bundle for the given scenario.

    Parameters
    ----------
    scenario : str
        One of:
          "start"           — robot at origin, map fully unknown
          "exploring"       — robot has explored ~40% of the map, no target
          "obstacle_ahead"  — obstacle very close in front
          "target_locked"   — active waypoint set, path planned
          "near_victim"     — robot close to last detected human position

    Returns
    -------
    dict with keys:
        robot_pose         : {x: float, y: float, heading: float}   (cm, degrees)
        occupancy_grid     : np.ndarray shape (50, 50) dtype int8
        planned_path       : list of (row, col) tuples
        target_waypoint    : (row, col) or None
        proximity          : {us_front, us_left45, us_left90, us_right45, us_right90} cm
    """

    if scenario == "start":
        return {
            "robot_pose": {"x": 0.0, "y": 0.0, "heading": 0.0},
            "occupancy_grid": _blank_grid(),
            "planned_path": [],
            "target_waypoint": None,
            "proximity": {
                "us_front":   120,
                "us_left45":  100,
                "us_left90":   90,
                "us_right45": 110,
                "us_right90":  95,
            },
        }

    elif scenario == "exploring":
        grid = _partially_explored_grid(0.4)
        return {
            "robot_pose": {"x": 30.0, "y": 10.0, "heading": 45.0},
            "occupancy_grid": grid,
            "planned_path": [],
            "target_waypoint": None,
            "proximity": {
                "us_front":   80,
                "us_left45":  70,
                "us_left90":  60,
                "us_right45": 85,
                "us_right90": 90,
            },
        }

    elif scenario == "obstacle_ahead":
        grid = _partially_explored_grid(0.3)
        return {
            "robot_pose": {"x": 20.0, "y": 0.0, "heading": 0.0},
            "occupancy_grid": grid,
            "planned_path": [],
            "target_waypoint": None,
            "proximity": {
                "us_front":   12,   # ← dangerously close!
                "us_left45":  30,
                "us_left90":  60,
                "us_right45": 25,
                "us_right90": 55,
            },
        }

    elif scenario == "target_locked":
        grid = _partially_explored_grid(0.5)
        target = (GRID_CENTER_Y - 5, GRID_CENTER_X + 8)
        # Simple straight path from centre to target
        path = [(GRID_CENTER_Y - i, GRID_CENTER_X + i) for i in range(6)]
        return {
            "robot_pose": {"x": 0.0, "y": 0.0, "heading": 30.0},
            "occupancy_grid": grid,
            "planned_path": path,
            "target_waypoint": target,
            "proximity": {
                "us_front":   90,
                "us_left45":  80,
                "us_left90":  70,
                "us_right45": 85,
                "us_right90": 75,
            },
        }

    elif scenario == "near_victim":
        grid = _partially_explored_grid(0.6)
        return {
            "robot_pose": {"x": 110.0, "y": -35.0, "heading": 315.0},
            "occupancy_grid": grid,
            "planned_path": [],
            "target_waypoint": None,
            "proximity": {
                "us_front":   55,
                "us_left45":  50,
                "us_left90":  45,
                "us_right45": 60,
                "us_right90": 65,
            },
        }

    else:
        raise ValueError(
            f"Unknown scenario '{scenario}'. "
            f"Valid options: start | exploring | obstacle_ahead | target_locked | near_victim"
        )


def get_all_scenarios() -> list:
    """Return all available navigation scenario names."""
    return ["start", "exploring", "obstacle_ahead", "target_locked", "near_victim"]