# Project Drishya Simulation Brain — Complete Technical Guide

This document explains what the current simulation does, why each part exists, how
data moves through the system, what is genuinely implemented, and what remains future
work. It is intended both as a learning reference and as preparation for a project
presentation or technical defense.

## 1. What the simulation proves

Project Drishya models a search-and-rescue rover operating inside an unknown building.
The current software prototype demonstrates that the rover can:

1. start without knowledge of the building;
2. observe nearby free space and obstacles using simulated ultrasonic and ToF sensors;
3. build an occupancy map incrementally;
4. select actions through a safety-first Behavior Tree;
5. choose useful exploration frontiers;
6. plan shortest collision-free routes using A*;
7. detect a hidden victim from simulated WiFi confidence;
8. navigate to the confirmed victim;
9. transmit the victim's location to a rescue coordinator; and
10. publish explainable decisions and measurable episode results.

This is a software-intelligence simulation. It does **not** claim that a physical robot,
real WiFi localization system, calibrated sensors, radio transmitter, or evacuation
mechanism has already been built.

## 2. Curated midterm demonstration

Run this from the repository root:

```bash
.drishya/bin/python -m simulation_brain --presentation
```

The presentation preset resolves to:

| Setting | Value |
|---|---:|
| Scenario | `two-bedroom-house` |
| Seed | `4` |
| Grid | 50 × 50 cells |
| Cell size | 10 cm |
| Simulated area | 5 m × 5 m |
| Playback | 0.5× |
| Initial map view | Robot Perception |
| Initial state | Paused introduction |
| Moving hazards | None |
| Exploration policy | Deterministic heuristic unless a valid PPO model is supplied |

The expected deterministic seed-4 result is:

```text
Victim reached:      yes
Signal transmitted: yes
Steps:               344
Coverage:            68.64%
Collisions:          0
Policy:              heuristic
```

The exact wall-clock time depends on display speed and hardware. Simulation steps and
the resulting trajectory remain deterministic for the same seed and actions.

## 3. High-level architecture

```text
PRIVATE SIMULATION STATE
  Ground-truth building + hidden victim + robot cell
                         │
                         ▼
PERCEPTION
  Ultrasonic rays + ToF rays + noisy WiFi confidence
                         │
                         ▼
SHARED BLACKBOARD
  Perceived occupancy map + pose + proximity + detection
                         │
                         ▼
BEHAVIOR TREE (priority selector)
  Safety → emergency → victim → navigation → exploration → idle
                         │
                         ▼
PLANNING
  Frontier goal or victim goal → A* over known-free cells
                         │
                         ▼
VALIDATED MOTION
  One four-connected grid step, checked against ground truth
                         │
                         ▼
RESULTS
  Updated environment + decision trace + metrics + rescue signal
```

The visual dashboard presents the same process as:

```text
SENSE → MAP → BT → A* → MOVE
```

The renderer is only a view of the state. Smooth animation never changes the
authoritative robot cell, decisions, map, or metrics.

## 4. Ground truth versus robot perception

The simulator maintains two very different maps.

### 4.1 Ground-truth map

Ground truth contains every wall, furniture block, rubble cell, moving hazard, and the
real victim position. It is used only by the simulated world, sensors, collision check,
tests, and explicit Ground Truth presentation view.

Ground truth is **not** written to the Blackboard and is not included in an RL
observation.

### 4.2 Perceived occupancy map

The rover begins with a 50×50 grid filled with `UNKNOWN`. Sensor rays gradually change
cells to `FREE` or `OCCUPIED`.

| Cell value | Meaning | Display |
|---:|---|---|
| `0` | Known free | Light |
| `1` | Known occupied | Dark wall |
| `2` | Unknown | Gray |

Coverage is calculated as:

```text
coverage % = 100 × number of non-UNKNOWN cells / 2500
```

Room labels are renderer annotations. They appear only in Ground Truth view and never
enter the robot's perceived map or policy observation.

## 5. Coordinates, headings, and movement

The shared coordinate convention places the robot's initial physical origin at the
center of the map.

```text
Grid start:  (row=25, col=25)
World start: (x=0 cm, y=0 cm)
1 cell:      10 cm
```

Conversions are:

```text
col = round(x / 10) + 25
row = round(-y / 10) + 25

x = (col - 25) × 10
y = -(row - 25) × 10
```

The negative sign exists because screen/grid rows increase downward while world `+Y`
points upward.

The authoritative rover uses four-connected motion:

