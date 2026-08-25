# Simulation Brain

`simulation_brain` is the executable software prototype for Project Drishya, a
search-and-rescue robot that must explore an unknown obstacle-filled environment,
locate a victim, and explain every decision. It connects the repository's shared
Blackboard, occupancy mapper, behavior tree, and learning dependencies into one
repeatable simulation.

For a complete explanation of the coordinate system, sensing, mapping, Behavior Tree,
A* planning, rescue signal, RL interface, metrics, and defense talking points,
read [`SYSTEM_TECHNICAL_GUIDE.md`](SYSTEM_TECHNICAL_GUIDE.md).

## System flow

```text
Hidden ground truth -> simulated ultrasonic/ToF observations -> occupancy grid
  -> safety-first Behavior Tree -> exploration/victim waypoint -> A* path
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

.drishya/bin/python -m simulation_brain --mode visual --scenario studio-apartment --seed 7
.drishya/bin/python -m simulation_brain --presentation
.drishya/bin/python -m simulation_brain --mode visual --scenario maze --moving-obstacles 3 --obstacle-interval 6
.drishya/bin/python -m simulation_brain --mode headless --scenario random --seed 7 --episodes 20
.drishya/bin/python -m simulation_brain --mode visual --model simulation_brain/models/ppo_explore.zip
```

The six building scenarios are `studio-apartment`, `two-bedroom-house`, `office-suite`,
`clinic-ward`, `warehouse`, and `collapsed-house`. They have fixed walls, rooms,
doorways, corridors, and furniture, while the seed selects a reachable victim from
room-specific candidates. The original `open-room`, `maze`, `corridor`,
`blocked-route`, `unreachable-target`, and `random` fixtures remain available for
regression demonstrations. The visual simulator opens in Robot Perception mode
at presentation-friendly half speed. Use `--speed 0.25`, `0.5`, `1.0`, or `2.0` to
change the initial playback rate.

### Midterm presentation mode

Use the curated presentation entry point:

```bash
.drishya/bin/python -m simulation_brain --presentation
```

This one command selects the two-bedroom house, deterministic seed `4`, half-speed
playback, Robot Perception view, and no moving hazards. It opens paused on a short
project briefing; press `Enter` to begin. The dashboard shows the live
`Sense → Map → BT → A* → Move` pipeline and the complete Behavior Tree priority
selector. Ground Truth view adds room labels, while Robot Perception receives neither
those labels nor hidden geometry.

Presentation mode starts without moving hazards so the core system story remains
clear. Demonstrate replanning with `O` and a mouse click, press `D` to add one autonomous
hazard, or launch with `--moving-obstacles 1`. Press `H` for the four-minute defense
guide and `L` for an honest RL-readiness panel. This simulation intentionally presents the software intelligence layer;
hardware integration, physical sensor calibration, and field testing remain later work.

The single-map dashboard contains a top-down rescue rover with four wheels, ToF bar,
ultrasonic indicators, WiFi antenna, heading marker, and behavior status light. Smooth
movement is visual only: the controller, Behavior Tree, A* planner, and metrics
continue to use authoritative grid cells.

### Presentation controls

Every action is available through an on-screen button and a keyboard shortcut:

| Key | Action |
|---|---|
| `Space` | Run or pause |
| `Enter` | Start the guided presentation mission |
| `N` | Advance one decision step |
| `R` | Reset the same scenario and seed |
| `G` | Toggle Robot Perception and Ground Truth |
| `S` | Show or hide ultrasonic/ToF rays |
| `P` | Show or hide the A* path and target |
| `O` | Toggle obstacle-editing mode; click a map cell to add/remove a wall |
| `D` | Pause or resume autonomous moving obstacles |
| `H` | Show or hide the midterm presentation guide |
| `L` | Show or hide the RL readiness glimpse |
| `+` / `-` | Increase or decrease playback speed |
| `Esc` | Exit |

Robot Perception is the scientifically honest default: hidden obstacles and the victim
remain concealed until sensed or confirmed. Ground Truth is an explicit presentation
view and is never published to the Blackboard or RL observation.

### Dynamic obstacles and replanning

Press `O` or click **Edit On**, then click any interior map cell to add an obstacle.
Click the same cell again to remove it. The editor treats the change as an observed map
event: ground truth and occupancy are updated together, the old route is invalidated,
and A* immediately finds a new route around the obstacle. Boundary, robot, and
victim cells are protected. The highlighted cell, edit count, and decision message make
the replanning event visible during a demonstration.

Visual mode starts with two orange autonomous obstacles. They move one safe grid cell
every 10 decision ticks and are tracked as observed hazards. Before each move is
accepted, the simulator prevents entry into the robot or victim cell and verifies that
the victim remains reachable in ground truth. The perceived grid and any affected path
are then updated before robot motion, so A* never deliberately follows a route
through a moving obstacle. Configure this behavior with:

```bash
.drishya/bin/python -m simulation_brain --mode visual --scenario maze \
  --moving-obstacles 3 --obstacle-interval 6
```

