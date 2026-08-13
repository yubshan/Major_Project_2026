import unittest

from modules.navigation.tof_to_grid import tof_cell_to_grid


class TestTofToGrid(unittest.TestCase):

    def test_left_center_zone(self):
        result = tof_cell_to_grid(
            robot_x=0,
            robot_y=0,
            robot_heading=0,
            distance_cm=100,
            row=3,
            col=3
        )

        self.assertEqual(result, (25, 35))


    def test_right_center_zone(self):
        result = tof_cell_to_grid(
            robot_x=0,
            robot_y=0,
            robot_heading=0,
            distance_cm=100,
            row=3,
            col=4
        )

        self.assertEqual(result, (25, 35))

    def test_invalid_distance(self):
        result = tof_cell_to_grid(
            robot_x=0,
            robot_y=0,
            robot_heading=0,
            distance_cm=0,
            row=3,
            col=3
        )

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()