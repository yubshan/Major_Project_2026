import math

SCREEN_WIDTH = 800
SCREEN_HEIGH = 800
PPM = 100

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

ROBOT_MAX_SPEED = 0.7
ROBOT_MAX_TURNING_SPEED = 1.2

RAY_RANGE = 4  # meters
FOV = 15 * (math.pi / 180)
ULTRASONIC_NUM_RAYS = 9
CRITICAL_DISTANCE = 0.7
WARNING_ZONE = 1.5

SENSOR_CONFIGS = [
    {"name": "FRONT",        "offset_angle":   0, "firing_round": 2},
    {"name": "FRONT_LEFT",   "offset_angle":  45, "firing_round": 1},
    {"name": "FRONT_RIGHT",  "offset_angle": -45, "firing_round": 1},
    {"name": "LEFT",         "offset_angle":  90, "firing_round": 0},
    {"name": "RIGHT",        "offset_angle": -90, "firing_round": 0},
]

NUM_FIRING_ROUNDS = 4

FRAMES_PER_ROUND = 8

TOF_ROWS = 8
TOF_COLS = 8
TOF_FOV = 61.0 * math.pi /180    #Raidian
TOF_MAX_RANGE = 4.0              #Meter
TOF_RENDER_OVERLAY = True
 

 
