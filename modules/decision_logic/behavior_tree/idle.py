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

IDLE_COMMAND = {
    "left_speed":  0,
    "right_speed": 0,
    "duration_ms": 0,
}


class Idle(py_trees.behaviour.Behaviour):
    """
    Fallback idle state. Robot holds position and waits for new mission input.
    """

    def __init__(self, blackboard, name: str = "Idle"):
        super().__init__(name=name)
        self.bb = blackboard

    def update(self) -> py_trees.common.Status:
        self.bb.set("state/motor_command", IDLE_COMMAND)
        self.bb.set("state/bt_status", "IDLE — awaiting mission")
        self.feedback_message = "Idle, waiting for mission start"
        return py_trees.common.Status.SUCCESS
