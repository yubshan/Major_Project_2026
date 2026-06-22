import math

SCREEN_WIDTH = 800
SCREEN_HEIGH = 800
PPM = 60

# config.py
GRID_CELL_SIZE = 0.1   
GRID_WIDTH     = 80    
GRID_HEIGHT    = 80    

ROBOT_CONFIG = {
    "robot_dimension": {
        "width": 0.5,
        "height": 0.5
    },
    "robot_chasis": {
        "width": 0.3,
        "height": 0.35
    },
    "robot_wheel": {
        "width": 0.06,
        "height": 0.14
    }
}

ROBOT_MAX_SPEED = 1.5
ROBOT_MAX_TURNING_SPEED = 1.2

RAY_RANGE = 4  # meters
FOV = 15 * (math.pi / 180)
RES = 4
NUM_RAYS = SCREEN_WIDTH // RES
ULTRASONIC_NUM_RAYS = 9
CRITICAL_DISTANCE = 0.7
WARNING_ZONE = 1.5

SENSOR_CONFIGS = [
    {"name": "FRONT",        "offset_angle":   0, "firing_round": 2},
    {"name": "FRONT_LEFT",   "offset_angle":  45, "firing_round": 1},
    {"name": "FRONT_RIGHT",  "offset_angle": -45, "firing_round": 1},
    {"name": "LEFT",         "offset_angle":  90, "firing_round": 0},
    {"name": "RIGHT",        "offset_angle": -90, "firing_round": 0},
    {"name": "REAR",         "offset_angle": 180, "firing_round": 3},
]

NUM_FIRING_ROUNDS = 4

FRAMES_PER_ROUND = 4