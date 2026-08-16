"""Shared Blackboard keys and runtime contract constants for decision logic."""

from __future__ import annotations

import math
import time
from typing import Any


MISSION_CONTROL = "mission/control"
ROBOT_POSE = "navigation/robot_pose"
OCCUPANCY_GRID = "navigation/occupancy_grid"
PLANNED_PATH = "navigation/planned_path"
TARGET_WAYPOINT = "navigation/target_waypoint"
PROXIMITY = "sensor/proximity"
DETECTION_RESULT = "detection/result"

MOTOR_COMMAND = "state/motor_command"
BT_STATUS = "state/bt_status"
DECISION_STATE = "decision/state"
DECISION_TRACE = "decision/trace"
DECISION_TICK_ID = "decision/tick_id"

MISSION_MODES = {"idle", "run", "pause", "return", "stop"}
PROXIMITY_FIELDS = (
    "us_front",
    "us_left45",
    "us_left90",
    "us_right45",
    "us_right90",
)

MAX_STATE_AGE_MS = 1_500
MAX_DETECTION_AGE_MS = 5_000
MAX_FUTURE_SKEW_MS = 1_000

MOTOR_MIN = -255
MOTOR_MAX = 255
MAX_COMMAND_DURATION_MS = 1_000


def now_ms() -> int:
    """Return current Unix time in milliseconds."""
    return int(time.time() * 1_000)


def payload_timestamp_ms(payload: Any) -> int | None:
    """Read the canonical timestamp, accepting the legacy name during migration."""
    if not isinstance(payload, dict):
        return None
    value = payload.get("timestamp_ms", payload.get("timestamp"))
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        return None
    return int(value)


def is_fresh(payload: Any, max_age_ms: int, current_time_ms: int | None = None) -> bool:
    """Return whether a timestamped payload is recent and not far in the future."""
    timestamp_ms = payload_timestamp_ms(payload)
    if timestamp_ms is None:
        return False
    current = now_ms() if current_time_ms is None else current_time_ms
    age_ms = current - timestamp_ms
    return -MAX_FUTURE_SKEW_MS <= age_ms <= max_age_ms
