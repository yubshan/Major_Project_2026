# Requirement / Purpose: Houses the mathematical code for Bresenham’s Line Algorithm. Given a starting pixel/cell and
#  an ending pixel/cell, it outputs a list of all discrete cells in a straight line between them.

# Why it is needed: Ray-casting. When an ultrasonic sensor reports an obstacle 50cm away, the mapping engine needs to 
# know which grid cells are completely Free (the empty air the sensor ray shot through) and which specific cell is
#  Occupied (where the ray hit the wall).

# Teammate Roles:

#     Teammate A: Writes the mathematical implementation of this algorithm.

#     Teammate C: Imports this exact file into the simulator to calculate whether an obstacle blocks a simulated sensor's 
#                 line of sight.