## Official Coordinate Convention
# Origin: (0, 0), robot's physical starting position
# Initial robot position: (0, 0)
# Initial robot heading: 0°
# +X: forward
# +Y: left
# -X: backward
# -Y: right

# 1 grid unit = 10 cm
# Grid size = 50 × 50 cells
# Physical area = 5 m × 5 m

# The robot's physical starting point (0,0) is placed in the middle of the 50×50 map, rather than at the corner.

GRID_WIDTH = 50
GRID_HEIGHT = 50

GRID_CENTER_X = 25
GRID_CENTER_Y = 25

CELL_SIZE_CM = 10

FREE = 0
OCCUPIED = 1
UNKNOWN = 2

INITIAL_X = 0.0
INITIAL_Y = 0.0
INITIAL_HEADING = 0.0

def world_to_grid(x, y):
    """Convert physical position (cm) to grid cell (row, col)."""
    col = round(x / CELL_SIZE_CM) + GRID_CENTER_X
    row = round(-y / CELL_SIZE_CM) + GRID_CENTER_Y
    return row, col

def grid_to_world(row, column):
    """Convert grid cell (row, col) to physical position (cm), cell center."""
    x = (column - GRID_CENTER_X) * CELL_SIZE_CM
    y = -(row - GRID_CENTER_Y) * CELL_SIZE_CM
    return x, y  
