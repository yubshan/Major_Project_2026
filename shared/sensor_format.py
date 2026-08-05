# Sensor distance convention:
# - Positive distance values represent valid measurements.
# - 0 represents an invalid, unavailable, or timed-out measurement.
# - Invalid measurements must not be used to mark obstacles in the occupancy grid.


#defining sensor fields
ULTRASONIC_FIELDS = [
    "us_front",
    "us_left45",
    "us_left90",
    "us_right45",
    "us_right90",
]

REQUIRED_FIELDS = [
    "us_front",
    "us_left45",
    "us_left90",
    "us_right45",
    "us_right90",
    "tof_grid",
    "timestamp",
]

TOF_GRID_SIZE = 8


#creating validation function
def validate_sensor_packet(packet):
    if not isinstance(packet, dict):
        return False

    for field in REQUIRED_FIELDS:
        if field not in packet:
            return False

    for field in ULTRASONIC_FIELDS:      #validating ultrasonic values
        value = packet[field]

        if not isinstance(value, int):
            return False

        if value < 0:
            return False

    if not isinstance(packet["timestamp"], int):     #validating timestamp
        return False

    if packet["timestamp"] < 0:
        return False

    tof_grid = packet["tof_grid"]        #validating tof_grid

    if not isinstance(tof_grid, list):
        return False

    if len(tof_grid) != TOF_GRID_SIZE:
        return False
    
    for row in tof_grid:
        if not isinstance(row, list):
            return False

        if len(row) != TOF_GRID_SIZE:
            return False
    
        for value in row:
            if not isinstance(value, int):
                return False

            if value < 0:
                return False

    return True

