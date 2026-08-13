from modules.navigation.sensor_to_grid import sensor_to_grid
from shared.coordinate_system import world_to_grid
from modules.navigation.tof_to_grid import tof_cell_to_grid

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
    
def update_tof_cell(
        grid,
        robot_x,
        robot_y,
        robot_heading,
        distance_cm,
        row,
        col
    ):
        # Ignore invalid measurements
        if distance_cm <= 0:
            return

        start = world_to_grid(
            robot_x,
            robot_y
        )

        end = tof_cell_to_grid(
            robot_x,
            robot_y,
            robot_heading,
            distance_cm,
            row,
            col
        )

        grid.update_ray(
            start,
            end,
            obstacle_detected=True
        )

def update_tof_grid(
    grid,
    robot_x,
    robot_y,
    robot_heading,
    tof_grid
):
    for row in range(8):
        for col in range(8):
            distance_cm = tof_grid[row][col]

            update_tof_cell(
                grid=grid,
                robot_x=robot_x,
                robot_y=robot_y,
                robot_heading=robot_heading,
                distance_cm=distance_cm,
                row=row,
                col=col
            )

def update_map(
    grid,
    robot_x,
    robot_y,
    robot_heading,
    sensor_packet
):
    update_ultrasonic_sensors(
        grid=grid,
        robot_x=robot_x,
        robot_y=robot_y,
        robot_heading=robot_heading,
        sensor_packet=sensor_packet
    )

    update_tof_grid(
        grid=grid,
        robot_x=robot_x,
        robot_y=robot_y,
        robot_heading=robot_heading,
        tof_grid=sensor_packet["tof_grid"]
    )