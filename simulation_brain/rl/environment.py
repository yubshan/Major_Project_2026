"""Gymnasium adapter backed by the same controller used by the visual demo."""

from __future__ import annotations

import numpy as np
import gymnasium as gym
from gymnasium import spaces

from shared.coordinate_system import GRID_HEIGHT, GRID_WIDTH
from simulation_brain.controller import SimulationController
from simulation_brain.rl.features import build_observation


class SARSimulationEnv(gym.Env):
    """Train exploration-sector selection without exposing hidden ground truth."""

    metadata = {"render_modes": []}

    def __init__(self, scenario: str = "random", max_steps: int = 500):
        super().__init__()
        self.scenario_name = scenario
        self.max_steps = max_steps
        self.action_space = spaces.Discrete(4)
        # Grid + row/col/heading + five ranges + coverage + four frontier-sector counts.
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(GRID_HEIGHT * GRID_WIDTH + 13,),
            dtype=np.float32,
        )
        self.controller: SimulationController | None = None
        self._seed = 0

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            self._seed = int(seed)
        scenario = (options or {}).get("scenario", self.scenario_name)
        self.controller = SimulationController(scenario=scenario, seed=self._seed)
        # Publish the initial partial observation before returning state.
        self.controller._publish_observation()
        self.controller.metrics.explored_cells = int(
            np.count_nonzero(self.controller.occupancy.data != 2)
        )
        self.controller.metrics.coverage_pct = (
            100.0 * self.controller.metrics.explored_cells / (GRID_HEIGHT * GRID_WIDTH)
        )
        return self._observation(), self._info()

    def step(self, action):
        if self.controller is None:
            raise RuntimeError("reset() must be called before step()")
        previous = self.controller.metrics.to_dict()
        self.controller.exploration_sector_override = int(action)
        result = self.controller.step()
        current = self.controller.metrics.to_dict()

        explored_delta = current["explored_cells"] - previous["explored_cells"]
        collision_delta = current["collisions"] - previous["collisions"]
        reward = explored_delta * 1.0 - 0.02 - collision_delta * 5.0
        if explored_delta == 0:
            reward -= 0.1
        if result.detected:
            reward += 2.0
        if current["rescued"]:
            reward += 100.0

        terminated = bool(current["rescued"] or current["termination_reason"] == "map_fully_explored")
        truncated = bool(current["steps"] >= self.max_steps or current["termination_reason"] == "step_limit")
        return self._observation(), float(reward), terminated, truncated, self._info()

    def _observation(self) -> np.ndarray:
        assert self.controller is not None
        return build_observation(self.controller)

    def _info(self) -> dict:
        assert self.controller is not None
        info = self.controller.metrics.to_dict()
        # Wall-clock time is useful for the dashboard but would make seeded Gym
        # transitions non-deterministic and is therefore excluded from env info.
        info.pop("elapsed_seconds", None)
        return info

    def close(self):
        self.controller = None
