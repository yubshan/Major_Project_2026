# Requirement / Purpose: Generates dummy navigation states (fake 50x50 occupancy grid NumPy arrays, fake robot positions,
#  and fake coordinate paths).

# Why it is needed: Allows Teammate B to test complex decision rules (e.g., "If an obstacle is ahead, look at
#  the occupancy grid to determine whether to swing left or right") completely in isolation, using simple terminal prints,
#  without needing the Pygame UI running.

# Teammate Roles:

#     Teammate B: Builds this file to create their own automated test suite for the 9 core system scenarios.

#     Teammate A: Reviews this file to ensure the fake arrays match how their actual mapping module will construct them.