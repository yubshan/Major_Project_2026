"""Gymnasium environment for direct, collision-learning house-rescue training."""

from __future__ import annotations

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from modules.decision_logic.contracts import DECISION_STATE, SIMULATION_METRICS, now_ms
from shared.coordinate_system import FREE, GRID_HEIGHT, GRID_WIDTH
from simulation_brain.controller import HEADINGS, SimulationController
from simulation_brain.rl.features import OBSERVATION_SIZE, build_observation
from simulation_brain.scenarios import HOUSE_SCENARIOS

HEADING_DELTAS = {heading: delta for delta, heading in HEADINGS.items()}
ACTION_TURNS = (0, 90, 180, -90)


class SARSimulationEnv(gym.Env):
    """Let PPO attempt adjacent moves while keeping hidden walls out of observations.

    This training environment intentionally permits collision *attempts*. The visual
    and headless deployment controller remains protected by its Behavior Tree,
    collision validator, and A* planner.
    """

    metadata = {"render_modes": []}

    def __init__(
        self,
        scenario: str = "studio-apartment",
        max_steps: int = 750,
        *,
        base_seed: int = 7,
        scenario_pool: tuple[str, ...] | None = None,
    ):
        super().__init__()
        self.scenario_name = scenario
        self.scenario_pool = tuple(scenario_pool or ())
        self.max_steps = int(max_steps)
        self.base_seed = int(base_seed)
        self.action_space = spaces.Discrete(4)
        low = np.zeros(OBSERVATION_SIZE, dtype=np.float32)
        low[-3:-1] = -1.0  # confirmed victim-relative row/column may be signed.
        self.observation_space = spaces.Box(
            low=low,
            high=np.ones(OBSERVATION_SIZE, dtype=np.float32),
            dtype=np.float32,
        )
        self.controller: SimulationController | None = None
        self._seed = self.base_seed
        self._reset_index = 0
        self._victim_confirmed = False
        self._previous_collision = False
        self._collision_streak = 0
        self._episode_reward = 0.0
        self._detection_step: int | None = None

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        options = options or {}
        if seed is not None:
            self._seed = int(seed)
        else:
            self._seed = self.base_seed

        if self.scenario_pool:
            pool_index = self._reset_index % len(self.scenario_pool)
            cycle = self._reset_index // len(self.scenario_pool)
            scenario = self.scenario_pool[pool_index]
            scenario_seed = self._seed + cycle
        else:
            scenario = options.get("scenario", self.scenario_name)
            scenario_seed = int(options.get("scenario_seed", self._seed))
        self._reset_index += 1

        self.controller = SimulationController(scenario=scenario, seed=scenario_seed)
        self._victim_confirmed = False
        self._previous_collision = False
        self._collision_streak = 0
        self._episode_reward = 0.0
        self._detection_step = None
        self.controller._publish_observation()
        self._refresh_metrics()
        return self._observation(), self._info()

    def step(self, action):
        if self.controller is None:
            raise RuntimeError("reset() must be called before step()")
        action = int(action)
        if not self.action_space.contains(action):
            raise ValueError(f"Invalid action {action}; expected 0, 1, 2, or 3")

        controller = self.controller
        previous_explored = controller.metrics.explored_cells
        previous_distance = self._victim_distance()
        desired_heading = (controller.heading + ACTION_TURNS[action]) % 360
        dr, dc = HEADING_DELTAS[desired_heading]
        attempted = (controller.robot[0] + dr, controller.robot[1] + dc)
        controller.heading = desired_heading

        collision = not (
            0 <= attempted[0] < GRID_HEIGHT
            and 0 <= attempted[1] < GRID_WIDTH
            and controller.ground_truth[attempted] == FREE
        )
        if collision:
            controller.metrics.collisions += 1
            self._collision_streak += 1
        else:
            controller.robot = attempted
            self._collision_streak = 0
        self._previous_collision = collision

        _, signal_confirmed = controller._publish_observation()
        first_confirmation = bool(signal_confirmed and not self._victim_confirmed)
        if first_confirmation:
            self._victim_confirmed = True
            self._detection_step = controller.metrics.steps + 1
            controller.metrics.victim_detections += 1

        controller.metrics.steps += 1
        self._refresh_metrics()
        newly_explored = controller.metrics.explored_cells - previous_explored

        reward = 0.05 * newly_explored - 0.02
        if newly_explored == 0:
            reward -= 0.1
        if collision:
            reward -= 8.0 + 0.5 * max(0, self._collision_streak - 1)
        if first_confirmation:
            reward += 25.0
        if self._victim_confirmed and not collision:
            reward += 0.5 * (previous_distance - self._victim_distance())

        rescued = self._victim_confirmed and (
            self._victim_distance() <= controller.config.victim_confirmation_radius_cells
        )
        terminated = bool(rescued)
        truncated = bool(controller.metrics.steps >= self.max_steps and not terminated)
        if rescued:
            reward += 100.0
            controller.metrics.rescued = True
            controller.metrics.termination_reason = "victim_rescued"
            controller._publish_rescue_signal()
        elif truncated:
            reward -= 10.0
            controller.metrics.termination_reason = "step_limit"

        self._episode_reward += reward
        self._publish_training_state(action, collision, first_confirmation)
        controller.blackboard.set(SIMULATION_METRICS, controller.metrics.to_dict())
        return self._observation(), float(reward), terminated, truncated, self._info()

    def _refresh_metrics(self) -> None:
        assert self.controller is not None
        metrics = self.controller.metrics
        metrics.explored_cells = int(np.count_nonzero(self.controller.occupancy.data != 2))
        metrics.coverage_pct = 100.0 * metrics.explored_cells / (GRID_HEIGHT * GRID_WIDTH)
        metrics.policy_source = "ppo_training"

    def _victim_distance(self) -> int:
        assert self.controller is not None
        row, col = self.controller.robot
        victim_row, victim_col = self.controller.scenario.victim
        return abs(row - victim_row) + abs(col - victim_col)

    def _publish_training_state(self, action: int, collision: bool, detected: bool) -> None:
        assert self.controller is not None
        names = ("FORWARD", "LEFT", "BACKWARD", "RIGHT")
        if collision:
            status, reason = "Collision attempt", "Hidden obstacle blocked training move"
        elif detected:
            status, reason = "Victim signal confirmed", "WiFi confidence crossed threshold"
        else:
            status, reason = "RL exploring", f"Direct relative move: {names[action]}"
        self.controller.blackboard.set(DECISION_STATE, {
            "active_behavior": "RLTraining",
            "status": status,
            "reason": reason,
            "source_layer": "RL_TRAINING",
            "tick": self.controller.metrics.steps,
            "timestamp_ms": now_ms(),
        })

    def _observation(self) -> np.ndarray:
        assert self.controller is not None
        return build_observation(
            self.controller,
            victim_confirmed=self._victim_confirmed,
            previous_collision=self._previous_collision,
        )

    def _info(self) -> dict:
        assert self.controller is not None
        info = self.controller.metrics.to_dict()
        info.pop("elapsed_seconds", None)
        info.update({
            "scenario": self.controller.scenario.name,
            "seed": self.controller.seed,
            "detection_step": self._detection_step,
            "episode_reward": float(self._episode_reward),
            "victim_confirmed": self._victim_confirmed,
        })
        return info

    def close(self):
        self.controller = None


def mixed_house_env(seed: int = 7, max_steps: int = 750) -> SARSimulationEnv:
    """Create the deterministic rotating mixed-layout curriculum environment."""
    return SARSimulationEnv(
        scenario=HOUSE_SCENARIOS[0],
        scenario_pool=HOUSE_SCENARIOS,
        base_seed=seed,
        max_steps=max_steps,
    )
