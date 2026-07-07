# Requirement / Purpose: Implements a thread-safe FIFO (First-In, First-Out) data queue using Python's native queue.Queue.

# Why it is needed: During the simulation phase (Weeks 1–18), Teammate C's physics loop generates sensor readings. 
# These readings need to stream directly into Teammate A's mapping code. A queue allows Teammate C to quickly drop
#  data into a bucket so Teammate A can fish it out at their own pace without slowing down the visualization frame rate.

# Teammate Roles:

#     Teammate C: Instantiates the queue. Pushes simulated data packets into it inside the simulation loop.

#     Teammate A: Continuously listens to the queue, pops the data out, and feeds it into the occupancy grid logic.