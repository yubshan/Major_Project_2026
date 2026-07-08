# Requirement / Purpose: A text dictionary or schema file that strictly defines what a raw sensor data payload looks like
#  (the exact names of keys like us_front, tof_grid, and their expected data types).

#     Why it is needed: Teammate C is building a simulator that spits out fake sensor readings. Later, 
#     Teammate A is writing real ESP32 firmware that spits out real sensor readings. 
#     Teammate A's mapping code must read both seamlessly. By defining the data layout here,
#     Teammate C knows exactly how to format the simulator output, 
#     and Teammate A knows exactly how to write their parser.

#     Teammate Roles:

#         Teammate A: Defines the dictionary keys and structures.

#         Teammate C: References this file to ensure their simulated sensor engine and ESP32 WiFi JSON packets match 
#                      this structure byte-for-byte.