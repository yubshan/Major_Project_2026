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