| Heading | Grid movement | Screen direction |
|---:|---|---|
| `0°` | `(row, col + 1)` | Right/east |
| `90°` | `(row - 1, col)` | Up/north |
| `180°` | `(row, col - 1)` | Left/west |
| `270°` | `(row + 1, col)` | Down/south |

Diagonal motion is disabled. A simulation step can move the rover by at most one cell.

## 6. Scenarios and determinism

Six structured building scenarios are available:

| Scenario | Main structures |
|---|---|
| `studio-apartment` | Living/sleeping area, kitchen, bathroom, furniture |
| `two-bedroom-house` | Two bedrooms, bathroom, living room, kitchen, hallway |
| `office-suite` | Lobby, offices, cubicles, meeting room, corridors |
| `clinic-ward` | Reception, treatment rooms, beds, storage, passages |
| `warehouse` | Loading area, shelving aisles, storage, alternate routes |
| `collapsed-house` | Damaged rooms, rubble, blocked passages, detours |

The older `open-room`, `corridor`, `maze`, `blocked-route`, `unreachable-target`, and
`random` scenarios remain available for regression and algorithm demonstrations.

For a house scenario:

- walls and furniture are fixed;
- the seed selects one victim from scenario-specific room candidates;
- candidates are validated as free and reachable from the start;
- the starting 5×5 region is cleared; and
- the same scenario and seed reproduce the same initial world.

Seed `4` is used for the midterm because it produces enough exploration to demonstrate
mapping without making the presentation unnecessarily long.

## 7. Simulated sensors

### 7.1 Ultrasonic sensors

Five ray sensors are simulated relative to the rover heading:

| Field | Relative angle |
|---|---:|
| `us_front` | `0°` |
| `us_left45` | `+45°` |
| `us_left90` | `+90°` |
| `us_right45` | `-45°` |
| `us_right90` | `-90°` |

The default range is 8 cells, or 80 cm. Rays use Bresenham line traversal. Each result
contains:

- measured distance in centimetres;
- the traversed grid cells;
- an explicit hit/no-hit flag; and
- a timestamp.

The hit flag is important. If a ray reaches maximum range without hitting anything,
all visible cells are marked free and the endpoint is **not** incorrectly marked as an
obstacle.

### 7.2 ToF representation

The simulated ToF sensor casts eight forward rays from `-28°` through `+28°` in 8°
increments. Their depths are repeated vertically to form a compact 8×8-compatible
depth grid.

This is a simplified 2D representation for integration and visualization; it is not a
physical 3D camera model.

### 7.3 Occupancy updates

For every sensor ray:

- cells before a detected endpoint become `FREE`;
- a true hit endpoint becomes `OCCUPIED`;
- no-hit endpoints remain free; and
- an existing occupied cell is never overwritten as free.

The number of cells changing from unknown to known is returned as `newly_explored`.

## 8. Victim detection

The victim is placed in ground truth but hidden from the policy. A simulated noisy WiFi
confidence increases as the rover approaches.

Distance is Manhattan distance:

```text
d = |robot_row - victim_row| + |robot_col - victim_col|
```

Default detection range is 10 cells. Within that range, confidence is approximately:

```text
confidence = clip(1.0 - 0.018 × d + Normal(0, 0.015), 0.0, 0.99)
```

Outside that range, a small background confidence is produced. Detection becomes a
confirmed victim only when confidence reaches `0.85` and the packet is fresh.

Before confirmation:

- the victim cell remains hidden in perception view;
- exact victim coordinates are unavailable to RL; and
- exploration continues normally.

After confirmation, `VictimConfirmation` publishes the victim as the navigation target.

## 9. Behavior Tree

The Behavior Tree is a `py_trees` priority selector evaluated from top to bottom every
decision tick:

```text
DrishyaBrain (Selector, no memory)
├── 1. SafetyGate
├── 2. EmergencyStop
├── 3. VictimConfirmation
├── 4. NavigateToTarget
├── 5. RLExplore
└── 6. Idle
```

In a selector:

- `SUCCESS` means the node handled this tick, so lower-priority nodes are not run;
- `RUNNING` means the active behavior continues and lower nodes are not run; and
- `FAILURE` means “not applicable,” so the selector tries the next node.

### 9.1 SafetyGate

SafetyGate stops the rover when:

- mission control is missing or invalid;
- the mission is paused, idle, stopped, or not in `run` mode;
- the operator emergency flag is set;
- pose, map, target, or proximity values are malformed;
- pose or proximity timestamps are stale; or
- every proximity reading is unavailable.

