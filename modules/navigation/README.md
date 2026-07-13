# Navigation & Environmental Mapping Module

**Owner:** Anusha Shrestha (Navigation & Mapping / Teammate A)
<br />
**Project:** Drishya — autonomous rescue robot for search-and-exploration missions

This module gives the robot spatial awareness. It reads sensor data (simulated or real), maintains a real-time occupancy grid of the environment, and calculates the safest path to any target position. It writes the grid, path, and robot position to the shared blackboard for Decision Logic and Simulation & Visualization to use.

This module also defines the shared system contracts (`coordinate_system.py`, `sensor_format.py`, `blackboard.py`) used by the whole team.

---

# Role in the System

```text
Simulation / ESP32 ──sensor packet──►  Navigation Module  ──writes──► shared/blackboard
                                              │                              │
                                        occupancy grid                      ▼
                                        robot position          Decision Logic / Dashboard
                                        planned path
```

Navigation sits between raw sensing and decision-making: it consumes sensor packets and a target position, and publishes the occupancy grid, robot pose, and planned path for the rest of the system to act on.

---

# Responsibilities

This module is responsible for:

* Parsing incoming sensor packets (ultrasonic + ToF) into map coordinates.
* Maintaining and updating the occupancy grid every sensor cycle (~10 Hz).
* Running A* pathfinding toward a target position when one is set.
* Running frontier exploration when no target is set.
* Publishing robot position, occupancy grid, and planned path to the blackboard.
* Defining and maintaining the shared coordinate system, sensor format, and blackboard.
* Implementing the ESP32 sensor-reading firmware.

Out of scope for this module: Pygame rendering, the ground truth map, sensor simulation, behavior tree/decision logic, motor commands, and the ESP32 motor firmware — all owned by other teammates.

---

# Expected Structure

```text
navigation/
├── README.md
├── occupancy_grid.py     # OccupancyGrid class
├── a_star.py             # Custom pathfinding implementation
├── exploration.py        # Frontier search algorithm
└── navigator.py          # Runtime loop @ 10 Hz

shared/
├── blackboard.py
├── coordinate_system.py
├── sensor_format.py
├── bresenham.py
└── mock_sensors.py
```

---

# Blackboard Contract

## Reads

| Source | Data |
|---|---|
| Simulation (Weeks 1–18) or ESP32 (Week 19+) | Sensor JSON packet — see `shared/sensor_format.py` |
| Decision Logic | `navigation/target_position` — `(int, int)` or `None` |

## Writes

| Consumer | Data |
|---|---|
| Decision Logic, Dashboard | `navigation/occupancy_grid` — `numpy.ndarray (50,50)`, `0=FREE`, `1=OCCUPIED`, `2=UNKNOWN` |
| Decision Logic, Dashboard | `navigation/robot_position` — `(grid_x, grid_y, heading_degrees)` |
| Decision Logic, Dashboard | `navigation/planned_path` — `List[(int, int)]`, empty if no path |

Coordinate system: origin at robot's starting position, X forward, Y left, 1 grid unit = 10 cm, grid is 50×50 (5m × 5m).

---

# Runtime Flow

1. Read the latest sensor JSON packet (simulation or ESP32).
2. Convert readings to map coordinates via Bresenham ray casting.
3. Update the occupancy grid.
4. Read `navigation/target_position` from the blackboard.
5. Run A* toward the target, or frontier exploration if no target is set.
6. Write grid, robot position, and planned path back to the blackboard.
7. Repeat at ~10 Hz.

---

# Developing Before Other Modules Are Ready

Use `shared/mock_sensors.py` — `get_mock_sensor_packet(scenario)`, with scenarios like `open_front`, `obstacle_ahead`, `narrow_corridor`, `left_blocked`, `right_blocked`, `all_blocked`.

This allows the occupancy grid and A* to be built and unit-tested without the simulator or hardware. It's also shared with Decision Logic for testing `AvoidObstacle`/`EscapeDanger` behaviors. Testing uses ASCII grid printouts (`.` FREE, `#` OCCUPIED, `?` UNKNOWN) — no display needed.

Integration timeline: mock data  → simulation replaces mock  → real ESP32 replaces simulation, with only the sensor data source changing each time.

---

# ESP32 Sensor Firmware

This module owns the sensor-reading portion of the ESP32 firmware (motor firmware is owned separately and combined before flashing).

* HC-SR04 ultrasonic ×5: GPIO 4/5, 18/19, 13/14, 23/25, 26/27
* VL53L5CX ToF: SDA=GPIO21, SCL=GPIO22, I2C @ 400kHz
* Sequential firing of all sensors + ToF read, then send JSON — cycle ~70ms (~10 Hz)

---

# Planned Dependencies

This module primarily depends on:

* NumPy
* pyserial (for ESP32 serial reads)

No external pathfinding or ray-casting libraries — A* and Bresenham are custom implementations.

---

# Development Checklist

* Define `shared/coordinate_system.py`, `shared/sensor_format.py`, `shared/blackboard.py`
* Implement `OccupancyGrid` class
* Implement Bresenham ray casting
* Implement A* pathfinding
* Implement frontier exploration
* Implement `navigator.py` runtime loop
* Build and share `shared/mock_sensors.py`
* Add unit tests / ASCII grid testing
* Write ESP32 sensor firmware
* Update this README as the module evolves