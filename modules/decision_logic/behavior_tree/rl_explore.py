# modules/decision_logic/behavior_tree/rl_explore.py
#
# RLExplore — Behavior Tree node (Priority 4)
#
# When no emergency, no victim, and no active waypoint exists, this node
# calls the trained PPO policy to decide the robot's next exploration move.
#
# If no trained model is found, it falls back to a heuristic: move to the
# direction with the most UNKNOWN cells nearby (frontier exploration).
#
# Always returns RUNNING (exploration is ongoing) unless the occupancy grid
# is fully explored, in which case it returns FAILURE to fall through to Idle.

import os
import numpy as np
import py_trees

from modules.decision_logic.rl_env.sar_explore_env import (
    SARExploreEnv, ACTION_NAMES,
)
from shared.coordinate_system import (
    GRID_WIDTH, GRID_HEIGHT, GRID_CENTER_X, GRID_CENTER_Y, UNKNOWN,
)

# Path to the saved PPO checkpoint
DEFAULT_MODEL_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "models", "ppo_sar_explore.zip"
))


def _heuristic_action(grid: np.ndarray, robot_row: int, robot_col: int) -> int:
    """
    Fallback: pick the action whose direction has the most UNKNOWN cells
    in a look-ahead window of 3 cells.
    """
    deltas = {
        0: (-1,  0),   # Forward
        1: ( 0, -1),   # Left
        2: ( 1,  0),   # Backward
        3: ( 0,  1),   # Right
    }
    best_action  = 0
    best_unknown = -1

    for action, (dr, dc) in deltas.items():
        count = 0
        for step in range(1, 4):
            r = robot_row + dr * step
            c = robot_col + dc * step
            if 0 <= r < GRID_HEIGHT and 0 <= c < GRID_WIDTH:
                if grid[r, c] == UNKNOWN:
                    count += 1
        if count > best_unknown:
            best_unknown  = count
            best_action   = action

    return best_action


class RLExplore(py_trees.behaviour.Behaviour):
    """
    Uses a trained PPO policy to explore the unknown environment.
    Falls back to heuristic frontier exploration if no model is available.
    """

    def __init__(self, blackboard, model_path: str = None, name: str = "RLExplore"):
        super().__init__(name=name)
        self.bb = blackboard
        self._model_path = os.path.abspath(model_path) if model_path else DEFAULT_MODEL_PATH
        self._model = None
        self._model_loaded = False

    def setup(self, **kwargs) -> None:
        """Called once before the first tick — try to load the PPO model."""
        self._try_load_model()

    def _try_load_model(self):
        if self._model_loaded:
            return
        try:
            from stable_baselines3 import PPO
            if os.path.isfile(self._model_path):
                self._model = PPO.load(self._model_path)
                self.logger.info(f"PPO model loaded from {self._model_path}")
            else:
                self.logger.warning(
                    f"No trained model at {self._model_path} — using heuristic"
                )
        except ImportError:
            self.logger.warning("stable-baselines3 not installed — using heuristic fallback")
        self._model_loaded = True

    def update(self) -> py_trees.common.Status:
        self._try_load_model()

        grid    = self.bb.get("navigation/occupancy_grid")
        pose    = self.bb.get("navigation/robot_pose")

        if grid is None or pose is None:
            # No environment data — use heuristic on blank grid
            grid    = np.full((GRID_HEIGHT, GRID_WIDTH), UNKNOWN, dtype=np.int8)
            pose    = {"x": 0.0, "y": 0.0, "heading": 0.0}

        from shared.coordinate_system import world_to_grid
        robot_row, robot_col = world_to_grid(pose["x"], pose["y"])

        # Check if fully explored
        unknown_count = int(np.sum(grid == UNKNOWN))
        if unknown_count == 0:
            self.feedback_message = "Map fully explored"
            return py_trees.common.Status.FAILURE

        # Choose action
        if self._model is not None:
            # Build a lightweight observation for the PPO policy
            grid_flat = grid.flatten().astype(np.float32) / 2.0
            row_norm  = robot_row / (GRID_HEIGHT - 1)
            col_norm  = robot_col / (GRID_WIDTH  - 1)
            obs       = np.concatenate([grid_flat, [row_norm, col_norm, 0.5]], dtype=np.float32)
            action, _ = self._model.predict(obs, deterministic=True)
            action    = int(action)
            source    = "PPO"
        else:
            action = _heuristic_action(grid, robot_row, robot_col)
            source = "Heuristic"

        motor_cmd = SARExploreEnv.action_to_motor_command(action)
        action_name = ACTION_NAMES.get(action, "?")

        self.bb.set("state/motor_command", motor_cmd)
        self.bb.set("state/bt_status",
                    f"RL_EXPLORE [{source}] → {action_name} "
                    f"(unknown={unknown_count} cells)")

        explore_pct = 100.0 * (1 - unknown_count / (GRID_WIDTH * GRID_HEIGHT))
        self.feedback_message = (
            f"[{source}] action={action_name}, "
            f"explored={explore_pct:.1f}%, unknown={unknown_count}"
        )
        return py_trees.common.Status.RUNNING