When state is valid, it returns `FAILURE` intentionally so the next branch may run. The
dashboard therefore labels an inactive SafetyGate as `CLEAR`.

### 9.2 EmergencyStop

EmergencyStop checks the sensor aligned with the next planned move. Its danger threshold
is 15 cm. It avoids deadlocking the rover because side obstacles do not block a planned
turn, and a rear movement relies on A*'s already known-free cell.

If the relevant measured obstacle is closer than 15 cm, it publishes a zero-speed
command and takes control of the selector.

### 9.3 VictimConfirmation

This branch validates confidence, coordinates, and freshness. At confidence `≥ 0.85`,
it converts world coordinates into a victim grid waypoint and publishes that target.
The same detection packet is not confirmed repeatedly.

### 9.4 NavigateToTarget

If a target and planned path exist, this branch publishes a motor intention for the
next path cell and returns `RUNNING`. The integrated simulator does not apply that motor
command as continuous physics; it executes exactly one validated grid cell from
`navigation/planned_path`.

### 9.5 RLExplore

When there is no victim target or current waypoint, this branch proposes an exploration
direction. With no trained model it uses a deterministic heuristic. The integrated
controller converts the proposal into a reachable frontier and then invokes A*.

The node name remains `RLExplore` because it is the integration point for a future PPO
policy. The presentation correctly displays `HEURISTIC FALLBACK` when PPO is absent.

### 9.6 Idle

Idle is the final fallback. It publishes a stop command when there is no actionable
mission behavior, such as after the map is fully explored.

## 10. One complete controller tick

The controller's authoritative `step()` performs these operations in order:

1. publish active mission control;
2. advance optional moving obstacles;
3. raycast sensors against private ground truth;
4. update the perceived occupancy grid;
5. calculate and publish victim confidence;
6. plan or refresh a route for an existing target;
7. tick the Behavior Tree once;
8. convert an exploration proposal into a frontier target when needed;
9. execute one validated path cell if navigation is active;
10. update coverage, steps, detections, collisions, and traces;
11. evaluate rescue and safe termination conditions; and
12. publish the rescue signal and final metrics when successful.

There is deliberately a one-tick separation between selecting a new target and moving:
one tick chooses/plans; the following navigation tick executes the next cell.

The logical decision rate is 10 Hz. Pygame renders at up to 60 FPS and interpolates
between the old and new visual poses. Changing visual speed does not change the order
or determinism of logical decisions.

## 11. Exploration and frontier selection

A frontier is a known-free cell adjacent to at least one unknown cell. The rover can
reach it without entering unknown space.

Frontier selection works as follows:

1. breadth-first search finds all frontiers reachable through known-free cells;
2. each frontier receives a reachable distance;
3. information gain counts unknown cells within radius 2;
4. a requested direction sector is preferred if it has candidates;
5. the nearest candidate wins;
6. higher information gain breaks equal-distance ties; and
7. row/column order provides deterministic final tie-breaking.

The four absolute sectors are east, north, west, and south. PPO or the heuristic only
expresses a preference. It never directly authorizes deployment movement.

## 12. A* planning

A* runs on the **perceived** occupancy grid, not ground truth. It uses:

```text
g(n) = cells travelled from the robot
h(n) = |row - goal_row| + |col - goal_col|
f(n) = g(n) + h(n)
```

Manhattan distance is admissible and consistent because movement is four-connected and
every cell transition costs 1. Heap entries use `(f, h, g, row, col)`, providing
deterministic, goal-directed tie-breaking. The traversal rules are:

- four-connected neighbors only;
- each step costs 1;
- only `FREE` cells are traversable;
- `UNKNOWN` and `OCCUPIED` cells are blocked;
- deterministic neighbor order is north, west, east, south; and
- the returned path excludes the current cell.

Possible statuses include:

| Status | Meaning |
|---|---|
| `ok` | A path was found |
| `arrived` | Start already equals goal |
| `blocked_goal_or_start` | Start or goal is not known free |
| `unreachable` | No known-free route exists |
| `out_of_bounds` | Start or goal is outside the map |

An unobserved or blocked victim goal is approached through a reachable neighboring cell
or a frontier that reduces remaining Manhattan distance.

The controller refreshes plans when robot/map/goal state changes, a target becomes
invalid, or the path is blocked. Therefore the `replans` metric counts planner
invocations and route validation—not collisions or failures. The curated run's high
replan count shows continuous replanning as perception changes; its collision count is
still zero.

