# Project Drisya

## Overview

Project Drisya is a Search and Rescue (SAR) autonomous robot being developed to help locate people trapped under collapsed buildings during disasters such as earthquakes. The main idea behind this project is to detect human presence even when the person cannot be seen directly because of walls, concrete, or heavy rubble.

Most rescue systems depend on cameras or infrared (IR) sensors. These sensors work well when the victim is visible, but they cannot detect people hidden behind thick obstacles. Project Drisya tries to solve this problem by using **WiFi Channel State Information (CSI)**. Since WiFi signals can pass through many building materials, the changes in these signals caused by a human body can be analyzed to estimate the presence and location of a trapped person.

The project is first developed completely in simulation before being deployed on real hardware. This allows us to test the algorithms safely, improve the system, and reduce hardware related problems during development.

---

# Problem Statement

In search and rescue operations, especially after earthquakes or building collapses, finding survivors as quickly as possible is extremely important. Rescue teams often refer to the first few hours after a disaster as the **Golden Hour**, where the chances of survival are highest.

Current rescue tools have several limitations:

- Cameras require a direct line of sight.
- Infrared (IR) sensors cannot detect people behind concrete walls or thick rubble.
- Manual searching takes time and increases the risk for rescue workers.

Our solution is to use **WiFi Channel State Information (CSI)** to detect human presence through obstacles. WiFi signals naturally pass through many construction materials. When a person is inside the signal path, their body changes the radio signal by creating reflections, attenuation, and phase changes. By processing these signal changes using machine learning, the system can estimate where a person is located without needing direct visual contact.

---

# Project Roadmap

The project is divided into two major phases.

## Phase 1 – Software and Simulation

The first phase focuses entirely on software development. Everything is built and tested inside a custom simulation environment before any hardware is connected.

The work includes:

- Building a custom 2D simulator using Pygame
- Developing occupancy grid mapping
- Implementing WiFi CSI based human detection
- Creating navigation algorithms
- Developing decision making using Behavior Trees and Reinforcement Learning
- Testing all modules independently

The objective of this phase is to make sure every software component works correctly before moving to real hardware.

---

## Phase 2 – Hardware Integration

After the software has been tested in simulation, it is integrated with the physical robot.

The hardware includes:

- ESP32
- Raspberry Pi
- Ultrasonic Sensors
- Time-of-Flight (ToF) Sensor
- WiFi Modules
- Motor Drivers
- DC Motors

Instead of simulated sensor data, the software now reads real sensor values and controls the robot's movement.

---

# System Architecture

To make development easier for multiple team members, the project is divided into independent modules. Every module performs its own task and communicates only through a shared memory system called the **Blackboard**.

```
                          BLACKBOARD
              (Shared Thread-Safe Memory System)

                     ▲          ▲          ▲
                     │          │          │

        +------------+----------+----------+------------+
        |                       |                       |
        |                       |                       |
+---------------+     +------------------+     +----------------+
| WiFi Detection|     | Navigation & Map |     | Decision Logic |
+---------------+     +------------------+     +----------------+
         ▲                     ▲                      ▲
         |                     |                      |
         +---------------------+----------------------+
                               |
                    +--------------------------+
                    | Simulation & Dashboard   |
                    +--------------------------+
```

Each module runs independently and continuously updates or reads information from the Blackboard. This makes it possible for different team members to work on different modules without affecting each other's code.

---

# Shared Coordinate System

To make sure every module understands the robot's location in the same way, the project uses a common coordinate system.

- Origin `(0, 0)` is the robot's starting position.
- The robot initially faces the positive X direction.
- Positive X points forward from the robot.
- Positive Y points to the robot's left side.
- Initial robot heading is `0°`.
- One grid cell represents **10 cm**.
- The simulation map contains **50 × 50 cells**, representing an area of **5 m × 5 m**.
- The physical origin `(0, 0)` corresponds to grid cell `(25, 25)`.
- X coordinates correspond to grid columns.
- Y coordinates correspond to grid rows.


Every module follows this coordinate system when sharing position information.

---

# Project Modules

## Module 1 – WiFi Human Detection

This module is responsible for detecting where a human is located using WiFi signals.

### Input

- Raw WiFi CSI data
- RSSI values
- Amplitude values
- Phase values

### Processing

The collected CSI data is processed using a Convolutional Neural Network (CNN) developed in PyTorch. The model learns to distinguish normal environmental noise from signal patterns caused by a human body.

Once a person is detected, triangulation techniques are used to estimate the person's relative position.

### Blackboard Output

```python
"detection/result": {
    "human_x": float,
    "human_y": float,
    "confidence": float,
    "timestamp": int
}
```

---

## Module 2 – Navigation and Environmental Mapping

This module creates a map of the environment and finds a safe path for the robot.

### Input

Simulation

- Virtual ultrasonic sensor readings
- Virtual ToF sensor data

Hardware

- 5 Ultrasonic Sensors
- 8×8 Time-of-Flight Sensor

### Processing

The sensor readings are converted into map coordinates using Bresenham's ray casting algorithm. The environment is stored as an Occupancy Grid where each cell is classified as:

- Unknown
- Free
- Occupied

Whenever a target location is available, an A* pathfinding algorithm calculates the safest route.

### Blackboard Output

- Occupancy Grid
- Planned Path
- Robot Position

---

## Module 3 – Decision Logic

