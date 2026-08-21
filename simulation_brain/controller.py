"""End-to-end orchestration of sensing, decisions, planning, and motion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from modules.decision_logic.brain import Brain
from modules.decision_logic.decision_output import publish_decision
from modules.decision_logic.contracts import (
    DECISION_STATE,
    DETECTION_RESULT,
    MISSION_CONTROL,
    OCCUPANCY_GRID,
    PATH_STATUS,
    PLANNED_PATH,
    PROXIMITY,
    ROBOT_POSE,
    SIMULATION_METRICS,
    TARGET_WAYPOINT,
    now_ms,
)
from modules.navigation.occupancy_grid import OccupancyGrid
from shared.blackboard import Blackboard
from shared.coordinate_system import FREE, GRID_HEIGHT, GRID_WIDTH, grid_to_world
from simulation_brain.config import SimulationConfig
from simulation_brain.metrics import EpisodeMetrics
from simulation_brain.planning import (
    choose_frontier, dijkstra, nearest_reachable_neighbor, reachable_frontiers,
)
from simulation_brain.scenarios import Scenario, create_scenario
from simulation_brain.sensors import apply_observation, sense

Cell = tuple[int, int]
HEADINGS = {(0, 1): 0, (-1, 0): 90, (0, -1): 180, (1, 0): 270}


@dataclass(frozen=True)
class StepResult:
    terminated: bool
    reason: str
    newly_explored: int
    detected: bool


class SimulationController:
    """Own the hidden environment while exposing only sensed state to the brain."""

    def __init__(
        self,
        scenario: str = "random",
        seed: int = 7,
        config: SimulationConfig | None = None,
        model_path: str | None = None,
    ):
        self.config = config or SimulationConfig()
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.scenario: Scenario = create_scenario(scenario, seed)
        self.blackboard = Blackboard()
        self.occupancy = OccupancyGrid()
        self.robot: Cell = self.scenario.start
        self.heading = 0
        self.metrics = EpisodeMetrics()
        self.metrics.start()
        # The integrated PPO policy uses the richer Simulation Brain observation;
        # the existing decision-module checkpoint format remains backward-compatible.
        self.brain = Brain(self.blackboard)
        self._policy = None
        self.policy_load_error: str | None = None
        if model_path:
            try:
                from stable_baselines3 import PPO
                path = Path(model_path)
                if not path.is_file():
                    raise FileNotFoundError(path)
                self._policy = PPO.load(str(path))
            except Exception as exc:  # Safe deterministic fallback is intentional.
                self.policy_load_error = str(exc)
        self.terminated = False
        self.exploration_sector_override: int | None = None
        self._last_plan_signature = None
        self._publish_mission()

    @property
    def ground_truth(self) -> np.ndarray:
        """Ground truth is for rendering/evaluation only; it is never put on the Blackboard."""
        return self.scenario.ground_truth

    def _publish_mission(self) -> None:
        self.blackboard.set(MISSION_CONTROL, {
            "mode": "run", "emergency_stop": False, "timestamp_ms": now_ms()
        })

    def _pose(self, timestamp: int) -> dict:
        x, y = grid_to_world(*self.robot)
        return {"x": x, "y": y, "heading": self.heading, "timestamp_ms": timestamp}

    def _detect_victim(self, timestamp: int) -> tuple[dict, bool]:
        active_target = self.blackboard.get(TARGET_WAYPOINT)
        previous = self.blackboard.get(DETECTION_RESULT)
        if (
            active_target is not None
            and tuple(active_target) == self.scenario.victim
            and isinstance(previous, dict)
            and previous.get("confidence", 0.0) >= self.config.victim_confirm_threshold
        ):
            return previous, previous.get("confidence", 0.0) >= self.config.victim_confirm_threshold
        distance = abs(self.robot[0] - self.scenario.victim[0]) + abs(
            self.robot[1] - self.scenario.victim[1]
        )
        max_range = self.config.victim_detection_range_cells
        if distance > max_range:
            confidence = max(0.02, 0.18 - 0.01 * (distance - max_range))
        else:
            base = 1.0 - 0.018 * distance
            confidence = float(np.clip(base + self.rng.normal(0.0, 0.015), 0.0, 0.99))
        x, y = grid_to_world(*self.scenario.victim)
        packet = {
            "human_x": x,
            "human_y": y,
            "confidence": confidence,
            "timestamp_ms": timestamp,
        }
        return packet, confidence >= self.config.victim_confirm_threshold

    def _publish_observation(self) -> tuple[int, bool]:
        timestamp = now_ms()
        packet = sense(
            self.ground_truth,
            self.robot,
            self.heading,
            self.config.sensor_range_cells,
            timestamp,
        )
        newly_explored = apply_observation(self.occupancy, packet, self.robot)
        detection, detected = self._detect_victim(timestamp)
        values = {
            ROBOT_POSE: self._pose(timestamp),
            OCCUPANCY_GRID: self.occupancy.data.copy(),
            PROXIMITY: packet,
            DETECTION_RESULT: detection,
        }
        self.blackboard.update_many(values)
        return newly_explored, detected

    def _plan(self, reason: str = "goal_or_map_changed") -> None:
        goal = self.blackboard.get(TARGET_WAYPOINT)
        if goal is None:
            return
        goal = tuple(goal)
        perceived = self.occupancy.data
        effective_goal = goal
        if perceived[goal] != FREE:
            alternative = nearest_reachable_neighbor(perceived, self.robot, goal)
            if alternative is not None:
                effective_goal = alternative
            else:
                # Approach an unobserved victim through the reachable frontier that
                # minimizes remaining Manhattan distance; keep the victim as mission goal.
                frontiers = reachable_frontiers(perceived, self.robot)
                if frontiers:
                    effective_goal = min(
                        frontiers,
                        key=lambda item: (
                            abs(item[0][0] - goal[0]) + abs(item[0][1] - goal[1]),
                            item[1],
                            -item[2],
                            item[0],
                        ),
                    )[0]
        signature = (self.robot, goal, perceived.tobytes())
        existing = self.blackboard.get(PLANNED_PATH, [])
        next_invalid = bool(existing) and perceived[tuple(existing[0])] != FREE
        if signature == self._last_plan_signature and existing and not next_invalid:
            return
        result = dijkstra(perceived, self.robot, effective_goal)
        self.blackboard.update_many({
            PLANNED_PATH: result.path,
            PATH_STATUS: {
                "goal": goal,
                "effective_goal": effective_goal,
                "status": result.status,
                "cost": result.cost,
                "replan_reason": "path_blocked" if next_invalid else reason,
                "timestamp_ms": now_ms(),
            },
        })
        self._last_plan_signature = signature
        self.metrics.replans += 1

    def _exploration_target_from_trace(self) -> None:
        state = self.blackboard.get(DECISION_STATE, {})
        if state.get("active_behavior") != "RLExplore":
            return
        if self.blackboard.get(TARGET_WAYPOINT) is not None:
            return
        status = state.get("status", "")
        names = ("FORWARD", "LEFT", "BACKWARD", "RIGHT")
        action = next((index for index, name in enumerate(names) if name in status), None)
        if self.exploration_sector_override is not None:
            action = self.exploration_sector_override
            self.metrics.policy_source = "external_policy"
        elif self._policy is not None:
            from simulation_brain.rl.features import build_observation
            predicted, _ = self._policy.predict(build_observation(self), deterministic=True)
            action = int(predicted)
            self.metrics.policy_source = "ppo"
        # Convert relative action to the absolute sectors expected by choose_frontier:
        # east, north, west, south.
        turn = (0, 90, 180, -90)[action] if action is not None else 0
        desired_heading = (self.heading + turn) % 360
        sector = {0: 0, 90: 1, 180: 2, 270: 3}[desired_heading]
        goal = choose_frontier(self.occupancy.data, self.robot, sector=sector)
        if goal is not None:
            self.blackboard.set(TARGET_WAYPOINT, goal)
            self._plan("exploration_frontier_selected")
            if self.exploration_sector_override is None:
                if self._policy is None:
                    self.metrics.policy_source = "heuristic"
                else:
                    action_name = names[action]
                    publish_decision(
                        self.blackboard,
                        behavior="RLExplore",
                        status=f"RL_EXPLORE [PPO] → {action_name}",
                        reason=f"source=PPO;frontier={goal};action={action_name}",
                        source_layer="RL_POLICY",
                        command=self.blackboard.get("state/motor_command", {}),
                    )

    def _execute_planned_step(self) -> None:
        state = self.blackboard.get(DECISION_STATE, {})
        if state.get("active_behavior") != "NavigateToTarget":
            return
        path = self.blackboard.get(PLANNED_PATH, [])
        if not path:
            return
        nxt = tuple(path[0])
        delta = nxt[0] - self.robot[0], nxt[1] - self.robot[1]
        if delta not in HEADINGS or self.ground_truth[nxt] != FREE:
            self.metrics.collisions += 1
            self.blackboard.set(PLANNED_PATH, [])
            self._last_plan_signature = None
            return
        self.heading = HEADINGS[delta]
        self.robot = nxt
        self.blackboard.set(PLANNED_PATH, list(path[1:]))

    def _update_metrics(self, detected: bool) -> None:
        self.metrics.steps += 1
        self.metrics.explored_cells = int(np.count_nonzero(self.occupancy.data != 2))
        self.metrics.coverage_pct = 100.0 * self.metrics.explored_cells / (GRID_HEIGHT * GRID_WIDTH)
        if detected:
            self.metrics.victim_detections += 1
        self.blackboard.set(SIMULATION_METRICS, self.metrics.to_dict())

    def _victim_known_unreachable(self, detected: bool) -> bool:
        if not detected or self.blackboard.get(TARGET_WAYPOINT) is None:
            return False
        goal = tuple(self.blackboard.get(TARGET_WAYPOINT))
        if goal != self.scenario.victim:
            return False
        neighbors = []
        for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
            row, col = goal[0] + dr, goal[1] + dc
            if 0 <= row < GRID_HEIGHT and 0 <= col < GRID_WIDTH:
                neighbors.append(int(self.occupancy.data[row, col]))
        return bool(neighbors) and all(value == 1 for value in neighbors)

    def step(self) -> StepResult:
        if self.terminated:
            return StepResult(True, self.metrics.termination_reason, 0, False)
        self._publish_mission()
        newly_explored, detected = self._publish_observation()
        self._plan()
        self.brain.tick_once()
        self._exploration_target_from_trace()
        self._execute_planned_step()
        self._update_metrics(detected)

        victim_distance = abs(self.robot[0] - self.scenario.victim[0]) + abs(
            self.robot[1] - self.scenario.victim[1]
        )
        if detected and victim_distance <= self.config.victim_confirmation_radius_cells:
            self.terminated = True
            self.metrics.rescued = True
            self.metrics.termination_reason = "victim_rescued"
        elif self._victim_known_unreachable(detected):
            self.terminated = True
            self.metrics.termination_reason = "victim_unreachable"
        elif self.metrics.steps >= self.config.max_steps:
            self.terminated = True
            self.metrics.termination_reason = "step_limit"
        elif not np.any(self.occupancy.data == 2) and not self.metrics.rescued:
            self.terminated = True
            self.metrics.termination_reason = "map_fully_explored"
        self.blackboard.set(SIMULATION_METRICS, self.metrics.to_dict())
        return StepResult(self.terminated, self.metrics.termination_reason, newly_explored, detected)

    def run(self, max_steps: int | None = None) -> dict:
        limit = max_steps or self.config.max_steps
        while not self.terminated and self.metrics.steps < limit:
            self.step()
        if not self.terminated and self.metrics.steps >= limit:
            self.terminated = True
            self.metrics.termination_reason = "step_limit"
        return self.metrics.to_dict()
