"""Fail-safe validation and operator-control gate for the behavior tree."""

from __future__ import annotations

import math
import numpy as np
import py_trees

from modules.decision_logic.contracts import (
    MAX_STATE_AGE_MS,
    MISSION_CONTROL,
    MISSION_MODES,
    OCCUPANCY_GRID,
    PROXIMITY,
    PROXIMITY_FIELDS,
    ROBOT_POSE,
    TARGET_WAYPOINT,
    is_fresh,
)
from modules.decision_logic.decision_output import STOP_COMMAND, publish_decision
from shared.coordinate_system import GRID_HEIGHT, GRID_WIDTH


class SafetyGate(py_trees.behaviour.Behaviour):
    """Stop unless the mission is active and critical state is valid and fresh."""

    def __init__(self, blackboard, name: str = "SafetyGate"):
        super().__init__(name=name)
        self.bb = blackboard

    def _stop(self, status: str, reason: str) -> py_trees.common.Status:
        publish_decision(
            self.bb,
            behavior=self.name,
            status=status,
            reason=reason,
            source_layer="BT_SAFETY",
            command=STOP_COMMAND,
        )
        self.feedback_message = reason
        return py_trees.common.Status.SUCCESS

    def update(self) -> py_trees.common.Status:
        mission = self.bb.get(MISSION_CONTROL)
        if not isinstance(mission, dict):
            return self._stop("SAFE_STOP", "mission_control_missing_or_invalid")

        mode = mission.get("mode")
        if mode not in MISSION_MODES:
            return self._stop("SAFE_STOP", "mission_mode_invalid")
        emergency_requested = mission.get("emergency_stop", False)
        if not isinstance(emergency_requested, bool):
            return self._stop("SAFE_STOP", "emergency_stop_flag_invalid")
        if emergency_requested:
            return self._stop("EMERGENCY_STOP [operator]", "operator_emergency_stop")
        if mode != "run":
            return self._stop(f"MISSION_{mode.upper()}", f"mission_mode_{mode}")

        pose = self.bb.get(ROBOT_POSE)
        if not isinstance(pose, dict):
            return self._stop("SAFE_STOP", "robot_pose_missing_or_invalid")
        for field in ("x", "y", "heading"):
            value = pose.get(field)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                return self._stop("SAFE_STOP", f"robot_pose_{field}_invalid")
        if not is_fresh(pose, MAX_STATE_AGE_MS):
            return self._stop("SAFE_STOP", "robot_pose_stale")

        grid = self.bb.get(OCCUPANCY_GRID)
        if not isinstance(grid, np.ndarray) or grid.shape != (GRID_HEIGHT, GRID_WIDTH):
            return self._stop("SAFE_STOP", "occupancy_grid_missing_or_invalid")
        if not np.isin(grid, (0, 1, 2)).all():
            return self._stop("SAFE_STOP", "occupancy_grid_values_invalid")

        waypoint = self.bb.get(TARGET_WAYPOINT)
        if waypoint is not None:
            if (
                not isinstance(waypoint, (tuple, list))
                or len(waypoint) != 2
                or any(isinstance(value, bool) or not isinstance(value, int) for value in waypoint)
                or not (0 <= waypoint[0] < GRID_HEIGHT and 0 <= waypoint[1] < GRID_WIDTH)
            ):
                return self._stop("SAFE_STOP", "target_waypoint_invalid")

        proximity = self.bb.get(PROXIMITY)
        if not isinstance(proximity, dict):
            return self._stop("SAFE_STOP", "proximity_missing_or_invalid")
        for field in PROXIMITY_FIELDS:
            value = proximity.get(field)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < 0
            ):
                return self._stop("SAFE_STOP", f"proximity_{field}_invalid")
        if not any(proximity[field] > 0 for field in PROXIMITY_FIELDS):
            return self._stop("SAFE_STOP", "all_proximity_readings_unavailable")
        if not is_fresh(proximity, MAX_STATE_AGE_MS):
            return self._stop("SAFE_STOP", "proximity_stale")

        self.feedback_message = "Mission active; critical state valid"
        return py_trees.common.Status.FAILURE