This module acts as the brain of the robot.

It combines information from all other modules and decides what action the robot should perform next.

### Input

- Human location
- Robot position
- Occupancy Grid
- Planned path

### Processing

The module continuously evaluates a Behavior Tree (BT).

If no human has been detected yet, a PPO Reinforcement Learning policy is used to explore the environment efficiently.

If obstacles are detected, the Behavior Tree immediately changes the robot's behavior to avoid collisions.

### Blackboard Output

```python
"state/motor_command": {
    "left_speed": int,
    "right_speed": int,
    "duration_ms": int
}
```

---

## Module 4 – Simulation and Dashboard

This module provides the testing environment before the robot is deployed on hardware.

The simulator generates virtual sensor readings from a hidden Ground Truth Map and sends them to the navigation module exactly like real hardware would.

A real-time dashboard displays all important information while the simulation is running.

The dashboard contains four panels.

### Panel 1 – Ground Truth

Shows the actual map, hidden obstacles, victim locations, and robot position.

### Panel 2 – Robot Perception

Displays the Occupancy Grid, planned path, and detected human position.

### Panel 3 – Sensor Data

Displays ultrasonic sensor rays and the 8×8 ToF depth grid.

### Panel 4 – Decision Log

Shows the current Behavior Tree execution and important system events in real time.

---

# Repository Structure

```text

## 📂 Repository Architecture

```text
project-drishya/
├── .gitignore
├── README.md                 # Project landing page & documentation
├── requirements.txt          # Universal Python dependencies (PyTorch, py_trees, etc.)
│
├── shared/                   # THE SYSTEM CONTRACTS (Strict API layer, changes require team sync)
│   ├── __init__.py
│   ├── blackboard.py         # Thread-safe dict implementation (Teammate A)
│   ├── coordinate_system.py  # Core spatial constants: origin, 1 unit = 10cm (Teammate A)
│   ├── sensor_format.py      # Shared JSON packet definitions (Teammate A)
│   ├── sensor_queue.py       # Thread-safe queue for simulated sensor data (Teammate C)
│   ├── bresenham.py          # Shared ray-casting algorithm (Teammate A/C)
│   ├── mock_detection.py     # Yubshan's mock data generator for Teammate B
│   ├── mock_navigation.py    # Teammate B's mock data generator
│   └── mock_sensors.py       # Teammate A's mock data generator
│
├── modules/                  # INDEPENDENT DEVELOPER SANDBOXES
│   ├── wifi_detection/       # Yubshan's Workspace (WiFi Detection Lead)
│   │   ├── data_collection/  # Raw CSI capture scripts
│   │   ├── models/           # CNN architecture & local PyTorch training scripts
│   │   ├── triangulation.py  # Triangulation & SLAM logic
│   │   └── detector.py       # Independent loop updating blackboard key
│   │
│   ├── navigation/           # Teammate A's Workspace (Navigation & Mapping)
│   │   ├── occupancy_grid.py # Map maintenance logic
│   │   ├── a_star.py         # Custom pathfinding implementation
│   │   ├── exploration.py    # Frontier search algorithm
│   │   └── navigator.py      # Independent loop updating mapping keys
│   │
│   ├── decision_logic/       # Teammate B's Workspace (Decision Logic / BT + RL)
│   │   ├── behavior_tree/    # Individual py_trees Behavior sub-classes
│   │   ├── rl_env/           # Custom SARExploreEnv Gymnasium environment
│   │   ├── train_ppo.py      # Stable-Baselines3 training scripts
│   │   └── brain.py          # Core loop ticking the BT @ 10Hz
│   │
│   └── simulation_viz/       # Teammate C's Workspace (Simulation & Visualization)
│       ├── map_editor.py     # Ground truth map maker (.npy files)
│       ├── maps/             # Saved map layouts
│       ├── sensor_sim.py     # Math for calculating fake ultrasonic/ToF grids
│       ├── dashboard.py      # The 4-panel Pygame interface
│       └── simulator.py      # Core visualization and hardware link loop
│
├── firmware/                 # MICROCONTROLLER EMBEDDED LAYER
│   ├── platformio.ini        # PlatformIO unified config
│   └── src/
│       ├── main.cpp          # Combined ESP32 entry point
│       ├── sensors.h/.cpp    # Teammate A's sensor reading code
│       └── motors.h/.cpp     # Teammate C's motor driving code
│
└── main.py                   # System Orchestrator (Launches all module threads)
```

The repository is organized so that each team member can work independently on their assigned module. Communication between modules only happens through the shared Blackboard, making the system modular and easier to maintain.

---

# Technologies Used

- Python
- Pygame
- NumPy
- PyTorch
- OpenCV
- ESP32
- Raspberry Pi
- WiFi CSI
- Behavior Trees
- PPO Reinforcement Learning
- A* Path Planning

---

# Current Progress

- [ ] Build Simulation Environment
- [ ] Occupancy Grid Mapping
- [ ] WiFi CSI Data Collection
- [ ] CNN Training
- [ ] Human Localization
- [ ] Decision Logic
- [ ] Dashboard Visualization
- [ ] Hardware Integration

---

# Final Goal

The final goal of Project Drisya is to develop an autonomous search and rescue robot that can detect trapped humans using WiFi CSI, navigate safely through disaster environments, and assist rescue teams by reducing search time and improving the chances of locating survivors.