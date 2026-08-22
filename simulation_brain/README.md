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

.drishya/bin/python -m simulation_brain --mode visual --scenario maze --seed 7
.drishya/bin/python -m simulation_brain --mode headless --scenario random --seed 7 --episodes 20
.drishya/bin/python -m simulation_brain --mode visual --model simulation_brain/models/ppo_explore.zip
```

Available scenarios are `open-room`, `maze`, `corridor`, `blocked-route`,
`unreachable-target`, and `random`. The visual simulator opens in Robot Perception mode
at presentation-friendly half speed. Use `--speed 0.25`, `0.5`, `1.0`, or `2.0` to
change the initial playback rate.

The single-map dashboard contains a top-down rescue rover with four wheels, ToF bar,
ultrasonic indicators, WiFi antenna, heading marker, and behavior status light. Smooth
movement is visual only: the controller, Behavior Tree, Dijkstra planner, and metrics
continue to use authoritative grid cells.

### Presentation controls

Every action is available through an on-screen button and a keyboard shortcut:

| Key | Action |
|---|---|
| `Space` | Run or pause |
| `N` | Advance one decision step |
| `R` | Reset the same scenario and seed |
| `G` | Toggle Robot Perception and Ground Truth |
| `S` | Show or hide ultrasonic/ToF rays |
| `P` | Show or hide the Dijkstra path and target |
| `O` | Toggle obstacle-editing mode; click a map cell to add/remove a wall |
| `+` / `-` | Increase or decrease playback speed |
| `Esc` | Exit |

Robot Perception is the scientifically honest default: hidden obstacles and the victim
remain concealed until sensed or confirmed. Ground Truth is an explicit presentation
view and is never published to the Blackboard or RL observation.

### Dynamic obstacles and replanning

Press `O` or click **Edit On**, then click any interior map cell to add an obstacle.
Click the same cell again to remove it. The editor treats the change as an observed map
event: ground truth and occupancy are updated together, the old route is invalidated,
and Dijkstra immediately finds a new route around the obstacle. Boundary, robot, and
victim cells are protected. The highlighted cell, edit count, and decision message make
the replanning event visible during a demonstration.

### Suggested defense demonstration

1. Start `maze` in Robot Perception view and explain that gray cells are unknown.
2. Pause with Space and use N to show one sensor-map-decision cycle at a time.
3. Point out cyan ultrasonic rays, purple ToF rays, the yellow Dijkstra route, and the
   rover's heading marker.
4. Press G briefly to compare the hidden ground truth, then return to perception.
5. Resume and show the human-readable Behavior Tree decision and live metrics.
6. Allow the run to finish at the Victim Rescued overlay, or use
   `unreachable-target` to demonstrate a safe failure state.

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
Interactive edits are reported through `simulation/map_edit`. Ground truth and the
exact hidden victim cell are deliberately excluded.

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
