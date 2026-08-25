# modules/decision_logic/behavior_tree/emergency_stop.py
#
# EmergencyStop — Behavior Tree node (Priority 1, highest)
#
# Reads proximity and the next planned grid movement from the blackboard.
# If an obstacle in the selected movement direction is dangerously close, the node:
#   - Writes a STOP motor command to the blackboard
#   - Writes "EMERGENCY_STOP" to state/bt_status
#   - Returns SUCCESS (which causes the Selector to stop — no other node runs)
#
# If all directions are safe, returns FAILURE so the Selector tries the next node.
#
# py_trees return statuses:
#   SUCCESS  → this node handled the situation, Selector stops here
#   FAILURE  → not triggered, Selector moves to next child
#   RUNNING  → long-running action in progress (not used here)

import py_trees

from modules.decision_logic.contracts import (
    PLANNED_PATH, PROXIMITY, PROXIMITY_FIELDS, ROBOT_POSE, TARGET_WAYPOINT,
)
from modules.decision_logic.decision_output import STOP_COMMAND, publish_decision

DANGER_CM = 15   # Emergency threshold in centimetres

class EmergencyStop(py_trees.behaviour.Behaviour):
    """
    Halt the robot if the ultrasonic sensor along its selected move is unsafe.
    This is the highest-priority node in the Selector — safety first.
    """

    def __init__(self, blackboard, name: str = "EmergencyStop"):
        super().__init__(name=name)
        self.bb = blackboard

    def update(self) -> py_trees.common.Status:
        proximity = self.bb.get(PROXIMITY)

        if proximity is None:
            # No sensor data yet — assume safe, let other nodes decide
            return py_trees.common.Status.FAILURE

        # If a planner has deliberately selected a non-forward next cell, a close
        # obstacle in front must not deadlock the robot before it can turn away.
        path = self.bb.get(PLANNED_PATH, [])
        pose = self.bb.get(ROBOT_POSE, {})
        # Grid motion advances only in the selected direction; side sensors inform
        # mapping but do not make a safe turn impossible.
        relevant_directions = {"us_front"}
        target = self.bb.get(TARGET_WAYPOINT)
        if isinstance(proximity.get("hits"), dict) and not path and target is None:
            # The simulation has no pending movement yet; allow exploration to choose
            # a safe frontier instead of repeatedly stopping while facing a wall.
            relevant_directions = set()
        if isinstance(target, (tuple, list)) and isinstance(pose, dict):
            from shared.coordinate_system import world_to_grid
            current = world_to_grid(pose.get("x", 0.0), pose.get("y", 0.0))
            if tuple(target) == current:
                relevant_directions = set()
        if isinstance(path, list) and path and isinstance(pose, dict):
            from shared.coordinate_system import world_to_grid
            row, col = world_to_grid(pose.get("x", 0.0), pose.get("y", 0.0))
            heading = int(round(pose.get("heading", 0.0) / 90.0) * 90) % 360
            absolute_deltas = {0: (0, 1), 90: (-1, 0), 180: (0, -1), 270: (1, 0)}
            desired = (path[0][0] - row, path[0][1] - col)
            desired_heading = next(
                (angle for angle, delta in absolute_deltas.items() if delta == desired), None
            )
            relative = None if desired_heading is None else (desired_heading - heading) % 360
            relevant_directions = {
                0: {"us_front"},
                90: {"us_left90"},
                270: {"us_right90"},
                # The rear is not instrumented; A*'s known-free path remains authoritative.
                180: set(),
            }.get(relative, set(PROXIMITY_FIELDS))

        # Check all 5 ultrasonic directions.
        for direction in PROXIMITY_FIELDS:
            if direction not in relevant_directions:
                continue
            distance_cm = proximity[direction]
            if distance_cm > 0 and distance_cm < DANGER_CM:
                status = f"EMERGENCY_STOP [{direction}: {distance_cm}cm]"
                publish_decision(
                    self.bb,
                    behavior=self.name,
                    status=status,
                    reason=f"{direction}={distance_cm}cm_below_{DANGER_CM}cm",
                    source_layer="BT_SAFETY",
                    command=STOP_COMMAND,
                )
                self.feedback_message = f"BLOCKED: {direction} = {distance_cm}cm"
                return py_trees.common.Status.SUCCESS

        # All directions safe
        self.feedback_message = "All clear"
        return py_trees.common.Status.FAILURE
