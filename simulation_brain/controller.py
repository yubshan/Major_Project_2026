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
    SIMULATION_MAP_EDIT,
    SIMULATION_METRICS,
    SIMULATION_RESCUE_SIGNAL,
    TARGET_WAYPOINT,
    now_ms,
)
from modules.navigation.occupancy_grid import OccupancyGrid
from shared.blackboard import Blackboard
from shared.coordinate_system import FREE, GRID_HEIGHT, GRID_WIDTH, OCCUPIED, grid_to_world
from simulation_brain.config import SimulationConfig
from simulation_brain.metrics import EpisodeMetrics
from simulation_brain.planning import (
    astar, choose_frontier, nearest_reachable_neighbor, reachable_frontiers,
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


@dataclass(frozen=True)
class MapEditResult:
    accepted: bool
    cell: Cell
    occupied: bool | None
    reason: str


class SimulationController:
    """Own the hidden environment while exposing only sensed state to the brain."""

    def __init__(
        self,
        scenario: str = "random",
        seed: int = 7,
        config: SimulationConfig | None = None,
        model_path: str | None = None,
        moving_obstacle_count: int = 0,
        moving_obstacle_interval: int | None = None,
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
        # Load optional BT resources before publishing time-sensitive sensor state.
        # Otherwise a cold Stable-Baselines import can make the first packet stale
        # and introduce a timing-dependent extra safety-stop tick.
        self.brain.setup()
        self._policy = None
        self.policy_load_error: str | None = None
        if model_path:
            try:
                from stable_baselines3 import PPO
                path = Path(model_path)
                if not path.is_file():
                    raise FileNotFoundError(path)
                self._policy = PPO.load(str(path))
                from simulation_brain.rl.features import OBSERVATION_SCHEMA, OBSERVATION_SIZE
                actual_shape = tuple(self._policy.observation_space.shape)
                if actual_shape != (OBSERVATION_SIZE,):
                    self._policy = None
                    raise ValueError(
                        f"Incompatible PPO observation space {actual_shape}; expected "
                        f"{OBSERVATION_SCHEMA} ({OBSERVATION_SIZE},). Retrain this checkpoint."
                    )
            except Exception as exc:  # Safe deterministic fallback is intentional.
                self.policy_load_error = str(exc)
        self.terminated = False
        self.moving_obstacles_enabled = True
        self.moving_obstacle_interval = max(
            1, moving_obstacle_interval or self.config.moving_obstacle_interval
        )
        self.moving_obstacles: dict[int, Cell] = {}
        self._next_moving_obstacle_id = 1
        self.exploration_sector_override: int | None = None
        self._last_plan_signature = None
        self._publish_mission()
        self.spawn_moving_obstacles(max(0, int(moving_obstacle_count)))

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
        if perceived[goal] != FREE and goal != self.scenario.victim:
            # An exploration frontier can become invalid when a later sensor ray
            # resolves it as occupied. Drop it instead of repeatedly "arriving" at
            # the nearest free neighbor and stalling the mission.
            self.blackboard.update_many({
                TARGET_WAYPOINT: None,
                PLANNED_PATH: [],
                PATH_STATUS: {
                    "goal": goal,
                    "effective_goal": None,
                    "status": "invalidated",
                    "cost": None,
                    "replan_reason": "exploration_target_became_occupied",
                    "timestamp_ms": now_ms(),
                },
            })
            self._last_plan_signature = None
            self.metrics.replans += 1
            return
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
        result = astar(perceived, self.robot, effective_goal)
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

    def _publish_rescue_signal(self) -> dict:
        """Publish the confirmed victim location once when the rover reaches them."""
        existing = self.blackboard.get(SIMULATION_RESCUE_SIGNAL)
        if isinstance(existing, dict) and existing.get("sent") is True:
            return existing
        world_x, world_y = grid_to_world(*self.scenario.victim)
        detection = self.blackboard.get(DETECTION_RESULT, {})
        signal = {
            "sent": True,
            "victim_cell": self.scenario.victim,
            "victim_world": {"x": world_x, "y": world_y},
            "confidence": float(detection.get("confidence", 0.0)),
            "coverage_pct": self.metrics.coverage_pct,
            "timestamp_ms": now_ms(),
        }
        self.metrics.signal_transmitted = True
        self.blackboard.set(SIMULATION_RESCUE_SIGNAL, signal)
        return signal

    def set_dynamic_obstacle(self, cell: Cell, occupied: bool) -> MapEditResult:
        """Apply a safe map edit and immediately invalidate/replan navigation."""
        try:
            row, col = int(cell[0]), int(cell[1])
        except (TypeError, ValueError, IndexError):
            return MapEditResult(False, (-1, -1), None, "invalid_cell")
        cell = (row, col)
        if not (0 <= row < GRID_HEIGHT and 0 <= col < GRID_WIDTH):
            return MapEditResult(False, cell, None, "out_of_bounds")
        if row in (0, GRID_HEIGHT - 1) or col in (0, GRID_WIDTH - 1):
            return MapEditResult(False, cell, None, "boundary_protected")
        if cell == self.robot:
            return MapEditResult(False, cell, None, "robot_cell_protected")
        if cell == self.scenario.victim:
            return MapEditResult(False, cell, None, "victim_cell_protected")

        requested_value = OCCUPIED if occupied else FREE
        if int(self.ground_truth[cell]) == requested_value:
            return MapEditResult(False, cell, occupied, "no_change")

        if not occupied:
            for obstacle_id, obstacle_cell in tuple(self.moving_obstacles.items()):
                if obstacle_cell == cell:
                    del self.moving_obstacles[obstacle_id]
        self.ground_truth[cell] = requested_value
        self.occupancy.set_cell(row, col, requested_value)
        self.metrics.dynamic_obstacle_changes += 1
        self._last_plan_signature = None

        target = self.blackboard.get(TARGET_WAYPOINT)
        if occupied and target is not None and tuple(target) == cell:
            # An exploration target may disappear; victim cells are protected above.
            self.blackboard.update_many({TARGET_WAYPOINT: None, PLANNED_PATH: []})
            target = None

        reason = "dynamic_obstacle_added" if occupied else "dynamic_obstacle_removed"
        edit = {
            "cell": cell,
            "occupied": occupied,
            "reason": reason,
            "timestamp_ms": now_ms(),
        }
        self.blackboard.update_many({
            OCCUPANCY_GRID: self.occupancy.data.copy(),
            SIMULATION_MAP_EDIT: edit,
        })
        if target is not None:
            self._plan(reason)
        else:
            self.blackboard.update_many({
                PLANNED_PATH: [],
                PATH_STATUS: {
                    "goal": None,
                    "effective_goal": None,
                    "status": "awaiting_target",
                    "cost": None,
                    "replan_reason": reason,
                    "timestamp_ms": now_ms(),
                },
            })
        self.blackboard.set(SIMULATION_METRICS, self.metrics.to_dict())
        return MapEditResult(True, cell, occupied, reason)

    def toggle_dynamic_obstacle(self, cell: Cell) -> MapEditResult:
        """Toggle a non-protected cell between free and occupied."""
        try:
            row, col = int(cell[0]), int(cell[1])
        except (TypeError, ValueError, IndexError):
            return MapEditResult(False, (-1, -1), None, "invalid_cell")
        cell = (row, col)
        if not (0 <= row < GRID_HEIGHT and 0 <= col < GRID_WIDTH):
            return MapEditResult(False, cell, None, "out_of_bounds")
        return self.set_dynamic_obstacle(cell, self.ground_truth[cell] != OCCUPIED)

    def _moving_candidate_is_safe(self, old: Cell, new: Cell) -> bool:
        row, col = new
        if row in (0, GRID_HEIGHT - 1) or col in (0, GRID_WIDTH - 1):
            return False
        if new in {self.robot, self.scenario.victim} or self.ground_truth[new] != FREE:
            return False
        self.ground_truth[old] = FREE
        self.ground_truth[new] = OCCUPIED
        route_exists = astar(
            self.ground_truth, self.robot, self.scenario.victim
        ).status == "ok"
        self.ground_truth[new] = FREE
        self.ground_truth[old] = OCCUPIED
        return route_exists

    def spawn_moving_obstacles(self, count: int = 1) -> int:
        """Place deterministic moving hazards without making the victim unreachable."""
        candidates = [
            (row, col)
            for row in range(1, GRID_HEIGHT - 1)
            for col in range(1, GRID_WIDTH - 1)
            if self.ground_truth[row, col] == FREE
            and abs(row - self.robot[0]) + abs(col - self.robot[1]) >= 7
            and abs(row - self.scenario.victim[0]) + abs(col - self.scenario.victim[1]) >= 4
        ]
        placed = 0
        candidate_indices = self.rng.permutation(len(candidates)) if candidates else ()
        for index in candidate_indices:
            if placed >= count:
                break
            cell = candidates[int(index)]
            self.ground_truth[cell] = OCCUPIED
            if astar(self.ground_truth, self.robot, self.scenario.victim).status != "ok":
                self.ground_truth[cell] = FREE
                continue
            obstacle_id = self._next_moving_obstacle_id
            self._next_moving_obstacle_id += 1
            self.moving_obstacles[obstacle_id] = cell
            self.occupancy.set_cell(*cell, OCCUPIED)
            placed += 1
        if placed:
            self.blackboard.set(OCCUPANCY_GRID, self.occupancy.data.copy())
        return placed

    def advance_moving_obstacles(self, force: bool = False) -> int:
        """Move autonomous obstacles and replan before the robot can move."""
        if (
            not self.moving_obstacles_enabled
            or not self.moving_obstacles
            or (not force and (self.metrics.steps + 1) % self.moving_obstacle_interval != 0)
        ):
            return 0
        moved = 0
        last_move = None
        directions = ((-1, 0), (0, -1), (0, 1), (1, 0))
        for obstacle_id in sorted(self.moving_obstacles):
            old = self.moving_obstacles[obstacle_id]
            for direction_index in self.rng.permutation(len(directions)):
                dr, dc = directions[int(direction_index)]
                new = old[0] + dr, old[1] + dc
                if not self._moving_candidate_is_safe(old, new):
                    continue
                self.ground_truth[old] = FREE
                self.ground_truth[new] = OCCUPIED
                self.occupancy.set_cell(*old, FREE)
                self.occupancy.set_cell(*new, OCCUPIED)
                self.moving_obstacles[obstacle_id] = new
                moved += 1
                last_move = {"id": obstacle_id, "from": old, "cell": new}
                break
        if not moved:
            return 0

        self.metrics.moving_obstacle_moves += moved
        self._last_plan_signature = None
        target = self.blackboard.get(TARGET_WAYPOINT)
        if (
            target is not None
            and tuple(target) in self.moving_obstacles.values()
            and tuple(target) != self.scenario.victim
        ):
            self.blackboard.update_many({TARGET_WAYPOINT: None, PLANNED_PATH: []})
            target = None
        event = {
            **last_move,
            "reason": "moving_obstacle_moved",
            "moves": moved,
            "timestamp_ms": now_ms(),
        }
        self.blackboard.update_many({
            OCCUPANCY_GRID: self.occupancy.data.copy(),
            SIMULATION_MAP_EDIT: event,
        })
        if target is not None:
            self._plan("moving_obstacle_moved")
        self.blackboard.set(SIMULATION_METRICS, self.metrics.to_dict())
        return moved

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
        self.advance_moving_obstacles()
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
            self._publish_rescue_signal()
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