Before every deployment move, the next cell is validated against ground truth. If it is
not a valid adjacent free cell, movement is refused, the path is cleared, and replanning
is forced.

## 13. Dynamic obstacles

Two mechanisms are available outside the simplified presentation controls:

- press `O`, then click a cell to add/remove a wall;
- press `D` to add or pause an autonomous moving hazard.

Boundary, robot, and victim cells are protected. A moving hazard is accepted only if
the ground-truth victim remains reachable. When a hazard changes:

- ground truth is updated;
- the perceived map receives the simulated event;
- an affected exploration target is cleared;
- the current path is invalidated when necessary; and
- A* checks the route before robot motion.

These features demonstrate online replanning. They are advanced presentation tools and
are disabled by default in the curated midterm run.

## 14. Blackboard and data contracts

The Blackboard is a lock-protected shared dictionary. `update_many()` atomically
publishes related values, and `snapshot()` returns a consistent deep copy.

Important keys are:

| Blackboard key | Producer | Main contents |
|---|---|---|
| `mission/control` | Controller/operator | mode, emergency flag, timestamp |
| `navigation/robot_pose` | Controller | world x/y, heading, timestamp |
| `navigation/occupancy_grid` | Mapping | perceived 50×50 grid only |
| `navigation/target_waypoint` | BT/controller | exploration or victim `(row, col)` |
| `navigation/planned_path` | A* planner | ordered remaining cells |
| `navigation/path_status` | Planner | goal, effective goal, status, cost, reason |
| `sensor/proximity` | Sensors | five distances, hits, rays, ToF data, range, timestamp |
| `detection/result` | Victim detector | human x/y, confidence, timestamp |
| `state/motor_command` | BT | bounded left/right speed and duration |
| `decision/state` | BT | mission and active behavior summary |
| `decision/trace` | BT | tick, action, reason, source, status, command, timestamp |
| `simulation/map_edit` | Simulator | latest manual/moving obstacle event |
| `simulation/metrics` | Controller | current episode measurements |
| `simulation/rescue_signal` | Controller | confirmed transmitted victim location |

Motor commands are sanitized to speed range `[-255, 255]` and duration range
`[0, 1000]` ms. In this discrete simulation they explain the intended physical action;
the controller's grid-cell validator remains authoritative.

## 15. Rescue signal

When confirmed victim distance is within one cell, the controller:

1. marks the episode successful;
2. keeps the compatible termination reason `victim_rescued`;
3. publishes `simulation/rescue_signal` exactly once; and
4. displays `VICTIM LOCATED — SIGNAL TRANSMITTED`.

Example payload:

```python
{
    "sent": True,
    "victim_cell": (10, 42),
    "victim_world": {"x": 170, "y": 150},
    "confidence": 0.86,
    "coverage_pct": 68.64,
    "timestamp_ms": 1780000000000,
}
```

The exact values depend on seed and run. This packet represents software-level
transmission to a future rescue coordination system.

## 16. Termination conditions

An episode can finish with:

| Reason | Meaning |
|---|---|
| `victim_rescued` | Confirmed victim reached; location signal transmitted |
| `victim_unreachable` | Every perceived safe approach to the victim is occupied |
| `map_fully_explored` | No unknown cells or actionable target remain |
| `step_limit` | Maximum logical steps reached |

Default maximum length is 750 steps. Safe failures do not cause the rover to enter an
occupied or out-of-bounds cell.

## 17. Metrics

| Metric | Interpretation |
|---|---|
| `steps` | Logical controller ticks |
| `explored_cells` | Non-unknown occupancy cells |
| `coverage_pct` | Explored cells divided by 2500 |
| `replans` | A* planner invocations/refreshes |
| `collisions` | Refused invalid deployment moves or RL training wall attempts |
| `unsafe_proximity_count` | Recorded unsafe proximity events |
| `dynamic_obstacle_changes` | Accepted manual edits |
| `moving_obstacle_moves` | Autonomous hazard moves |
| `victim_detections` | Ticks with confirmed victim confidence |
| `rescued` | Compatibility success flag |
| `signal_transmitted` | Rescue-location packet was published |
| `termination_reason` | Final or current episode state |
| `policy_source` | heuristic, PPO, external policy, or PPO training |
| `elapsed_seconds` | Real execution time, not simulated mission time |

## 18. Reinforcement-learning design

RL is implemented as a training-ready integration, but the midterm presentation does
not claim that a trained model is currently being used.

### 18.1 Observation: `house-rescue-v2`

The observation contains exactly 2,517 values:

