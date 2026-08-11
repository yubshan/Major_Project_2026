import unittest

from modules.navigation.mapping import (
    update_front_sensor,
    update_ultrasonic_sensors
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

if __name__ == "__main__":
    unittest.main()