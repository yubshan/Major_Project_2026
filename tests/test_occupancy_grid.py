import unittest

import numpy as np

from shared.occupancy_grid import (
    OccupancyGrid,
    FREE,
    OCCUPIED,
    UNKNOWN
)


class TestOccupancyGrid(unittest.TestCase):

    def test_initial_grid(self):
        grid = OccupancyGrid()

        self.assertEqual(grid.data.shape, (50, 50))
        self.assertEqual(grid.data.dtype, np.int8)
        self.assertTrue(np.all(grid.data == UNKNOWN))

    def test_set_and_get_cell(self):
        grid = OccupancyGrid()

        grid.set_cell(25, 26, FREE)

        self.assertEqual(grid.get_cell(25, 26), FREE)

    def test_set_occupied_cell(self):
        grid = OccupancyGrid()

        grid.set_cell(25, 27, OCCUPIED)

        self.assertEqual(grid.get_cell(25, 27), OCCUPIED)

    def test_get_out_of_bounds_cell(self):
        grid = OccupancyGrid()

        with self.assertRaises(IndexError):
            grid.get_cell(50, 25)

    def test_set_out_of_bounds_cell(self):
        grid = OccupancyGrid()

        with self.assertRaises(IndexError):
            grid.set_cell(25, 50, FREE)

    def test_invalid_occupancy_value(self):
        grid = OccupancyGrid()

        with self.assertRaises(ValueError):
            grid.set_cell(25, 25, 99)


    def test_negative_occupancy_value(self):
        grid = OccupancyGrid()

        with self.assertRaises(ValueError):
            grid.set_cell(25, 25, -1)

    def test_update_ray_with_obstacle(self):
        grid = OccupancyGrid()

        grid.update_ray(
            (25, 25),
            (25, 28),
            obstacle_detected=True
        )

        self.assertEqual(grid.get_cell(25, 25), FREE)
        self.assertEqual(grid.get_cell(25, 26), FREE)
        self.assertEqual(grid.get_cell(25, 27), FREE)
        self.assertEqual(grid.get_cell(25, 28), OCCUPIED)


    def test_update_ray_without_obstacle(self):
        grid = OccupancyGrid()

        grid.update_ray(
            (25, 25),
            (25, 28),
            obstacle_detected=False
        )

        self.assertEqual(grid.get_cell(25, 25), FREE)
        self.assertEqual(grid.get_cell(25, 26), FREE)
        self.assertEqual(grid.get_cell(25, 27), FREE)
        self.assertEqual(grid.get_cell(25, 28), FREE)
        
if __name__ == "__main__":
    unittest.main()