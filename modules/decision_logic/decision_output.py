"""Centralized, bounded decision outputs and explainability traces."""

from __future__ import annotations

import math

from modules.decision_logic.contracts import (
    BT_STATUS,
    DECISION_STATE,
    DECISION_TICK_ID,
    DECISION_TRACE,
    MAX_COMMAND_DURATION_MS,
    MISSION_CONTROL,
    MOTOR_COMMAND,
    MOTOR_MAX,
    MOTOR_MIN,
    now_ms,
)


STOP_COMMAND = {"left_speed": 0, "right_speed": 0, "duration_ms": 0}


def sanitize_motor_command(command: dict) -> dict:
    """Return a motor command clamped to the agreed hardware-safe envelope."""
    if not isinstance(command, dict):
        return dict(STOP_COMMAND)

    def bounded_int(field: str, minimum: int, maximum: int) -> int:
        value = command.get(field, 0)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            return 0
        return max(minimum, min(maximum, int(value)))

    return {
        "left_speed": bounded_int("left_speed", MOTOR_MIN, MOTOR_MAX),
        "right_speed": bounded_int("right_speed", MOTOR_MIN, MOTOR_MAX),
        "duration_ms": bounded_int("duration_ms", 0, MAX_COMMAND_DURATION_MS),
    }


def publish_decision(
    blackboard,
    *,
    behavior: str,
    status: str,
    reason: str,
    source_layer: str,
    command: dict,
) -> dict:
    """Publish the final command, state, and machine-readable explanation."""
    safe_command = sanitize_motor_command(command)
    timestamp_ms = now_ms()
    mission = blackboard.get(MISSION_CONTROL, {})
    mission_mode = mission.get("mode", "unknown") if isinstance(mission, dict) else "invalid"
    tick_id = blackboard.get(DECISION_TICK_ID, 0)

    state = {
        "mission_state": mission_mode,
        "active_behavior": behavior,
        "status": status,
        "timestamp_ms": timestamp_ms,
    }
    trace = {
        "tick_id": tick_id,
        "selected_action": behavior,
        "reason": reason,
        "source_layer": source_layer,
        "status": status,
        "command": dict(safe_command),
        "timestamp_ms": timestamp_ms,
    }

    outputs = {
        MOTOR_COMMAND: safe_command,
        BT_STATUS: status,
        DECISION_STATE: state,
        DECISION_TRACE: trace,
    }
    if hasattr(blackboard, "update_many"):
        blackboard.update_many(outputs)
    else:
        for key, value in outputs.items():
            blackboard.set(key, value)
    return safe_command
