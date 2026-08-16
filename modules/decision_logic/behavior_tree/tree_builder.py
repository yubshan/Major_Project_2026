# modules/decision_logic/behavior_tree/tree_builder.py
#
# tree_builder.py — assembles the full Drishya behavior tree
#
# Tree structure (Selector = "try each child until one succeeds"):
#
#   Selector [root]
#   ├── SafetyGate             ← Priority 1: Mission/data validity
#   ├── EmergencyStop          ← Priority 2: Proximity safety
#   ├── VictimConfirmation     ← Priority 3: Confirm victim
#   ├── NavigateToTarget       ← Priority 4: Execute active waypoint
#   ├── RLExplore              ← Priority 5: Exploration
#   └── Idle                   ← Priority 6: Fallback
#
# A py_trees Selector ticks each child left-to-right:
#   - If a child returns SUCCESS or RUNNING → Selector stops here (this tick)
#   - If a child returns FAILURE → Selector moves to the next child
#
# This means safety checks always run first and can immediately override
# any exploration or navigation behaviour.

import py_trees

from modules.decision_logic.behavior_tree.emergency_stop      import EmergencyStop
from modules.decision_logic.behavior_tree.safety_gate         import SafetyGate
from modules.decision_logic.behavior_tree.victim_confirmation  import VictimConfirmation
from modules.decision_logic.behavior_tree.navigate_to_target  import NavigateToTarget
from modules.decision_logic.behavior_tree.rl_explore          import RLExplore
from modules.decision_logic.behavior_tree.idle                import Idle


def build_tree(blackboard, model_path: str = None) -> py_trees.trees.BehaviourTree:
    """
    Build and return the full Drishya behavior tree wired to the given blackboard.

    Parameters
    ----------
    blackboard : shared.blackboard.Blackboard
        The shared system state object.

    Returns
    -------
    py_trees.trees.BehaviourTree
        Ready to call .setup() and .tick() on.
    """
    root = py_trees.composites.Selector(name="DrishyaBrain", memory=False)

    root.add_children([
        SafetyGate(blackboard),
        EmergencyStop(blackboard),
        VictimConfirmation(blackboard),
        NavigateToTarget(blackboard),
        RLExplore(blackboard, model_path=model_path),
        Idle(blackboard),
    ])

    tree = py_trees.trees.BehaviourTree(root)
    return tree
