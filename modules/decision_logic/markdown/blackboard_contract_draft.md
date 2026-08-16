# Draft Blackboard Contract For Decision Logic

This is a draft to discuss with the team. Do not treat it as final until navigation, WiFi detection, simulation, and decision logic owners agree.

## Inputs Read By Decision Logic

| Key | Owner | Required fields | Notes |
|---|---|---|---|
| `mission/control` | Simulator/dashboard/operator | `mode`, `emergency_stop`, `timestamp_ms` | `mode` can be `idle`, `run`, `pause`, `return`, `stop`. |
| `robot/pose` | Navigation/simulation | `x`, `y`, `theta_deg`, `timestamp_ms` | Coordinates must follow root README convention. |
| `map/occupancy_grid` | Navigation | 50 x 50 grid | Suggested encoding: unknown `-1`, free `0`, occupied `1`, hazard `2`. |
| `navigation/path` | Navigation | `points`, `status`, `timestamp_ms` | `status` can be `none`, `planning`, `ready`, `blocked`, `reached`. |
| `navigation/frontier` | Navigation | `target_x`, `target_y`, `score`, `timestamp_ms` | Used for exploration baseline. |
| `sensors/proximity` | Navigation/simulation | `front_cm`, `left_cm`, `right_cm`, `timestamp_ms` | Decision logic only needs processed proximity, not raw sensor rays. |
| `detection/result` | WiFi detection | `human_x`, `human_y`, `confidence`, `timestamp_ms` | Confidence should be from `0.0` to `1.0`. |

## Outputs Written By Decision Logic

| Key | Consumer | Required fields | Notes |
|---|---|---|---|
| `state/motor_command` | Simulator/hardware motor layer | `left_speed`, `right_speed`, `duration_ms`, `reason`, `timestamp_ms` | Speed range should be agreed, suggested `-100` to `100`. |
| `decision/state` | Dashboard/logs | `mission_state`, `active_behavior`, `last_transition`, `timestamp_ms` | Used for visualization and debugging. |
| `decision/target` | Navigation | `x`, `y`, `target_type`, `priority`, `timestamp_ms` | `target_type` can be `victim`, `frontier`, `return_home`. |
| `decision/trace` | Dashboard/logs | `tick_id`, `selected_action`, `reason`, `source_layer`, `timestamp_ms` | Can be latest trace entry or a bounded recent list. |
| `detection/confirm_request` | WiFi detection/simulation | `target_x`, `target_y`, `required_confidence`, `timestamp_ms` | Optional, used when confirmation behavior exists. |

## Example Input Payloads

```python
mission_control = {
    "mode": "run",
    "emergency_stop": False,
    "timestamp_ms": 1780000000000,
}

robot_pose = {
    "x": 12.0,
    "y": 8.0,
    "theta_deg": 90.0,
    "timestamp_ms": 1780000000000,
}

detection_result = {
    "human_x": 20.0,
    "human_y": 14.0,
    "confidence": 0.82,
    "timestamp_ms": 1780000000000,
}

proximity = {
    "front_cm": 42.0,
    "left_cm": 55.0,
    "right_cm": 31.0,
    "timestamp_ms": 1780000000000,
}
```

## Example Output Payloads

```python
motor_command = {
    "left_speed": 0,
    "right_speed": 0,
    "duration_ms": 100,
    "reason": "emergency_stop_requested",
    "timestamp_ms": 1780000000100,
}

decision_state = {
    "mission_state": "stopped",
    "active_behavior": "EmergencyStopSequence",
    "last_transition": "searching -> stopped",
    "timestamp_ms": 1780000000100,
}

decision_target = {
    "x": 20.0,
    "y": 14.0,
    "target_type": "victim",
    "priority": 100,
    "timestamp_ms": 1780000000100,
}

decision_trace = {
    "tick_id": 145,
    "selected_action": "SetVictimTarget",
    "reason": "detection_confidence_0.82_above_threshold_0.75",
    "source_layer": "BT_MISSION",
    "timestamp_ms": 1780000000100,
}
```

## Contract Rules

- Decision logic must not act on stale data.
- Decision logic must not move the robot if mission mode is `idle`, `pause`, or `stop`.
- Emergency stop must override all other behavior.
- Obstacle safety must override victim navigation and exploration.
- RL output must be supervised by Behavior Tree safety.
- Every motor command should include a reason.