| Component | Values |
|---|---:|
| Flattened perceived occupancy grid | 2500 |
| Normalized row, column, heading | 3 |
| Five normalized proximity readings | 5 |
| Coverage | 1 |
| Four normalized frontier-sector counts | 4 |
| Detection confidence | 1 |
| Masked victim-relative row and column | 2 |
| Previous collision flag | 1 |
| **Total** | **2517** |

Occupancy values are divided by 2, so free=`0.0`, occupied=`0.5`, and unknown=`1.0`.
Victim-relative values are exactly zero until confirmation, preventing coordinate leak.

### 18.2 Actions

There are four relative actions:

```text
0 forward
1 left
2 backward
3 right
```

### 18.3 Training versus deployment

This distinction is essential:

| Mode | What an RL action does |
|---|---|
| Training | Attempts an adjacent cell directly; wall attempts are recorded and penalized |
| Deployment | Expresses an exploration-sector preference; BT, validation, and A* execute safely |

Permitting collision attempts during training gives PPO a learning signal. Deployment
does not deliberately reproduce those collisions.

### 18.4 Reward function

```text
+0.05 × newly observed cells
+25    first confirmed victim detection
+0.5   per cell of progress toward a confirmed victim
+100   successful victim reach
-0.02  every step
-0.1   step with no newly observed area
-8     collision attempt
-0.5 × additional repeated-collision streak
-10    timeout
```

### 18.5 Curriculum

The optional PPO curriculum trains one model sequentially through all six houses, then
fine-tunes it on a deterministic mixed-house rotation.

```text
quick: 5,000 steps per house + 10,000 mixed
full:  50,000 steps per house + 100,000 mixed
```

Checkpoints use the 2,517-value schema. Older incompatible observations are rejected,
and deployment falls back safely to deterministic frontier exploration.

The midterm `L` overlay reports one of:

- `NOT TRAINED — DETERMINISTIC FRONTIER HEURISTIC ACTIVE`;
- `TRAINED PPO LOADED`; or
- `CHECKPOINT REJECTED — SAFE HEURISTIC FALLBACK`.

No improvement percentage is fabricated without actual training/evaluation results.

## 19. Visual interface

### Main map

- gray: unknown;
- light: known free;
- dark: known obstacle;
- cyan/purple: ultrasonic and ToF rays;
- yellow: A* path;
- green marker: current target;
- blue dots: visited trail;
- red figure: confirmed victim;
- orange: optional moving hazard; and
- expanding green rings: transmitted rescue signal.

### Behavior Tree panel

All six real priority branches remain visible. The active branch is highlighted. Safety
branches display `CLEAR` when their stop condition is not active. Without a model, the
exploration branch explicitly displays `HEURISTIC FALLBACK` while active.

### Presentation controls

| Key | Action |
|---|---|
| `Enter` | Start from an overlay and resume |
| `Space` | Pause/run |
| `N` | One logical step |
| `R` | Reset the same scenario and seed |
| `G` | Perception/Ground Truth |
| `H` | Presentation guide |
| `L` | RL readiness glimpse |
| `Esc` | Exit |

Advanced keyboard controls remain available:

| Key | Action |
|---|---|
| `S` | Toggle sensor rays |
| `P` | Toggle path/target |
| `O` | Toggle map editing; click a cell |
| `D` | Add/pause a moving hazard |
| `+` / `-` | Change visual speed |

Presentation overlays and visualization toggles never alter robot logic, hidden state,
or RL observations.

## 20. Commands

### Curated midterm

```bash
.drishya/bin/python -m simulation_brain --presentation
```

### Explicit visual scenario

```bash
.drishya/bin/python -m simulation_brain \
  --mode visual --scenario clinic-ward --seed 7 --speed 1.0
```

### Deterministic headless result

```bash
.drishya/bin/python -m simulation_brain \
  --mode headless --scenario two-bedroom-house --seed 4 --episodes 1
```

### Optional moving hazards

```bash
.drishya/bin/python -m simulation_brain \
  --mode visual --scenario warehouse --seed 7 \
  --moving-obstacles 2 --obstacle-interval 8
```

### Optional PPO curriculum

```bash
.drishya/bin/python -m simulation_brain.rl.train_ppo \
  --preset quick --seed 7 --dashboard
```

### Evaluation

```bash
.drishya/bin/python -m simulation_brain.rl.evaluate \
  --model simulation_brain/models/house_rescue_final.zip \
  --suite houses --episodes-per-scenario 20
```

### Tests

```bash
.drishya/bin/python -m pytest -q
```

