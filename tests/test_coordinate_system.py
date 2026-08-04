import unittest

from shared.coordinate_system import (
    world_to_grid,
    grid_to_world,
)

class TestCoordinateSystem(unittest.TestCase):
    def test_origin(self):
        self.assertEqual(world_to_grid(0, 0), (25, 25))

    def test_positive_coordinates(self):
        self.assertEqual(world_to_grid(10, 0), (25, 26))
        self.assertEqual(world_to_grid(0, 10), (24, 25))

    def test_negative_coordinates(self):
        self.assertEqual(world_to_grid(-10, 0), (25, 24))
        self.assertEqual(world_to_grid(0, -10), (26, 25))

    def test_grid_to_world(self):
        self.assertEqual(grid_to_world(25, 25), (0, 0))
        self.assertEqual(grid_to_world(25, 26), (10, 0))
        self.assertEqual(grid_to_world(24, 25), (0, 10))
        self.assertEqual(grid_to_world(25, 24), (-10, 0))
        self.assertEqual(grid_to_world(26, 25), (0, -10))

if __name__ == "__main__":
    unittest.main()