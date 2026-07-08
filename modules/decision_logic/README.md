# Decision Logic Module

This module is the robot's high-level decision layer. Maintained by Suwarna, it reads the shared
system state, decides what the robot should do next, and publishes navigation
or mission commands back to the shared blackboard.

The planned decision stack combines:

- A behavior tree for predictable mission flow and safety checks.
- Reinforcement learning experiments for exploration strategy tuning.
- A lightweight runtime loop that ticks the decision logic at a fixed rate.

## Responsibilities

- Choose the robot's current mission state: searching, navigating, confirming,
  returning, or stopping.
- Prioritize safety conditions before exploration or victim-search behavior.
- Consume navigation, map, sensor, and WiFi detection outputs from shared
  modules.
- Publish clear intent for the navigation module to execute.
- Keep experimental RL training separate from runtime decision execution.

## Expected Structure

```text
decision_logic/
├── README.md
├── brain.py              # Runtime loop that ticks the decision system
├── behavior_tree/        # Behavior tree nodes and tree assembly
├── rl_env/               # Custom SARExploreEnv-style training environment
└── train_ppo.py          # PPO training entry point for exploration policies
```

Some of these files may not exist yet. Add them as the implementation grows.

## Blackboard Contract

The decision layer should treat `shared/` as the integration boundary. Avoid
direct imports from sibling modules unless the team agrees on a shared API.

Likely inputs:

- Robot pose and heading from navigation.
- Occupancy grid or explored/frontier state from mapping.
- Obstacle and proximity data from sensors or simulation.
- Detection confidence and estimated target location from WiFi detection.
- Mission flags such as start, pause, emergency stop, and completion.

Likely outputs:

- Current behavior state for dashboard display.
- Target waypoint or exploration frontier for navigation.
- Stop, pause, resume, or return-to-base commands.
- Detection-confirmation requests when WiFi confidence is high.

When adding real keys, document the exact key names, value types, and owner
module here.

## Runtime Flow

1. Read the latest shared state from the blackboard.
2. Run safety and mission-precondition checks.
3. Tick the behavior tree.
4. Select the next action or navigation intent.
5. Write the decision output back to the blackboard.
6. Sleep until the next tick.

The target runtime tick rate from the architecture is 10 Hz.

## Behavior Tree Notes

Recommended top-level priority order:

1. Emergency stop or unsafe sensor state.
2. Confirm and report a high-confidence victim detection.
3. Navigate to an active target waypoint.
4. Explore unknown frontier regions.
5. Idle or wait for mission start.

Keep behavior nodes small and testable. Each node should read only the state it
needs and write only the command it owns.

## RL Environment Notes

The RL environment should be used for training and evaluation experiments, not
as the only source of runtime safety behavior.

Useful state features may include:

- Robot pose.
- Local obstacle layout.
- Explored-area percentage.
- Frontier distance.
- Detection confidence.
- Distance to last known target estimate.

Useful reward signals may include:

- Positive reward for newly explored cells.
- Positive reward for confirming a target.
- Penalty for collisions or unsafe proximity.
- Small time penalty to encourage efficient search.

## Development Checklist

- Define the real blackboard key names before wiring runtime integration.
- Add behavior tree unit tests as soon as behavior nodes are implemented.
- Keep training artifacts, checkpoints, and logs out of git unless they are
  intentionally small reference files.
- Update this README whenever the module contract changes.
