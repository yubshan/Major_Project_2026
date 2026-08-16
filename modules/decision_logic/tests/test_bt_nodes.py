# modules/decision_logic/tests/test_bt_nodes.py
#
# Unit tests for all Behavior Tree nodes.
# Run with: python -m pytest modules/decision_logic/tests/ -v
#
# Tests use only the Blackboard and mock data — no network, no GPU, no Pygame.

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import numpy as np
import pytest

from shared.blackboard      import Blackboard
from shared.coordinate_system import UNKNOWN
from modules.decision_logic.demo_data import get_mock_detection, get_mock_nav_state

import py_trees

from modules.decision_logic.behavior_tree.emergency_stop      import EmergencyStop
from modules.decision_logic.behavior_tree.victim_confirmation  import VictimConfirmation
from modules.decision_logic.behavior_tree.navigate_to_target  import NavigateToTarget
from modules.decision_logic.behavior_tree.rl_explore          import RLExplore
from modules.decision_logic.behavior_tree.idle                import Idle
from modules.decision_logic.behavior_tree.tree_builder        import build_tree


# ─── helpers ────────────────────────────────────────────────────────────────

def fresh_bb() -> Blackboard:
    return Blackboard()


def bb_with_nav(scenario: str, detection: str = "no_human") -> Blackboard:
    bb  = fresh_bb()
    nav = get_mock_nav_state(scenario)
    det = get_mock_detection(detection)
    bb.set("navigation/robot_pose",      nav["robot_pose"])
    bb.set("navigation/occupancy_grid",  nav["occupancy_grid"])
    bb.set("navigation/planned_path",    nav["planned_path"])
    bb.set("navigation/target_waypoint", nav["target_waypoint"])
    bb.set("sensor/proximity",           nav["proximity"])
    bb.set("detection/result",           det)
    return bb


# ─── EmergencyStop ───────────────────────────────────────────────────────────

class TestEmergencyStop:

    def test_safe_returns_failure(self):
        bb   = bb_with_nav("exploring")    # all directions > 15 cm
        node = EmergencyStop(bb)
        assert node.update() == py_trees.common.Status.FAILURE

    def test_danger_returns_success(self):
        bb   = bb_with_nav("obstacle_ahead")  # us_front = 12 cm
        node = EmergencyStop(bb)
        assert node.update() == py_trees.common.Status.SUCCESS

    def test_stop_command_written(self):
        bb   = bb_with_nav("obstacle_ahead")
        node = EmergencyStop(bb)
        node.update()
        cmd  = bb.get("state/motor_command")
        assert cmd is not None
        assert cmd["left_speed"]  == 0
        assert cmd["right_speed"] == 0

    def test_no_proximity_is_safe(self):
        bb   = fresh_bb()   # nothing in blackboard
        node = EmergencyStop(bb)
        assert node.update() == py_trees.common.Status.FAILURE

    def test_bt_status_contains_direction(self):
        bb   = bb_with_nav("obstacle_ahead")
        node = EmergencyStop(bb)
        node.update()
        status = bb.get("state/bt_status", "")
        assert "EMERGENCY_STOP" in status


# ─── VictimConfirmation ──────────────────────────────────────────────────────

class TestVictimConfirmation:

    def test_no_detection_returns_failure(self):
        bb   = fresh_bb()
        node = VictimConfirmation(bb)
        assert node.update() == py_trees.common.Status.FAILURE

    def test_low_confidence_returns_failure(self):
        bb  = fresh_bb()
        bb.set("detection/result", get_mock_detection("weak_signal"))   # conf=0.52
        node = VictimConfirmation(bb)
        assert node.update() == py_trees.common.Status.FAILURE

    def test_high_confidence_returns_success(self):
        bb  = fresh_bb()
        bb.set("detection/result", get_mock_detection("strong_detection"))  # conf=0.91
        node = VictimConfirmation(bb)
        assert node.update() == py_trees.common.Status.SUCCESS

    def test_waypoint_is_written_on_confirm(self):
        bb  = fresh_bb()
        bb.set("detection/result", get_mock_detection("strong_detection"))
        node = VictimConfirmation(bb)
        node.update()
        wp = bb.get("navigation/target_waypoint")
        assert wp is not None
        row, col = wp
        assert isinstance(row, int)
        assert isinstance(col, int)

    def test_threshold_boundary(self):
        bb  = fresh_bb()
        # Exactly at threshold — should succeed
        bb.set("detection/result", {"human_x": 10.0, "human_y": 10.0,
                                    "confidence": 0.85, "timestamp": 0})
        node = VictimConfirmation(bb)
        assert node.update() == py_trees.common.Status.SUCCESS

        # Just below threshold — should fail
        bb.set("detection/result", {"human_x": 10.0, "human_y": 10.0,
                                    "confidence": 0.84, "timestamp": 0})
        assert node.update() == py_trees.common.Status.FAILURE


# ─── NavigateToTarget ────────────────────────────────────────────────────────

class TestNavigateToTarget:

    def test_no_waypoint_returns_failure(self):
        bb   = bb_with_nav("exploring")    # target_waypoint = None
        node = NavigateToTarget(bb)
        assert node.update() == py_trees.common.Status.FAILURE

    def test_waypoint_present_returns_running(self):
        bb   = bb_with_nav("target_locked")   # has a waypoint far away
        node = NavigateToTarget(bb)
        result = node.update()
        # Should be RUNNING (far from target) or FAILURE (arrived — unlikely with mock)
        assert result in (py_trees.common.Status.RUNNING, py_trees.common.Status.FAILURE)

    def test_motor_command_written_when_navigating(self):
        bb   = bb_with_nav("target_locked")
        node = NavigateToTarget(bb)
        node.update()
        cmd = bb.get("state/motor_command")
        assert cmd is not None


