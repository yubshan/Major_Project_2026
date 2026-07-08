# Requirement / Purpose: Houses the custom, thread-safe central dictionary class that holds the global state of the robot. 
# It uses threading locks (threading.Lock()) to prevent data corruption.

# Why it is needed: Your modules run concurrently on separate threads. 
# If Yubshan's WiFi module tries to write a human position at the exact microsecond 
# Teammate B's decision tree tries to read it, Python will throw a fatal runtime error or corrupt the data. 
# This file safely gates access so only one thread can touch the data at a time.

# Teammate Roles:

#     Teammate A: Writes and maintains the thread-safe Blackboard class code.

#     Yubshan (WiFi Lead): Imports it; calls blackboard.set("detection/result", ...) every 1–2 seconds.

#     Teammate B (Decision Lead): Imports it; continuously reads everything to tick the Behavior Tree, 
#                                 then writes the final output to state/motor_command.

#     Teammate C (Sim Lead): Imports it; continuously reads all states to draw them onto the 4-panel Pygame screen.