## 21. How to explain the project in a defense

A concise technical explanation is:

> The ground-truth house is private. The rover starts with an unknown occupancy grid.
> Simulated range sensors reveal only nearby cells. A safety-first Behavior Tree checks
> mission validity and collision risk before selecting victim navigation or exploration.
> Exploration chooses a reachable frontier, while A* plans only through known-free
> cells. A noisy WiFi confidence confirms the hidden victim. After the rover reaches the
> confirmed location, it publishes a rescue-signal packet. RL is training-ready but not
> claimed as trained; without a checkpoint, deterministic exploration is used, and
> deployment safety remains outside the policy.

During the presentation:

1. explain the boundary on the intro screen;
2. press `Enter` and show unknown cells becoming mapped;
3. pause and press `N` to explain one complete controller tick;
4. point to the active BT branch and A* path;
5. press `G` briefly to contrast perception with ground truth;
6. press `L` and explain the honest RL-ready boundary;
7. resume; and
8. finish with coverage, zero collisions, and the transmitted location signal.

## 22. What is simulated and what is future work

### Implemented in software

- deterministic building environments;
- hidden ground truth and victim placement;
- ultrasonic and simplified ToF raycasting;
- occupancy mapping;
- Behavior Tree decisions;
- A* and frontier planning;
- victim confidence and confirmation;
- validated movement and dynamic replanning;
- rescue-signal contract;
- presentation dashboard;
- Gymnasium environment and PPO tooling;
- metrics, reports, replay, and automated tests.

### Not yet a real-world implementation

- physical chassis and motor control;
- real ultrasonic/ToF drivers and calibration;
- real WiFi localization accuracy;
- SLAM localization drift and correction;
- wheel slip, acceleration, and continuous collision geometry;
- batteries, radio range, packet loss, or network failure;
- fire, smoke, heat, water, chemical, or structural hazard physics;
- physical victim interaction or transport;
- hardware-in-the-loop validation;
- multi-robot coordination and field trials.

The simulation should therefore be presented as a validated software architecture and
research platform, not as proof of completed hardware performance.

## 23. Common questions and answers

### Why use a Behavior Tree instead of only RL?

Safety and mission priorities need deterministic authority. A learned policy may suggest
exploration, but it must not bypass emergency stopping, map validation, or path safety.

### Why use A*?

The grid has uniform movement cost, and Manhattan distance safely guides A* toward the
goal without sacrificing shortest-path optimality. Compared with an uninformed
uniform-cost search, A* normally avoids expanding as many irrelevant cells while preserving clear,
deterministic unreachable/error states.

### Why are unknown cells blocked?

Allowing the planner to treat unknown space as free would create unsafe shortcuts
through walls the rover has not observed.

### Why is coverage not 100% when the victim is found?

The rescue objective has higher priority than unnecessary exploration. Once the victim
is confirmed and safely reached, delaying assistance only to increase coverage would be
the wrong mission behavior.

### Why are there many replans but no collisions?

Replans count planner refreshes as the robot pose and perceived map change. They show
continuous route validation; they do not mean the rover hit something.

### Is PPO currently controlling the midterm demonstration?

No. Unless a compatible checkpoint is explicitly supplied, the dashboard says
`NOT TRAINED` and uses deterministic frontier exploration. This is intentional and
academically honest.

### Can the policy see the hidden victim?

No. Ground truth is excluded. Victim-relative observation fields stay zero until WiFi
confirmation.

### Does “rescued” mean physical evacuation?

No. The compatibility metric is retained, but the presentation says the victim was
located and their coordinates were transmitted. Physical evacuation is future work.

## 24. Source map

The main implementation areas are:

| Area | Location |
|---|---|
| Controller/runtime tick | `simulation_brain/controller.py` |
| Scenarios | `simulation_brain/scenarios.py` |
| Sensors/mapping | `simulation_brain/sensors.py` |
| A*/frontiers | `simulation_brain/planning.py` |
| Visual presentation | `simulation_brain/renderer.py`, `visual_state.py` |
| RL observation/environment | `simulation_brain/rl/features.py`, `rl/environment.py` |
| PPO curriculum/evaluation | `simulation_brain/rl/train_ppo.py`, `rl/evaluate.py` |
| Behavior Tree | `modules/decision_logic/behavior_tree/` |
| Blackboard contracts | `modules/decision_logic/contracts.py` |
| Shared coordinates | `shared/coordinate_system.py` |
| Tests | `simulation_brain/tests/`, `modules/decision_logic/tests/` |
