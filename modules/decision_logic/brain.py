# modules/decision_logic/brain.py
#
# Brain — the core runtime loop for Project Drishya's decision system.
#
# Ticks the Behavior Tree at 10 Hz in a background thread.
# Reads from and writes to the shared Blackboard.
#
# Usage (from main.py or demo_runner.py):
#
#   from shared.blackboard import Blackboard
#   from modules.decision_logic.brain import Brain
#
#   bb    = Blackboard()
#   brain = Brain(bb)
#   brain.start()         # non-blocking, runs in background thread
#   ...
#   brain.stop()          # graceful shutdown
#
# Or run directly: python -m modules.decision_logic.brain

import logging
import threading
import time

import py_trees

from modules.decision_logic.behavior_tree.tree_builder import build_tree

logger = logging.getLogger(__name__)

TICK_RATE_HZ = 10
TICK_INTERVAL = 1.0 / TICK_RATE_HZ


class Brain:
    """
    The robot's high-level decision system.

    Runs the Behavior Tree at 10 Hz in a dedicated thread.
    Reads environment state from the Blackboard, ticks the tree,
    and writes motor commands + BT status back to the Blackboard.
    """

    def __init__(self, blackboard, model_path: str = None):
        """
        Parameters
        ----------
        blackboard : shared.blackboard.Blackboard
            The shared system state object.
        model_path : str, optional
            Path to a trained PPO model checkpoint (.zip).
            If None, the RLExplore node uses heuristic fallback.
        """
        self.bb          = blackboard
        self._tree       = build_tree(blackboard, model_path=model_path)
        self._thread     = None
        self._running    = False
        self._tick_count = 0

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def start(self):
        """Start the brain in a background thread (non-blocking)."""
        if self._running:
            logger.warning("Brain is already running")
            return
        self._tree.setup(timeout=5)
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="DrishyaBrain")
        self._thread.start()
        logger.info("Brain started @ %d Hz", TICK_RATE_HZ)

    def stop(self):
        """Gracefully stop the brain loop."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("Brain stopped after %d ticks", self._tick_count)

    def tick_once(self):
        """
        Manually tick the tree once (useful for testing without threads).
        Returns the tip (active leaf node).
        """
        self._tree.tick()
        self._tick_count += 1
        return self._tree.tip()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _loop(self):
        """The main 10 Hz loop."""
        while self._running:
            t_start = time.perf_counter()

            try:
                self._tree.tick()
                self._tick_count += 1

                tip = self._tree.tip()
                if tip:
                    logger.debug(
                        "Tick %d | Active: %s | %s",
                        self._tick_count,
                        tip.name,
                        tip.feedback_message,
                    )

            except Exception as exc:
                logger.error("Brain tick error: %s", exc, exc_info=True)

            elapsed = time.perf_counter() - t_start
            sleep_for = max(0.0, TICK_INTERVAL - elapsed)
            time.sleep(sleep_for)


# ---------------------------------------------------------------------------
# Allow running standalone for quick smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(
        level  = logging.DEBUG,
        format = "%(asctime)s  %(name)-20s  %(levelname)-8s  %(message)s",
    )

    from shared.blackboard       import Blackboard
    from modules.decision_logic.demo_data import (
        get_mock_detection,
        get_mock_nav_state,
    )

    bb = Blackboard()

    # Pre-load some mock state so the BT has something to work with
    nav  = get_mock_nav_state("exploring")
    det  = get_mock_detection("weak_signal")
    bb.set("navigation/robot_pose",    nav["robot_pose"])
    bb.set("navigation/occupancy_grid", nav["occupancy_grid"])
    bb.set("navigation/target_waypoint", nav["target_waypoint"])
    bb.set("sensor/proximity",          nav["proximity"])
    bb.set("detection/result",          det)

    brain = Brain(bb)
    brain.start()

    try:
        for _ in range(30):
            time.sleep(0.1)
            bt_status = bb.get("state/bt_status", "–")
            motor_cmd  = bb.get("state/motor_command", {})
            print(f"  BT: {bt_status:<50}  Motors: {motor_cmd}")
    except KeyboardInterrupt:
        pass

    brain.stop()
    print(f"\nCompleted {brain._tick_count} ticks.")
