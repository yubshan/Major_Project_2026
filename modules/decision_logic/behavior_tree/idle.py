# modules/decision_logic/behavior_tree/idle.py
#
# Idle — Behavior Tree node (Priority 5, fallback / lowest)
#
# The final safety net of the Selector.
# Reached only when:
#   - No emergency (EmergencyStop failed)
#   - No victim confirmed (VictimConfirmation failed)
#   - No active waypoint (NavigateToTarget failed)
#   - Map is fully explored (RLExplore failed)
#
# Writes zero motor command and sets state to IDLE.
# Always returns SUCCESS so the Selector never falls off the bottom.

import py_trees

from modules.decision_logic.decision_output import STOP_COMMAND, publish_decision


class Idle(py_trees.behaviour.Behaviour):
    """
    Fallback idle state. Robot holds position and waits for new mission input.
    """

    def __init__(self, blackboard, name: str = "Idle"):
        super().__init__(name=name)
        self.bb = blackboard

    def update(self) -> py_trees.common.Status:
        publish_decision(
            self.bb,
            behavior=self.name,
            status="IDLE — awaiting mission",
            reason="no_actionable_mission_behavior",
            source_layer="BT_FALLBACK",
            command=STOP_COMMAND,
        )
        self.feedback_message = "Idle, waiting for mission start"
        return py_trees.common.Status.SUCCESS