# ─── RLExplore ───────────────────────────────────────────────────────────────

class TestRLExplore:

    def test_unknown_grid_returns_running(self):
        bb  = fresh_bb()
        bb.set("navigation/occupancy_grid",
               np.full((50, 50), UNKNOWN, dtype=np.int8))
        bb.set("navigation/robot_pose", {"x": 0.0, "y": 0.0, "heading": 0.0})
        node = RLExplore(bb)
        assert node.update() == py_trees.common.Status.RUNNING

    def test_motor_command_is_valid(self):
        bb  = fresh_bb()
        bb.set("navigation/occupancy_grid",
               np.full((50, 50), UNKNOWN, dtype=np.int8))
        bb.set("navigation/robot_pose", {"x": 0.0, "y": 0.0, "heading": 0.0})
        node = RLExplore(bb)
        node.update()
        cmd = bb.get("state/motor_command")
        assert "left_speed"  in cmd
        assert "right_speed" in cmd
        assert "duration_ms" in cmd

    def test_no_data_still_works(self):
        bb   = fresh_bb()    # empty blackboard
        node = RLExplore(bb)
        # Should not raise, should return RUNNING (heuristic on blank grid)
        result = node.update()
        assert result in (py_trees.common.Status.RUNNING, py_trees.common.Status.FAILURE)


# ─── Idle ────────────────────────────────────────────────────────────────────

class TestIdle:

    def test_always_succeeds(self):
        bb   = fresh_bb()
        node = Idle(bb)
        assert node.update() == py_trees.common.Status.SUCCESS

    def test_zero_motor_command(self):
        bb   = fresh_bb()
        node = Idle(bb)
        node.update()
        cmd = bb.get("state/motor_command")
        assert cmd["left_speed"]  == 0
        assert cmd["right_speed"] == 0

    def test_bt_status_set(self):
        bb   = fresh_bb()
        node = Idle(bb)
        node.update()
        assert "IDLE" in bb.get("state/bt_status", "")


# ─── Full Tree Integration ────────────────────────────────────────────────────

class TestFullTree:

    def test_tree_ticks_without_error(self):
        bb   = bb_with_nav("exploring", "no_human")
        tree = build_tree(bb)
        tree.setup(timeout=5)
        tree.tick()
        assert bb.get("state/bt_status") is not None

    def test_emergency_stop_takes_priority(self):
        bb   = bb_with_nav("obstacle_ahead", "strong_detection")
        tree = build_tree(bb)
        tree.setup(timeout=5)
        tree.tick()
        status = bb.get("state/bt_status", "")
        # Even though victim is detected (would normally trigger VictimConfirmation),
        # EmergencyStop has higher priority and should fire first
        assert "EMERGENCY_STOP" in status

    def test_victim_confirmed_when_safe(self):
        bb   = bb_with_nav("exploring", "strong_detection")  # safe proximity
        tree = build_tree(bb)
        tree.setup(timeout=5)
        tree.tick()
        status = bb.get("state/bt_status", "")
        assert "VICTIM_CONFIRMED" in status

    def test_confirmed_victim_yields_to_navigation_on_next_tick(self):
        bb = bb_with_nav("exploring", "strong_detection")
        tree = build_tree(bb)
        tree.setup(timeout=5)
        tree.tick()
        tree.tick()
        assert "NAVIGATING_TO_TARGET" in bb.get("state/bt_status", "")

    def test_rl_explore_when_no_victim(self):
        bb   = bb_with_nav("exploring", "no_human")
        tree = build_tree(bb)
        tree.setup(timeout=5)
        tree.tick()
        status = bb.get("state/bt_status", "")
        assert "RL_EXPLORE" in status

    def test_multiple_ticks_stable(self):
        bb   = bb_with_nav("exploring", "no_human")
        tree = build_tree(bb)
        tree.setup(timeout=5)
        for _ in range(20):
            tree.tick()
        # After 20 ticks, system should still be stable
        assert bb.get("state/bt_status") is not None
        assert bb.get("state/motor_command") is not None


# ─── SARExploreEnv sanity ────────────────────────────────────────────────────

class TestSAREnv:

    def test_env_reset(self):
        from modules.decision_logic.rl_env.sar_explore_env import SARExploreEnv
        env = SARExploreEnv()
        obs, info = env.reset()
        assert obs.shape == (50 * 50 + 3,)

    def test_env_step_all_actions(self):
        from modules.decision_logic.rl_env.sar_explore_env import SARExploreEnv
        env = SARExploreEnv()
        env.reset()
        for action in range(4):
            env.reset()
            obs, rew, term, trunc, info = env.step(action)
            assert "explore_pct" in info
            assert "action_name" in info

    def test_action_to_motor(self):
        from modules.decision_logic.rl_env.sar_explore_env import SARExploreEnv
        for action in range(4):
            cmd = SARExploreEnv.action_to_motor_command(action)
            assert "left_speed"  in cmd
            assert "right_speed" in cmd
            assert "duration_ms" in cmd
