# modules/decision_logic/rl_env/sar_explore_env.py
#
# SARExploreEnv — custom Gymnasium environment for Project Drishya
#
# The robot starts at the centre of a 50×50 occupancy grid (all cells UNKNOWN).
# Its goal is to efficiently explore the environment while avoiding obstacles.
# A PPO agent learns an exploration policy that is then used by the RLExplore
# behavior-tree node at runtime.
#
# Coordinate convention (matches shared/coordinate_system.py):
#   Grid centre  = (row 25, col 25)  ↔  world (0, 0)
#   Action 0 = Forward (+row)
#   Action 1 = Left    (+col)
#   Action 2 = Backward(-row)
#   Action 3 = Right   (-col)

import numpy as np
# pyrefly: ignore [missing-import]
import gymnasium as gym
# pyrefly: ignore [missing-import]
from gymnasium import spaces
from shared.coordinate_system import (
    GRID_WIDTH, GRID_HEIGHT, GRID_CENTER_X, GRID_CENTER_Y,
    FREE, OCCUPIED, UNKNOWN,
)

# ---------------------------------------------------------------------------
# Environment constants
# ---------------------------------------------------------------------------
MAX_STEPS          = 500       # episode length cap
OBSTACLE_DENSITY   = 0.08     # fraction of cells pre-set as walls
SENSOR_RANGE       = 5        # cells the robot can "see" around itself
COLLISION_PENALTY  = -5.0
TIME_PENALTY       = -0.05
EXPLORE_REWARD     = 1.0      # per newly revealed FREE cell
VICTIM_REWARD      = 50.0     # when victim cell is stepped near
VICTIM_RANGE       = 3        # cells from victim counts as "found"

# Action → (drow, dcol)
ACTION_DELTAS = {
    0: (-1,  0),   # Forward  (robot faces +X which is -row in our grid)
    1: ( 0, -1),   # Left
    2: ( 1,  0),   # Backward
    3: ( 0,  1),   # Right
}

ACTION_NAMES = {0: "FORWARD", 1: "LEFT", 2: "BACKWARD", 3: "RIGHT"}


