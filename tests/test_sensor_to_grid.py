import unittest

from modules.navigation.sensor_to_grid import sensor_to_grid


class TestSensorToGrid(unittest.TestCase):

    def test_front_sensor_with_90_degree_heading(self):
        result = sensor_to_grid(
            robot_x=0,
            robot_y=0,
            distance_cm=30,
            sensor_angle_degrees=0,
            robot_heading_degrees=90
        )

        self.assertEqual(result, (22, 25))

    def test_front_sensor_with_180_degree_heading(self):
        result = sensor_to_grid(
            robot_x=0,
            robot_y=0,
            distance_cm=30,
            sensor_angle_degrees=0,
            robot_heading_degrees=180
        )

        self.assertEqual(result, (25, 22))


    def test_front_sensor_with_270_degree_heading(self):
        result = sensor_to_grid(
            robot_x=0,
            robot_y=0,
            distance_cm=30,
            sensor_angle_degrees=0,
            robot_heading_degrees=270
        )

        self.assertEqual(result, (28, 25))

    def test_front_sensor(self):
        result = sensor_to_grid(
            robot_x=0,
            robot_y=0,
            distance_cm=30,
            sensor_angle_degrees=0
        )

        self.assertEqual(result, (25, 28))

    def test_left_sensor(self):
        result = sensor_to_grid(
            robot_x=0,
            robot_y=0,
            distance_cm=30,
            sensor_angle_degrees=90
        )

        self.assertEqual(result, (22, 25))

    def test_right_sensor(self):
        result = sensor_to_grid(
            robot_x=0,
            robot_y=0,
            distance_cm=30,
            sensor_angle_degrees=-90
        )

        self.assertEqual(result, (28, 25))
    
    def test_left45_sensor(self):
        result = sensor_to_grid(
            robot_x=0,
            robot_y=0,
            distance_cm=100,
            sensor_angle_degrees=45
        )

        self.assertEqual(result, (18, 32))


    def test_right45_sensor(self):
        result = sensor_to_grid(
            robot_x=0,
            robot_y=0,
            distance_cm=100,
            sensor_angle_degrees=-45
        )

        self.assertEqual(result, (32, 32))
        
if __name__ == "__main__":
    unittest.main()