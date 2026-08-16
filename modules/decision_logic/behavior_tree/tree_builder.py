# modules/decision_logic/behavior_tree/tree_builder.py
#
# tree_builder.py — assembles the full Drishya behavior tree
#
# Tree structure (Selector = "try each child until one succeeds"):
#
#   Selector [root]
#   ├── EmergencyStop          ← Priority 1: Safety
#   ├── VictimConfirmation     ← Priority 2: Mission (confirm & approach victim)
#   ├── NavigateToTarget       ← Priority 3: Execute active waypoint
#   ├── RLExplore              ← Priority 4: PPO exploration
#   └── Idle                   ← Priority 5: Fallback
#
# A py_trees Selector ticks each child left-to-right:
#   - If a child returns SUCCESS or RUNNING → Selector stops here (this tick)
#   - If a child returns FAILURE → Selector moves to the next child
#
# This means safety checks always run first and can immediately override
# any exploration or navigation behaviour.

import py_trees

from modules.decision_logic.behavior_tree.emergency_stop      import EmergencyStop
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
        EmergencyStop(blackboard),
        VictimConfirmation(blackboard),
        NavigateToTarget(blackboard),
        RLExplore(blackboard, model_path=model_path),
        Idle(blackboard),
    ])

    tree = py_trees.trees.BehaviourTree(root)
    return tree
