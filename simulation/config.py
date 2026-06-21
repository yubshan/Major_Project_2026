import math
SCREEN_WIDTH = 800
SCREEN_HEIGH = 800
PPM = 60

GRID_CELL_SIZE = 0.2
GRID_WIDTH = 40 
GRID_HEIGHT = 40


ROBOT_CONFIG = {
    "robot_dimension" : {
        "width": 1,
        "height": 1
    },
    "robot_chasis" :{
        "width": 0.6,
        "height": 0.7333
    },
    "robot_wheel" :{
        "width": 0.1667,
        "height": 0.55
    }
}
ROBOT_MAX_SPEED = 4
ROBOT_MAX_TURNING_SPEED = 3


RAY_RANGE = 4 # meter
FOV = 15 * (math.pi / 180)
RES = 4
NUM_RAYS = SCREEN_WIDTH // RES