Use `--moving-obstacles 0` for the original static demonstration. Headless and RL runs
default to zero moving obstacles so established evaluation results stay comparable.

### Suggested defense demonstration

1. Run `python -m simulation_brain --presentation` and explain the system boundary.
2. Press Enter, then pause with Space and use N for one sense-map-decide-move cycle.
3. Point out sensor rays, the perceived map, the active BT branch, and A* path.
4. Press G briefly to reveal the fixed house and hidden victim, then return to perception.
5. Press L to explain that PPO is training-ready but not trained; the heuristic is active.
6. Resume and finish at `Victim Located — Signal Transmitted` with approximately 69%
   coverage and zero collisions for the curated seed.

## Decision and navigation rules

- The authoritative map is 50 x 50 cells at 10 cm per cell, with the robot starting at
  the shared center origin.
- Ground truth is held privately by `SimulationController`; it is never published to
  the policy Blackboard.
- Explicit sensor hit flags distinguish a real obstacle from a maximum-range reading.
- A* traverses only known free cells. Unknown and occupied cells are never used
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
`decision/trace` keys. It adds `navigation/path_status`, `simulation/metrics`, and
`simulation/rescue_signal`.
Interactive edits are reported through `simulation/map_edit`. Ground truth and the
exact hidden victim cell are deliberately excluded.

The rescue signal is published once after confirmed arrival and contains the victim
grid cell, world coordinates, confidence, coverage, and timestamp. This represents
location transmission to a rescue team—not physical evacuation by the simulated rover.

## Reinforcement-learning curriculum

Training and deployment deliberately use different action executors around the same
house, sensor, occupancy, detection, and termination state. During training, the four
relative actions (`forward`, `left`, `backward`, `right`) attempt the adjacent cell
directly. A hidden wall attempt leaves the rover in place, increments collision metrics,
and applies an escalating penalty. This gives PPO an observable collision-learning
signal. During deployment, PPO only proposes a directional exploration preference;
the Behavior Tree, known-free collision check, and A* planner retain final motion
authority.

The versioned `house-rescue-v2` observation has 2,517 values: the perceived 50×50 grid,
pose and heading, five ranges, coverage, four frontier counts, detection confidence,
two victim-relative values, and the previous-collision flag. Victim-relative values are
exactly zero until WiFi confidence confirms the victim. Older 2,513-value checkpoints
are rejected with a retraining message and deployment safely falls back to the frontier
heuristic.

Train the same PPO model from the simplest house through the most difficult one, then
fine-tune it on a deterministic mixed-house rotation:

```bash
.drishya/bin/python -m simulation_brain.rl.train_ppo \
  --preset quick --seed 7 --dashboard

.drishya/bin/python -m simulation_brain.rl.train_ppo \
  --preset full --seed 7 --dashboard \
  --resume simulation_brain/models/latest.zip
```

`quick` uses 5,000 timesteps per house plus 10,000 mixed timesteps. `full` uses 50,000
per house plus 100,000 mixed timesteps. A checkpoint is written after each stage,
along with `latest.zip` and `house_rescue_final.zip`. Closing the Pygame training
dashboard only disables drawing; training continues headlessly.

Rewards are `+0.05` per newly observed cell, `+25` on first confirmation, `+0.5` per
cell of confirmed-victim progress, and `+100` for rescue. Costs are `-0.02` per step,
`-0.1` for no discovery, `-8` plus an escalating repeat cost per collision, and `-10`
at timeout.

Evaluate random, deterministic-frontier, and trained PPO policies on both the training
victim seeds and unseen victim seeds:

```bash
.drishya/bin/python -m simulation_brain.rl.evaluate \
  --model simulation_brain/models/house_rescue_final.zip \
  --suite houses --episodes-per-scenario 20
```

The evaluator and trainer create dependency-free CSV, JSON, and self-contained HTML/SVG
reports under `simulation_brain/reports/`. Per-house tables compare measured first and
final episode windows without claiming a guaranteed improvement percentage.

Replay an early random episode and a trained episode on the identical house and seed:

```bash
.drishya/bin/python -m simulation_brain.rl.replay \
  --scenario two-bedroom-house --policy random --seed 7

.drishya/bin/python -m simulation_brain.rl.replay \
  --scenario two-bedroom-house \
  --model simulation_brain/models/house_rescue_final.zip --seed 7
```

Stable-Baselines3 and a trained checkpoint remain optional for the normal demonstration.

## Metrics and tests

Headless runs emit JSON containing steps, coverage, replans, collisions, detection
count, rescue status, signal-transmission status, termination reason, elapsed time,
and policy source.

```bash
python -m pytest simulation_brain/tests modules/decision_logic/tests -v
```

Version 1 intentionally models one robot, walls, furniture, rubble, and optional moving
obstacles. Fire, flood, chemical hazards, genetic optimization, hardware-in-the-loop
operation, and multi-robot game theory remain later extensions.
