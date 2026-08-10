import math

from shared.coordinate_system import world_to_grid


def sensor_to_grid(
    robot_x,
    robot_y,
    distance_cm,
    sensor_angle_degrees,
    robot_heading_degrees=0
):
    world_angle_degrees = (
        robot_heading_degrees + sensor_angle_degrees
    )

    angle_radians = math.radians(world_angle_degrees)

    sensor_x = (
        robot_x
        + distance_cm * math.cos(angle_radians)
    )

    sensor_y = (
        robot_y
        + distance_cm * math.sin(angle_radians)
    )

    return world_to_grid(sensor_x, sensor_y)