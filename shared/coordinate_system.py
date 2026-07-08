# Requirement / Purpose: A central configuration file holding hardcoded mathematical constants for your environment 
# (e.g., GRID_SIZE = 50, CELL_SCALE_CM = 10, ORIGIN = (0,0)).

# Why it is needed: Spatial alignment. If Yubshan thinks 1 grid unit means 1 meter, 
# Teammate A thinks it means 10cm, and Teammate C scales pixels differently in Pygame,
#  the robot's pathfinding will be completely broken. This file forces the entire team to use an identical 
# spatial language.

# Teammate Roles:

#     Teammate A: Defines the coordinates (Origin = robot start, positive X = forward, positive Y = left).

#     Yubshan, Teammate B, Teammate C: Import these constants. When calculating coordinates or rendering shapes, 
# they multiply or divide by these exact values to keep the math unified.