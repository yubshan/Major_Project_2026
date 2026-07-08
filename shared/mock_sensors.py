# Requirement / Purpose: Generates static, predefined sensor packets (e.g., simulating a tight corridor or an obstacle right in
#  front of the nose).

#     Why it is needed: Teammate A needs to build their mapping loop and pathfinding logic in Weeks 7–14. 
#     They cannot wait around for Teammate C to finish the Pygame simulator dashboard. This file provides immediate, 
#     predictable inputs to test the math.

#     Teammate Roles:

#         Teammate A: Builds this to verify that their A* pathfinding can navigate out of a mock corridor.

#         Teammate B: Uses it to double-check that safety behaviors (EscapeDanger) trigger properly when a mock sensor 
#         reading drops below 8cm.