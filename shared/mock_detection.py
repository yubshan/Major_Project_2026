# shared/mock_detection.py
#
# Purpose : Provides pre-built WiFi detection scenarios for Teammate B (Decision Logic).
#           Returns dicts that exactly match the real detector's blackboard output format so
#           behavior tree nodes can be developed and tested without PyTorch running.
#
# Owner   : Yubshan (WiFi Detection Lead)  ← reviewed & filled by decision_logic branch
# Used by : modules/decision_logic/ (behavior tree nodes + demo_runner)

import time

# ---------------------------------------------------------------------------
# Blackboard key written by the real detector:  "detection/result"
# ---------------------------------------------------------------------------

def get_mock_detection(scenario: str) -> dict:
    """
    Return a fake detection/result packet for the given scenario.

    Parameters
    ----------
    scenario : str
        One of: "no_human" | "weak_signal" | "strong_detection" | "approaching"

    Returns
    -------
    dict with keys:
        human_x      : float  — estimated X position in cm  (0.0 if no human)
        human_y      : float  — estimated Y position in cm  (0.0 if no human)
        confidence   : float  — 0.0 … 1.0
        timestamp    : int    — milliseconds epoch
    """
    ts = int(time.time() * 1000)

    scenarios = {
        # Robot has just started — no WiFi anomaly detected at all
        "no_human": {
            "human_x": 0.0,
            "human_y": 0.0,
            "confidence": 0.08,
            "timestamp": ts,
        },

        # Signal variation present but not conclusive
        "weak_signal": {
            "human_x": 80.0,
            "human_y": 30.0,
            "confidence": 0.52,
            "timestamp": ts,
        },

        # High-confidence detection — BT should trigger VictimConfirmation
        "strong_detection": {
            "human_x": 120.0,
            "human_y": -40.0,
            "confidence": 0.91,
            "timestamp": ts,
        },

        # Robot is moving toward a known target (mid-confidence)
        "approaching": {
            "human_x": 50.0,
            "human_y": 10.0,
            "confidence": 0.74,
            "timestamp": ts,
        },
    }

    if scenario not in scenarios:
        raise ValueError(
            f"Unknown scenario '{scenario}'. "
            f"Valid options: {list(scenarios.keys())}"
        )

    return scenarios[scenario]


def get_all_scenarios() -> list:
    """Return the list of all available scenario names."""
    return ["no_human", "weak_signal", "strong_detection", "approaching"]