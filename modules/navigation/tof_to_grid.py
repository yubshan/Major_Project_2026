# VL53L5CX:
# 8 × 8 zones
# 45° horizontal FoV
# 45° vertical FoV
# ≈ 5.625° per zone

import math

from shared.coordinate_system import world_to_grid


TOF_GRID_SIZE = 8
TOF_HORIZONTAL_FOV = 45.0
TOF_ZONE_ANGLE = TOF_HORIZONTAL_FOV / TOF_GRID_SIZE


def tof_cell_to_grid(
    robot_x,
    robot_y,
    robot_heading,
    distance_cm,
    row,
    col
):
    """
    Convert one VL53L5CX ToF zone measurement
    into an occupancy-grid cell.
    """

    # Ignore invalid measurements
    if distance_cm <= 0:
        return None

    # Calculate horizontal angle of the ToF zone.
    #
    # Column 0 is the left side of the FoV.
    # Column 7 is the right side.
    #
    # The angle is measured relative to robot forward.
    sensor_angle = (
        (col + 0.5) * TOF_ZONE_ANGLE
        - TOF_HORIZONTAL_FOV / 2
    )

    world_angle = robot_heading + sensor_angle

    angle_radians = math.radians(world_angle)

    x = (
        robot_x
        + distance_cm * math.cos(angle_radians)
    )

    y = (
        robot_y
        + distance_cm * math.sin(angle_radians)
    )

    return world_to_grid(x, y)