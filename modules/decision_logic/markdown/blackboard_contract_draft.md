# Draft Blackboard Contract For Decision Logic

This is a draft to discuss with the team. Do not treat it as final until navigation, WiFi detection, simulation, and decision logic owners agree.

## Inputs Read By Decision Logic

| Key | Owner | Required fields | Notes |
|---|---|---|---|
| `mission/control` | Simulator/dashboard/operator | `mode`, `emergency_stop`, `timestamp_ms` | `mode` can be `idle`, `run`, `pause`, `return`, `stop`. |
| `navigation/robot_pose` | Navigation/simulation | `x`, `y`, `heading`, `timestamp_ms` | Centimetres and degrees; follows root convention. |
| `navigation/occupancy_grid` | Navigation | NumPy array shaped `(50, 50)` | Unknown `2`, free `0`, occupied `1`. |
| `navigation/planned_path` | Navigation | List of `(row, col)` cells | Empty until path planning is implemented. |
| `navigation/target_waypoint` | Decision logic | `(row, col)` or `None` | Temporary integration key consumed by navigation. |
| `sensor/proximity` | Navigation/simulation | Five `us_*` fields plus `timestamp_ms` | Distances are centimetres; `0` means unavailable. |
| `detection/result` | WiFi detection | `human_x`, `human_y`, `confidence`, `timestamp_ms` | Confidence should be from `0.0` to `1.0`. |

## Outputs Written By Decision Logic

| Key | Consumer | Required fields | Notes |
|---|---|---|---|
| `state/motor_command` | Simulator/hardware motor layer | `left_speed`, `right_speed`, `duration_ms` | Speeds are clamped to `[-255, 255]`; duration to `[0, 1000]` ms. |
| `state/bt_status` | Dashboard/logs | String | Concise status for display. |
| `decision/state` | Dashboard/logs | `mission_state`, `active_behavior`, `status`, `timestamp_ms` | Latest decision state. |
| `decision/trace` | Dashboard/logs | `tick_id`, `selected_action`, `reason`, `source_layer`, `status`, `command`, `timestamp_ms` | Latest structured explanation. |
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
    "heading": 90.0,
    "timestamp_ms": 1780000000000,
}

detection_result = {
    "human_x": 20.0,
    "human_y": 14.0,
    "confidence": 0.82,
    "timestamp_ms": 1780000000000,
}

proximity = {
    "us_front": 42.0,
    "us_left45": 55.0,
    "us_left90": 60.0,
    "us_right45": 31.0,
    "us_right90": 48.0,
    "timestamp_ms": 1780000000000,
}
```

## Example Output Payloads

```python
motor_command = {
    "left_speed": 0,
    "right_speed": 0,
    "duration_ms": 100,
}

decision_state = {
    "mission_state": "stopped",
    "active_behavior": "EmergencyStopSequence",
    "status": "EMERGENCY_STOP [operator]",
    "timestamp_ms": 1780000000100,
}

decision_trace = {
    "tick_id": 145,
    "selected_action": "SetVictimTarget",
    "reason": "detection_confidence_0.82_above_threshold_0.75",
    "source_layer": "BT_MISSION",
    "status": "VICTIM_CONFIRMED",
    "command": motor_command,
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
