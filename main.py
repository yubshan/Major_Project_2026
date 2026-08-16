"""Project Drishya headless integration harness.

This entry point connects the merged navigation mapper and decision brain through
the shared Blackboard. Sensor and WiFi inputs remain deterministic mocks until the
simulation and WiFi modules publish their live adapters.

Run from the repository root:

    python main.py
"""

from __future__ import annotations

from copy import deepcopy

from modules.decision_logic.brain import Brain
from modules.decision_logic.contracts import (
    DETECTION_RESULT,
    MISSION_CONTROL,
    OCCUPANCY_GRID,
    PLANNED_PATH,
    PROXIMITY,
    PROXIMITY_FIELDS,
    ROBOT_POSE,
    TARGET_WAYPOINT,
    now_ms,
)
from modules.decision_logic.demo_data import get_mock_detection
from modules.navigation.mapping import update_map
from modules.navigation.occupancy_grid import OccupancyGrid
from shared.blackboard import Blackboard
from shared.mock_sensors import get_mock_sensor_packet


SCENARIOS = (
    ("idle", "open_front", "no_human"),
    ("explore", "open_front", "no_human"),
    ("emergency", "obstacle_ahead", "no_human"),
    ("victim", "open_front", "strong_detection"),
)


class IntegrationHarness:
    """Minimal coordinator for repeatable cross-module defense scenarios."""

    def __init__(self):
        self.blackboard = Blackboard()
        self.grid = OccupancyGrid()
        self.brain = Brain(self.blackboard)
        self.pose = {"x": 0.0, "y": 0.0, "heading": 0.0}

    def publish_scenario(self, name: str, sensor_scenario: str, detection_scenario: str):
        timestamp_ms = now_ms()
        packet = deepcopy(get_mock_sensor_packet(sensor_scenario))
        packet["timestamp"] = timestamp_ms
        if name == "emergency":
            packet["us_front"] = 12

        update_map(
            self.grid,
            robot_x=self.pose["x"],
            robot_y=self.pose["y"],
            robot_heading=self.pose["heading"],
            sensor_packet=packet,
        )

        pose = {**self.pose, "timestamp_ms": timestamp_ms}
        proximity = {
            **{field: packet[field] for field in PROXIMITY_FIELDS},
            "timestamp_ms": timestamp_ms,
        }
        mission_mode = "idle" if name == "idle" else "run"

        values = {
            MISSION_CONTROL: {
                "mode": mission_mode,
                "emergency_stop": False,
                "timestamp_ms": timestamp_ms,
            },
            ROBOT_POSE: pose,
            OCCUPANCY_GRID: self.grid.data.copy(),
            PLANNED_PATH: [],
            PROXIMITY: proximity,
            DETECTION_RESULT: get_mock_detection(detection_scenario),
        }
        if name != "victim":
            values[TARGET_WAYPOINT] = None
        self.blackboard.update_many(values)

    def tick_and_report(self, name: str, ticks: int = 1):
        for _ in range(ticks):
            self.brain.tick_once()
        trace = self.blackboard.get("decision/trace", {})
        print(f"{name.upper():<10} | {trace.get('status', 'NO_STATUS')}")
        print(f"  reason  : {trace.get('reason', 'not available')}")
        print(f"  source  : {trace.get('source_layer', 'not available')}")
        print(f"  command : {trace.get('command', {})}")

    def run(self):
        print("Project Drishya — merged navigation/decision integration check\n")
        for name, sensor_scenario, detection_scenario in SCENARIOS:
            self.publish_scenario(name, sensor_scenario, detection_scenario)
            # Victim confirmation sets a waypoint on tick one; tick two navigates.
            self.tick_and_report(name, ticks=2 if name == "victim" else 1)


if __name__ == "__main__":
    IntegrationHarness().run()
