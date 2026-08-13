import unittest

from shared.mock_sensors import get_mock_sensor_packet

from modules.navigation.mapping import (
    update_front_sensor,
    update_ultrasonic_sensors,
    update_tof_cell,
    update_tof_grid,
    update_map
)

from modules.navigation.occupancy_grid import (
    OccupancyGrid,
    FREE,
    OCCUPIED,
    UNKNOWN
)

class TestMapping(unittest.TestCase):

    def test_front_sensor_obstacle(self):
        grid = OccupancyGrid()

        update_front_sensor(
            grid=grid,
            robot_x=0,
            robot_y=0,
            robot_heading=0,
            distance_cm=30
        )

        self.assertEqual(grid.get_cell(25, 25), FREE)
        self.assertEqual(grid.get_cell(25, 26), FREE)
        self.assertEqual(grid.get_cell(25, 27), FREE)
        self.assertEqual(grid.get_cell(25, 28), OCCUPIED)

    def test_front_sensor_invalid_zero_distance(self):
        grid = OccupancyGrid()

        update_front_sensor(
            grid=grid,
            robot_x=0,
            robot_y=0,
            robot_heading=0,
            distance_cm=0
        )

        self.assertEqual(grid.get_cell(25, 25), UNKNOWN)

    def test_all_ultrasonic_sensors(self):
        grid = OccupancyGrid()

        sensor_packet = {
            "us_front": 30,
            "us_left45": 30,
            "us_left90": 30,
            "us_right45": 30,
            "us_right90": 30
        }

        update_ultrasonic_sensors(
            grid=grid,
            robot_x=0,
            robot_y=0,
            robot_heading=0,
            sensor_packet=sensor_packet
        )

        # Front
        self.assertEqual(grid.get_cell(25, 28), OCCUPIED)

        # Left 90°
        self.assertEqual(grid.get_cell(22, 25), OCCUPIED)

        # Right 90°
        self.assertEqual(grid.get_cell(28, 25), OCCUPIED)

    def test_45_degree_ultrasonic_sensors(self):
        grid = OccupancyGrid()

        sensor_packet = {
            "us_front": 0,
            "us_left45": 100,
            "us_left90": 0,
            "us_right45": 100,
            "us_right90": 0
        }

        update_ultrasonic_sensors(
            grid=grid,
            robot_x=0,
            robot_y=0,
            robot_heading=0,
            sensor_packet=sensor_packet
        )

        # Left 45° sensor
        self.assertEqual(grid.get_cell(18, 32), OCCUPIED)

        # Right 45° sensor
        self.assertEqual(grid.get_cell(32, 32), OCCUPIED)

    def test_obstacle_ahead_scenario(self):
        grid = OccupancyGrid()

        sensor_packet = get_mock_sensor_packet("obstacle_ahead")

        update_ultrasonic_sensors(
            grid=grid,
            robot_x=0,
            robot_y=0,
            robot_heading=0,
            sensor_packet=sensor_packet
        )

        self.assertEqual(grid.get_cell(25, 28), OCCUPIED)

    def test_left_blocked_scenario(self):
        grid = OccupancyGrid()

        sensor_packet = get_mock_sensor_packet("left_blocked")

        update_ultrasonic_sensors(
            grid=grid,
            robot_x=0,
            robot_y=0,
            robot_heading=0,
            sensor_packet=sensor_packet
        )

        self.assertEqual(grid.get_cell(23, 27), OCCUPIED)
        self.assertEqual(grid.get_cell(24, 26), FREE)


    def test_right_blocked_scenario(self):
        grid = OccupancyGrid()

        sensor_packet = get_mock_sensor_packet("right_blocked")

        update_ultrasonic_sensors(
            grid=grid,
            robot_x=0,
            robot_y=0,
            robot_heading=0,
            sensor_packet=sensor_packet
        )

        self.assertEqual(grid.get_cell(27, 27), OCCUPIED)
        self.assertEqual(grid.get_cell(26, 26), FREE)


    def test_open_front_scenario(self):
        grid = OccupancyGrid()

        sensor_packet = get_mock_sensor_packet("open_front")

        update_ultrasonic_sensors(
            grid=grid,
            robot_x=0,
            robot_y=0,
            robot_heading=0,
            sensor_packet=sensor_packet
        )

        self.assertEqual(grid.get_cell(25, 45), OCCUPIED)

    def test_narrow_corridor_scenario(self):
        grid = OccupancyGrid()

        sensor_packet = get_mock_sensor_packet("narrow_corridor")

        update_ultrasonic_sensors(
            grid=grid,
            robot_x=0,
            robot_y=0,
            robot_heading=0,
            sensor_packet=sensor_packet
        )

        # Front remains open
        self.assertEqual(grid.get_cell(25, 45), OCCUPIED)

        # Left 90° obstacle: 30 cm
        self.assertEqual(grid.get_cell(22, 25), OCCUPIED)

        # Right 90° obstacle: 30 cm
        self.assertEqual(grid.get_cell(28, 25), OCCUPIED)
        
    def test_all_blocked_scenario(self):
        grid = OccupancyGrid()

        sensor_packet = get_mock_sensor_packet("all_blocked")

        update_ultrasonic_sensors(
            grid=grid,
            robot_x=0,
            robot_y=0,
            robot_heading=0,
            sensor_packet=sensor_packet
        )

        # Front: 20 cm
        self.assertEqual(grid.get_cell(25, 27), OCCUPIED)

        # Left 45°: 20 cm
        self.assertEqual(grid.get_cell(24, 26), OCCUPIED)

        # Left 90°: 20 cm
        self.assertEqual(grid.get_cell(23, 25), OCCUPIED)

        # Right 45°: 20 cm
        self.assertEqual(grid.get_cell(26, 26), OCCUPIED)

        # Right 90°: 20 cm
        self.assertEqual(grid.get_cell(27, 25), OCCUPIED)

    def test_tof_single_cell(self):
        grid = OccupancyGrid()

        update_tof_cell(
            grid=grid,
            robot_x=0,
            robot_y=0,
            robot_heading=0,
            distance_cm=100,
            row=3,
            col=3
        )

        self.assertEqual(grid.get_cell(25, 35), OCCUPIED)
    
    def test_tof_invalid_measurement(self):
        grid = OccupancyGrid()

        update_tof_cell(
            grid=grid,
            robot_x=0,
            robot_y=0,
            robot_heading=0,
            distance_cm=0,
            row=3,
            col=3
        )

        self.assertEqual(grid.get_cell(25, 25), UNKNOWN)

    def test_tof_grid(self):
        grid = OccupancyGrid()

        tof_grid = [[0] * 8 for _ in range(8)]

        # Put one valid measurement in the grid.
        tof_grid[3][3] = 100

        update_tof_grid(
            grid=grid,
            robot_x=0,
            robot_y=0,
            robot_heading=0,
            tof_grid=tof_grid
        )

        self.assertEqual(grid.get_cell(25, 35), OCCUPIED)
    
    def test_multiple_tof_cells(self):
        grid = OccupancyGrid()

        tof_grid = [[0] * 8 for _ in range(8)]

        # Two valid ToF measurements
        tof_grid[3][3] = 100
        tof_grid[3][4] = 100

        update_tof_grid(
            grid=grid,
            robot_x=0,
            robot_y=0,
            robot_heading=0,
            tof_grid=tof_grid
        )

        self.assertEqual(grid.get_cell(25, 35), OCCUPIED)
    
    def test_tof_left_and_right_zones(self):
        grid = OccupancyGrid()

        tof_grid = [[0] * 8 for _ in range(8)]

        # Leftmost and rightmost ToF zones
        tof_grid[3][0] = 100
        tof_grid[3][7] = 100

        update_tof_grid(
            grid=grid,
            robot_x=0,
            robot_y=0,
            robot_heading=0,
            tof_grid=tof_grid
        )

        # Leftmost zone
        self.assertEqual(grid.get_cell(28, 34), OCCUPIED)

        # Rightmost zone
        self.assertEqual(grid.get_cell(22, 34), OCCUPIED)
    
    def test_tof_respects_robot_heading(self):
        grid = OccupancyGrid()

        tof_grid = [[0] * 8 for _ in range(8)]

        # Use a central ToF zone
        tof_grid[3][3] = 100

        update_tof_grid(
            grid=grid,
            robot_x=0,
            robot_y=0,
            robot_heading=90,
            tof_grid=tof_grid
        )

        self.assertEqual(grid.get_cell(15, 25), OCCUPIED)

    def test_complete_sensor_packet(self):
        grid = OccupancyGrid()

        sensor_packet = get_mock_sensor_packet("obstacle_ahead")

        update_map(
            grid=grid,
            robot_x=0,
            robot_y=0,
            robot_heading=0,
            sensor_packet=sensor_packet
        )

        # Front ultrasonic sensor detects obstacle at 30 cm
        self.assertEqual(grid.get_cell(25, 28), OCCUPIED)
        
if __name__ == "__main__":
    unittest.main()