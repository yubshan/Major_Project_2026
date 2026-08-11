from modules.navigation.sensor_to_grid import sensor_to_grid


def update_front_sensor(grid, robot_x, robot_y, robot_heading, distance_cm):

    # Ignore invalid or unavailable sensor measurements
    if distance_cm <= 0:
        return

    start = sensor_to_grid(
        robot_x,
        robot_y,
        0,
        0,
        robot_heading
    )

    end = sensor_to_grid(
        robot_x,
        robot_y,
        distance_cm,
        0,
        robot_heading
    )

    grid.update_ray(
        start,
        end,
        obstacle_detected=True
    )



ULTRASONIC_ANGLES = {
    "us_front": 0,
    "us_left45": 45,
    "us_left90": 90,
    "us_right45": -45,
    "us_right90": -90,
}

def update_ultrasonic_sensors(
    grid,
    robot_x,
    robot_y,
    robot_heading,
    sensor_packet
):
    for sensor_name, sensor_angle in ULTRASONIC_ANGLES.items():

        distance_cm = sensor_packet[sensor_name]

        # Ignore invalid or unavailable measurements
        if distance_cm <= 0:
            continue

        start = sensor_to_grid(
            robot_x,
            robot_y,
            0,
            0,
            robot_heading
        )

        end = sensor_to_grid(
            robot_x,
            robot_y,
            distance_cm,
            sensor_angle,
            robot_heading
        )

        grid.update_ray(
            start,
            end,
            obstacle_detected=True
        )