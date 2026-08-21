# Simulation Brain

`simulation_brain` is the executable software prototype for Project Drishya, a
search-and-rescue robot that must explore an unknown obstacle-filled environment,
locate a victim, and explain every decision. It connects the repository's shared
Blackboard, occupancy mapper, behavior tree, and learning dependencies into one
repeatable simulation.

## System flow

```text
Hidden ground truth -> simulated ultrasonic/ToF observations -> occupancy grid
  -> safety-first Behavior Tree -> exploration/victim waypoint -> Dijkstra path
  -> validated grid motion -> environment update -> decision trace and metrics
```

This follows the proposal flowchart: sensor or simulation state enters a Behavior
Tree safety check before policy selection and action execution. Reinforcement learning
can influence exploration, but it cannot bypass the Behavior Tree, known-free path
planner, or collision validator.

## Run it

Install the repository and decision dependencies, then run from the repository root:

```bash
python -m pip install -r requirements.txt
python -m pip install -r modules/decision_logic/requirements.txt

python -m simulation_brain --mode visual --scenario maze --seed 7
python -m simulation_brain --mode headless --scenario random --seed 7 --episodes 20
python -m simulation_brain --mode visual --model simulation_brain/models/ppo_explore.zip
```

Available scenarios are `open-room`, `maze`, `corridor`, `blocked-route`,
`unreachable-target`, and `random`. Visual controls are Space to pause, N to advance
one decision tick, and Escape to quit.

The dashboard shows ground truth (evaluation only), the robot's partial occupancy map,
sensor-driven discoveries, Dijkstra route and waypoint, active Behavior Tree behavior,
the latest decision reason, and episode metrics.

## Decision and navigation rules

- The authoritative map is 50 x 50 cells at 10 cm per cell, with the robot starting at
  the shared center origin.
- Ground truth is held privately by `SimulationController`; it is never published to
  the policy Blackboard.
- Explicit sensor hit flags distinguish a real obstacle from a maximum-range reading.
- Dijkstra traverses only known free cells. Unknown and occupied cells are never used
  as shortcuts.
- Exploration chooses a reachable free frontier using shortest distance and information
  gain. A sector preference can come from PPO; a deterministic heuristic is the default.
- A changed goal, invalid next cell, or changed perceived map triggers replanning.
- Fresh victim confidence above the Behavior Tree threshold creates a mission target.
  Reaching its confirmation radius ends the episode successfully.
- If sensing proves that every neighboring cell around a confirmed victim is occupied,
  the mission terminates safely as `victim_unreachable`.

## Blackboard boundary

The simulation reads and writes the existing `mission/control`,
`navigation/robot_pose`, `navigation/occupancy_grid`, `navigation/target_waypoint`,
`navigation/planned_path`, `sensor/proximity`, `detection/result`, and
`decision/trace` keys. It adds `navigation/path_status` and `simulation/metrics`.
Ground truth and the exact hidden victim cell are deliberately excluded.

## Reinforcement learning

The Gymnasium environment uses exactly the same controller, sensing, mapping, planning,
and termination code as the visual simulation. Its observation contains the perceived
grid, normalized pose and heading, proximity ranges, coverage, and frontier-sector
counts. Its four actions prefer the forward, left, backward, or right exploration sector;
Dijkstra still validates and executes the resulting frontier route.

```bash
python -m simulation_brain.rl.train_ppo --timesteps 100000 --seed 7
python -m simulation_brain.rl.evaluate --episodes 10 --seed 7
python -m simulation_brain.rl.evaluate --model simulation_brain/models/ppo_explore.zip
```

Rewards favor new cells, detection, and rescue and penalize time, revisits, and
collisions. Stable-Baselines3 and a checkpoint are optional for the normal demo.

## Metrics and tests

Headless runs emit JSON containing steps, coverage, replans, collisions, detection
count, rescue status, termination reason, elapsed time, and policy source.

```bash
python -m pytest simulation_brain/tests modules/decision_logic/tests -v
```

Version 1 intentionally models one robot and static obstacles. Fire, flood, structural
collapse, chemical hazards, genetic optimization, hardware-in-the-loop operation, and
multi-robot game theory remain later extensions.
