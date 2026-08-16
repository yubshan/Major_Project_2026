# Decision Logic Module

**Owner:** Suwarna (Decision Logic / Teammate B)  
**Project:** [Drishya](https://github.com/yubshan/Major_Project_2026) — autonomous rescue robot for search-and-exploration missions

This module is the robot's high-level brain. It reads shared system state from `shared/blackboard.py`,
decides what the robot should do next, and writes navigation or mission commands back for other
modules to execute.

The decision stack is planned to combine:

- A **behavior tree** (`py_trees`) for predictable mission flow and safety checks.
- **Reinforcement learning** experiments (Stable-Baselines3 PPO) for exploration strategy tuning.
- A lightweight **runtime loop** (`brain.py`) that ticks the decision logic at 10 Hz.

The initial implementation includes a priority behavior tree, a Gymnasium exploration environment,
PPO training support, mock-driven tests, and a terminal demo.

Install its dependencies from the repository root:

```bash
python -m pip install -r modules/decision_logic/requirements.txt
```

## Role in the System

```text
  wifi_detection ──writes──►  shared/blackboard  ◄──reads──  navigation
  simulation_viz ──reads────►       ▲                writes──► decision_logic
                                    │
                              decision_logic
                              (this module)
```

Decision logic sits in the middle: it consumes pose, map, sensor, and detection data; it publishes
intent (waypoints, stop/resume, mission state) for navigation and the dashboard to act on.

Per `shared/blackboard.py`, this module should:

- **Read** blackboard keys written by WiFi detection, navigation, and sensors.
- **Write** outputs such as `state/motor_command` and behavior state for the simulator UI.

The current blackboard contract is documented below. Coordinate any contract change with the
navigation, sensing, and WiFi-detection owners.

## Responsibilities

- Choose the robot's current mission state: searching, navigating, confirming, returning, or stopping.
- Run safety checks before exploration or victim-search behavior.
- Consume navigation, map, sensor, and WiFi detection outputs from the blackboard.
- Publish clear intent for the navigation module to execute.
- Keep RL training scripts separate from the runtime decision loop.

## Expected Structure

```text
decision_logic/
├── README.md
├── brain.py              # Runtime loop that ticks the decision system @ 10 Hz
├── behavior_tree/        # py_trees Behavior sub-classes and tree assembly
├── rl_env/               # Custom SARExploreEnv-style Gymnasium environment
└── train_ppo.py          # PPO training entry point for exploration policies
```

## Blackboard Contract

Treat `shared/` as the only integration boundary. Do not import sibling modules directly unless the
team agrees on a shared API.

### Inputs

| Key | Value |
|-----|-------|
| `navigation/robot_pose` | `{x, y, heading}` in centimetres/degrees |
| `navigation/occupancy_grid` | 50 x 50 NumPy array using the shared grid constants |
| `navigation/target_waypoint` | `(row, col)` or `None` |
| `sensor/proximity` | Direction-to-distance mapping in centimetres |
| `detection/result` | Human position, confidence, and timestamp |

### Outputs

| Key | Value |
|-----|-------|
| `navigation/target_waypoint` | Confirmed victim waypoint |
| `state/motor_command` | `{left_speed, right_speed, duration_ms}` |
| `state/bt_status` | Human-readable active behavior state |

## Runtime Flow

1. Read the latest shared state from the blackboard.
2. Run safety and mission-precondition checks.
3. Tick the behavior tree.
4. Select the next action or navigation intent.
5. Write decision outputs back to the blackboard.
6. Sleep until the next tick (target: **10 Hz**).

## Behavior Tree Design

Recommended top-level priority order:

1. Emergency stop or unsafe sensor state.
2. Confirm and report a high-confidence victim detection.
3. Navigate to an active target waypoint.
4. Explore unknown frontier regions.
5. Idle or wait for mission start.

Keep nodes small and testable. Each node should read only the state it needs and write only the
command it owns.

## Developing Before Other Modules Are Ready

Use the module's deterministic demo fixtures to develop and test in isolation:

- `modules/decision_logic/demo_data.py` — fake WiFi detections, occupancy grids, poses, and sensors.

These let you build and unit-test behavior tree nodes without waiting for the full stack or Pygame
simulator to be running.

## RL Environment Notes

Use RL for training and evaluation experiments, not as the only source of runtime safety behavior.

**State features:** robot pose, local obstacles, explored-area %, frontier distance, detection
confidence, distance to last known target.

**Reward signals:** reward for newly explored cells and confirmed targets; penalties for collisions,
unsafe proximity, and wasted time.

## Dependencies (planned)

Root `requirements.txt` currently lists simulation deps. Decision logic will additionally need:

- `py_trees` — behavior tree runtime
- `gymnasium` + `stable-baselines3` — RL training (optional, for `train_ppo.py`)

Add these to `requirements.txt` when implementation begins.

## Development Checklist

- [ ] Agree on blackboard key names with navigation and WiFi leads.
- [x] Implement `brain.py` runtime loop at 10 Hz.
- [x] Add behavior tree nodes under `behavior_tree/`.
- [x] Add unit tests for each behavior node.
- [x] Keep training checkpoints and logs out of git.
- [x] Document the current blackboard contract.
