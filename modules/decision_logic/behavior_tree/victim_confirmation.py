# modules/decision_logic/behavior_tree/victim_confirmation.py
#
# VictimConfirmation — Behavior Tree node (Priority 2)
#
# Reads the WiFi detection result from the blackboard.
# If confidence ≥ CONFIRM_THRESHOLD, the node:
#   - Converts the detected human position (cm) → grid waypoint
#   - Writes the waypoint to "navigation/target_waypoint"
#   - Writes "VICTIM_CONFIRMED" to state/bt_status
#   - Returns SUCCESS
#
# If confidence is below threshold, returns FAILURE so the Selector
# continues to NavigateToTarget or RLExplore.

import py_trees
from shared.coordinate_system import world_to_grid

CONFIRM_THRESHOLD = 0.85   # WiFi confidence required to confirm a victim


class VictimConfirmation(py_trees.behaviour.Behaviour):
    """
    Activates when WiFi detection confidence is high enough to confirm a victim.
    Sets a navigation waypoint so the robot moves toward the detected human.
    """

    def __init__(self, blackboard, name: str = "VictimConfirmation"):
        super().__init__(name=name)
        self.bb = blackboard
        self._last_detection = None

    def update(self) -> py_trees.common.Status:
        detection = self.bb.get("detection/result")

        if detection is None:
            self.feedback_message = "No detection data"
            return py_trees.common.Status.FAILURE

        confidence = detection.get("confidence", 0.0)

        if confidence < CONFIRM_THRESHOLD:
            self.feedback_message = f"Confidence {confidence:.2f} below threshold"
            return py_trees.common.Status.FAILURE

        detection_id = (
            detection.get("timestamp"),
            detection.get("human_x"),
            detection.get("human_y"),
            confidence,
        )
        if detection_id == self._last_detection:
            self.feedback_message = "Detection already confirmed"
            return py_trees.common.Status.FAILURE

        # High-confidence detection — compute waypoint
        human_x = detection.get("human_x", 0.0)
        human_y = detection.get("human_y", 0.0)
        waypoint = world_to_grid(human_x, human_y)   # → (row, col)
        self._last_detection = detection_id

        # Write waypoint for navigation module and dashboard
        self.bb.set("navigation/target_waypoint", waypoint)
        self.bb.set("state/bt_status",
                    f"VICTIM_CONFIRMED [conf={confidence:.2f} → wp={waypoint}]")
        self.bb.set("state/motor_command",
                    {"left_speed": 0, "right_speed": 0, "duration_ms": 100})  # brief stop

        self.feedback_message = f"Confirmed victim @ {waypoint} (conf={confidence:.2f})"
        return py_trees.common.Status.SUCCESS