class SARExploreEnv(gym.Env):
    """
    Gymnasium environment for Search-And-Rescue exploration.

    Observation space
    -----------------
    A flattened view of:
      - Occupancy grid  50×50  (values: FREE=0, OCCUPIED=1, UNKNOWN=2)
      - Robot position  (row_norm, col_norm)  in [0, 1]
      - Victim distance (euclidean, normalised to grid diagonal)

    Total observation size: 50*50 + 2 + 1 = 2503

    Action space
    ------------
    Discrete(4) — Forward / Left / Backward / Right
    """

    metadata = {"render_modes": ["ansi"]}

    def __init__(self, render_mode=None):
        super().__init__()
        self.render_mode = render_mode

        obs_size = GRID_WIDTH * GRID_HEIGHT + 3   # grid flat + (row_n, col_n, victim_dist)
        self.observation_space = spaces.Box(
            low   = 0.0,
            high  = 1.0,
            shape = (obs_size,),
            dtype = np.float32,
        )
        self.action_space = spaces.Discrete(4)

        # Internal state (reset each episode)
        self._grid     : np.ndarray = None
        self._gt_grid  : np.ndarray = None   # ground-truth (hidden)
        self._robot_row: int        = GRID_CENTER_Y
        self._robot_col: int        = GRID_CENTER_X
        self._victim_row: int       = 0
        self._victim_col: int       = 0
        self._step_count: int       = 0
        self._explored_cells: set   = set()

    # ------------------------------------------------------------------
    # Gymnasium API
    # ------------------------------------------------------------------

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        rng = self.np_random

        # Build ground-truth grid (robot knows nothing about it yet)
        self._gt_grid = np.zeros((GRID_HEIGHT, GRID_WIDTH), dtype=np.int8)
        n_obstacles   = int(GRID_WIDTH * GRID_HEIGHT * OBSTACLE_DENSITY)
        obs_indices   = rng.choice(GRID_WIDTH * GRID_HEIGHT, size=n_obstacles, replace=False)
        for idx in obs_indices:
            r, c = divmod(int(idx), GRID_WIDTH)
            # Don't block the starting position
            if not (r == GRID_CENTER_Y and c == GRID_CENTER_X):
                self._gt_grid[r, c] = OCCUPIED

        # Robot's perceived grid starts UNKNOWN
        self._grid = np.full((GRID_HEIGHT, GRID_WIDTH), UNKNOWN, dtype=np.int8)

        # Robot starts at centre
        self._robot_row = GRID_CENTER_Y
        self._robot_col = GRID_CENTER_X
        self._step_count = 0
        self._explored_cells = set()

        # Place victim in a random free cell (biased toward far corners)
        while True:
            vr = int(rng.integers(5, GRID_HEIGHT - 5))
            vc = int(rng.integers(5, GRID_WIDTH - 5))
            if self._gt_grid[vr, vc] == FREE:
                # Not too close to start
                if abs(vr - GRID_CENTER_Y) + abs(vc - GRID_CENTER_X) > 10:
                    self._victim_row, self._victim_col = vr, vc
                    break

        # Initial sensor reveal
        self._reveal_around_robot()

        return self._get_obs(), {}

    def step(self, action: int):
        assert self.action_space.contains(action), f"Invalid action: {action}"

        dr, dc = ACTION_DELTAS[action]
        new_row = self._robot_row + dr
        new_col = self._robot_col + dc
        self._step_count += 1

        reward = TIME_PENALTY
        terminated = False
        truncated   = self._step_count >= MAX_STEPS

        # Boundary / obstacle check
        if (
            0 <= new_row < GRID_HEIGHT
            and 0 <= new_col < GRID_WIDTH
            and self._gt_grid[new_row, new_col] != OCCUPIED
        ):
            self._robot_row = new_row
            self._robot_col = new_col
        else:
            reward += COLLISION_PENALTY

        # Reveal cells around new position and reward exploration
        before = len(self._explored_cells)
        self._reveal_around_robot()
        newly_explored = len(self._explored_cells) - before
        reward += newly_explored * EXPLORE_REWARD

        # Check if near victim
        dist_to_victim = abs(self._robot_row - self._victim_row) + \
                         abs(self._robot_col - self._victim_col)
        if dist_to_victim <= VICTIM_RANGE:
            reward += VICTIM_REWARD
            terminated = True

        obs  = self._get_obs()
        info = {
            "action_name":    ACTION_NAMES[action],
            "explored_cells": len(self._explored_cells),
            "explore_pct":    100.0 * len(self._explored_cells) / (GRID_WIDTH * GRID_HEIGHT),
            "victim_dist":    dist_to_victim,
            "step":           self._step_count,
        }

        return obs, reward, terminated, truncated, info

    def render(self):
        if self.render_mode != "ansi":
            return
        symbols = {FREE: ".", OCCUPIED: "#", UNKNOWN: "?"}
        lines   = []
        for r in range(GRID_HEIGHT):
            row_str = ""
            for c in range(GRID_WIDTH):
                if r == self._robot_row and c == self._robot_col:
                    row_str += "R"
                elif r == self._victim_row and c == self._victim_col:
                    row_str += "V"
                else:
                    row_str += symbols[self._grid[r, c]]
            lines.append(row_str)
        return "\n".join(lines)

    def close(self):
        pass

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _reveal_around_robot(self):
        """Mark cells within SENSOR_RANGE of the robot using ground truth."""
        for dr in range(-SENSOR_RANGE, SENSOR_RANGE + 1):
            for dc in range(-SENSOR_RANGE, SENSOR_RANGE + 1):
                r = self._robot_row + dr
                c = self._robot_col + dc
                if 0 <= r < GRID_HEIGHT and 0 <= c < GRID_WIDTH:
                    gt_val = self._gt_grid[r, c]
                    self._grid[r, c] = gt_val
                    if gt_val == FREE:
                        self._explored_cells.add((r, c))

    def _get_obs(self) -> np.ndarray:
        """Build the flat observation vector."""
        grid_flat = self._grid.flatten().astype(np.float32) / 2.0   # normalise to [0,1]

        row_norm  = self._robot_row / (GRID_HEIGHT - 1)
        col_norm  = self._robot_col / (GRID_WIDTH  - 1)

        max_manhattan_distance = (GRID_HEIGHT - 1) + (GRID_WIDTH - 1)
        dist_norm = (
            abs(self._robot_row - self._victim_row) +
            abs(self._robot_col - self._victim_col)
        ) / max_manhattan_distance

        return np.concatenate(
            [grid_flat, [row_norm, col_norm, dist_norm]],
            dtype=np.float32,
        )

    # ------------------------------------------------------------------
    # Utility (used by brain.py at runtime)
    # ------------------------------------------------------------------

    def get_action_name(self, action: int) -> str:
        return ACTION_NAMES.get(action, "UNKNOWN")

    @staticmethod
    def action_to_motor_command(action: int, speed: int = 150) -> dict:
        """
        Translate a discrete action to a motor command dict matching
        the blackboard key 'state/motor_command'.
        """
        commands = {
            0: {"left_speed":  speed, "right_speed":  speed, "duration_ms": 200},  # Forward
            1: {"left_speed": -speed, "right_speed":  speed, "duration_ms": 150},  # Left
            2: {"left_speed": -speed, "right_speed": -speed, "duration_ms": 200},  # Backward
            3: {"left_speed":  speed, "right_speed": -speed, "duration_ms": 150},  # Right
        }
        return commands.get(action, {"left_speed": 0, "right_speed": 0, "duration_ms": 0})
