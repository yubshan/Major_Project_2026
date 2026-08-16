# modules/decision_logic/behavior_tree/emergency_stop.py
#
# EmergencyStop — Behavior Tree node (Priority 1, highest)
#
# Reads the proximity sensor readings from the blackboard.
# If any direction is dangerously close (< DANGER_CM), the node:
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

from modules.decision_logic.contracts import PROXIMITY, PROXIMITY_FIELDS
from modules.decision_logic.decision_output import STOP_COMMAND, publish_decision

DANGER_CM = 15   # Emergency threshold in centimetres

class EmergencyStop(py_trees.behaviour.Behaviour):
    """
    Immediately halts the robot if any ultrasonic sensor reads < DANGER_CM.
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

        # Check all 5 ultrasonic directions
        for direction in PROXIMITY_FIELDS:
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
