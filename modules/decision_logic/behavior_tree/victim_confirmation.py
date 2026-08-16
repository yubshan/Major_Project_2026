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

import math

import py_trees
from shared.coordinate_system import world_to_grid
from shared.coordinate_system import GRID_HEIGHT, GRID_WIDTH

from modules.decision_logic.contracts import (
    DETECTION_RESULT,
    MAX_DETECTION_AGE_MS,
    TARGET_WAYPOINT,
    is_fresh,
    payload_timestamp_ms,
)
from modules.decision_logic.decision_output import publish_decision

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
        detection = self.bb.get(DETECTION_RESULT)

        if detection is None:
            self.feedback_message = "No detection data"
            return py_trees.common.Status.FAILURE

        confidence = detection.get("confidence", 0.0)
        if (
            isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
            or not math.isfinite(confidence)
        ):
            self.feedback_message = "Invalid confidence"
            return py_trees.common.Status.FAILURE
        if not 0.0 <= confidence <= 1.0:
            self.feedback_message = "Confidence outside [0, 1]"
            return py_trees.common.Status.FAILURE
        if not is_fresh(detection, MAX_DETECTION_AGE_MS):
            self.feedback_message = "Detection is stale or missing timestamp"
            return py_trees.common.Status.FAILURE

        if confidence < CONFIRM_THRESHOLD:
            self.feedback_message = f"Confidence {confidence:.2f} below threshold"
            return py_trees.common.Status.FAILURE

        detection_id = (
            payload_timestamp_ms(detection),
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
        if any(isinstance(value, bool) or not isinstance(value, (int, float))
               or not math.isfinite(value)
               for value in (human_x, human_y)):
            self.feedback_message = "Invalid victim coordinates"
            return py_trees.common.Status.FAILURE
        waypoint = world_to_grid(human_x, human_y)   # → (row, col)
        if not (0 <= waypoint[0] < GRID_HEIGHT and 0 <= waypoint[1] < GRID_WIDTH):
            self.feedback_message = "Victim waypoint outside map"
            return py_trees.common.Status.FAILURE
        self._last_detection = detection_id

        # Write waypoint for navigation module and dashboard
        self.bb.set(TARGET_WAYPOINT, waypoint)
        status = f"VICTIM_CONFIRMED [conf={confidence:.2f} → wp={waypoint}]"
        publish_decision(
            self.bb,
            behavior=self.name,
            status=status,
            reason=f"fresh_detection_confidence={confidence:.2f}",
            source_layer="BT_MISSION",
            command={"left_speed": 0, "right_speed": 0, "duration_ms": 100},
        )

        self.feedback_message = f"Confirmed victim @ {waypoint} (conf={confidence:.2f})"
        return py_trees.common.Status.SUCCESS
