# Simulation & Visualization Module

**Owner:** Ditish Acharya (Simulation & Visualization / Teammate C)
**Project:** Drishya — autonomous rescue robot for search-and-exploration missions

This module provides the virtual environment used to develop, test, and demonstrate the robot before deployment on physical hardware. It simulates the robot's operating environment, generates realistic sensor data, renders a **2.5D isometric visualization** using Pygame, and executes the simulation loop. It also implements the motor-control portion of the ESP32 firmware used during hardware integration.

Implementation has not started yet. This README defines the module responsibilities and integration contract so the Navigation, WiFi Detection, and Decision Logic modules can integrate without tight coupling.

---

# Role in the System

```text
                  Ground Truth Map
                         │
                         ▼
               Sensor Simulation Layer
                         │
                         ▼
           shared/sensor_queue.py
                         │
                         ▼
                   Navigation Module
                         ▲
                         │
                shared/blackboard.py
                         ▲
                         │
              Simulation & Visualization
                         │
                         ▼
             2.5D Isometric Dashboard
```

The Simulation & Visualization module acts as the virtual robot and testing environment. It generates sensor data from the simulated world, visualizes the robot's current state, and provides the data required by the Navigation module for software development before hardware deployment.

---

# Responsibilities

This module is responsible for:

* Designing and maintaining the Ground Truth Map.
* Simulating Ultrasonic distance sensors.
* Simulating the 8×8 ToF depth sensor.
* Building sensor JSON packets compatible with the real robot.
* Managing the simulation loop.
* Rendering a **2.5D isometric visualization** of the environment.
* Developing the four-panel Pygame dashboard.
* Reading robot state from the shared blackboard.
* Publishing simulated sensor packets through `shared/sensor_queue.py`.
* Implementing the ESP32 motor command receiver firmware.
* Supporting hardware integration and motor calibration.

---

# Expected Structure

```text
simulation/
├── README.md
├── requirements.txt
├── main.py
├── config.py
├── constants.py
├── .gitignore
│
├── assets/
│   ├── maps/
│   ├── robot/
│   ├── tiles/
│   ├── ui/
│   ├── victims/
│   └── walls/
│
├── simulation/
│   └── __init__.py
│
├── visualization/
│   ├── __init__.py
│   ├── isometric.py
│   └── renderer.py
│
└── tests/
```

Additional files and directories will be added as implementation progresses.

---

# Blackboard & Queue Contract

This module communicates with the rest of the project only through the shared interfaces.

## Reads

| Source         | Data                       |
| -------------- | -------------------------- |
| Navigation     | Robot position and heading |
| Decision Logic | Motor commands             |
| Navigation     | Occupancy grid             |
| Navigation     | Planned path               |
| WiFi Detection | Detection results          |
| Decision Logic | Current robot behavior     |

## Writes

| Consumer             | Data                          |
| -------------------- | ----------------------------- |
| Navigation           | Simulated sensor JSON packets |
| Simulation Dashboard | Updated visualization state   |

Sensor packets must follow the structure defined in `shared/sensor_format.py` and are published through `shared/sensor_queue.py`.

---

# Runtime Flow

The simulation loop executes continuously during runtime.

1. Read the latest motor command from the blackboard.
2. Update the robot position and heading.
3. Generate simulated Ultrasonic and ToF sensor readings.
4. Build a sensor JSON packet.
5. Push the packet into the shared sensor queue.
6. Update the 2.5D visualization dashboard.
7. Repeat until the simulation stops.

---

# Visualization Dashboard

The simulator displays a single Pygame window containing four panels.

### Panel 1 — Ground Truth

Displays the designed environment including:

* Obstacles
* Victim locations
* Robot position

### Panel 2 — Robot Perception

Displays:

* Occupancy Grid
* Planned Path
* Robot Marker
* Human Detection Marker

### Panel 3 — Live Sensors

Displays:

* Ultrasonic sensor rays
* Distance visualization
* 8×8 ToF depth heatmap

### Panel 4 — Decision Log

Displays:

* Current robot behavior
* Recent behavior tree actions
* Timestamped decision history

---

# Visualization Approach

The simulator renders the environment using a **2.5D isometric projection**. Although the world is internally represented as a 2D occupancy grid, the isometric view improves depth perception and provides a clearer representation of the robot, rubble, obstacles, and victims during testing and demonstrations.

---

# Developing Before Other Modules Are Ready

Simulation and visualization can be developed independently using mock data.

Useful shared utilities include:

* `shared/mock_navigation.py`
* `shared/mock_detection.py`
* `shared/mock_sensors.py`

These allow the simulator and dashboard to be tested without requiring the Navigation, Decision Logic, or WiFi Detection modules to be complete.

---

# ESP32 Motor Firmware

This module owns the motor-control portion of the ESP32 firmware.

Responsibilities include:

* Receiving motor commands over WiFi (UDP).
* Parsing incoming JSON commands.
* Controlling the L298N motor driver.
* Executing left and right motor movements.

Sensor acquisition firmware is implemented separately and integrated before hardware deployment.

---

# Planned Dependencies

The project uses the root `requirements.txt` for dependency management.

This module primarily depends on:

* Pygame
* NumPy
* threading
* queue.Queue

Additional libraries will be added as implementation progresses.

---

# Development Checklist

* Learn Pygame fundamentals.
* Design the Ground Truth Map.
* Implement the 2.5D isometric renderer.
* Develop Ultrasonic sensor simulation.
* Develop ToF sensor simulation.
* Generate sensor JSON packets.
* Integrate with `shared/sensor_queue.py`.
* Build the four-panel visualization dashboard.
* Implement ESP32 motor firmware.
* Complete integration testing with the Navigation module.
* Update this README as the module evolves.
