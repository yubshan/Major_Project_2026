import unittest

from modules.navigation.a_star import a_star
from modules.navigation.occupancy_grid import (
    OccupancyGrid,
    OCCUPIED
)


class TestAStar(unittest.TestCase):

    def test_straight_path(self):
        grid = OccupancyGrid()

        start = (25, 25)
        goal = (25, 30)

        path = a_star(grid, start, goal)

        expected = [
            (25, 25),
            (25, 26),
            (25, 27),
            (25, 28),
            (25, 29),
            (25, 30)
        ]

        self.assertEqual(path, expected)


    def test_path_avoids_obstacle(self):
        grid = OccupancyGrid()

        # Block the direct path.
        grid.set_cell(25, 27, OCCUPIED)

        start = (25, 25)
        goal = (25, 30)

        path = a_star(grid, start, goal)

        self.assertIsNotNone(path)

        self.assertNotIn(
            (25, 27),
            path
        )


    def test_no_path(self):
        grid = OccupancyGrid()

        start = (25, 25)
        goal = (25, 27)

        # Completely surround the goal.
        grid.set_cell(24, 27, OCCUPIED)
        grid.set_cell(26, 27, OCCUPIED)
        grid.set_cell(25, 26, OCCUPIED)
        grid.set_cell(25, 28, OCCUPIED)

        path = a_star(grid, start, goal)

        self.assertIsNone(path)

    def test_path_near_grid_boundary(self):
        grid = OccupancyGrid()

        start = (0, 0)
        goal = (0, 3)

        path = a_star(grid, start, goal)

        expected = [
            (0, 0),
            (0, 1),
            (0, 2),
            (0, 3)
        ]

        self.assertEqual(path, expected)
    
    def test_path_around_wall(self):
        grid = OccupancyGrid()

        start = (25, 25)
        goal = (25, 30)

        # Create a wall across the direct path.
        grid.set_cell(25, 26, OCCUPIED)
        grid.set_cell(25, 27, OCCUPIED)
        grid.set_cell(25, 28, OCCUPIED)
        grid.set_cell(25, 29, OCCUPIED)

        path = a_star(grid, start, goal)

        self.assertIsNotNone(path)

        # The path must not pass through the wall.
        for cell in [
            (25, 26),
            (25, 27),
            (25, 28),
            (25, 29)
        ]:
            self.assertNotIn(cell, path)

        # Path must begin at start and end at goal.
        self.assertEqual(path[0], start)
        self.assertEqual(path[-1], goal)
    
    def test_occupied_goal(self):
        grid = OccupancyGrid()

        start = (25, 25)
        goal = (25, 30)

        grid.set_cell(25, 30, OCCUPIED)

        path = a_star(grid, start, goal)

        self.assertIsNone(path)
    
    def test_occupied_start(self):
        grid = OccupancyGrid()

        start = (25, 25)
        goal = (25, 30)

        grid.set_cell(25, 25, OCCUPIED)

        path = a_star(grid, start, goal)

        self.assertIsNone(path)

    def test_start_out_of_bounds(self):
        grid = OccupancyGrid()

        start = (-1, 25)
        goal = (25, 30)

        path = a_star(grid, start, goal)

        self.assertIsNone(path)

    def test_goal_out_of_bounds(self):
        grid = OccupancyGrid()

        start = (25, 25)
        goal = (50, 30)

        path = a_star(grid, start, goal)

        self.assertIsNone(path)
        
if __name__ == "__main__":
    unittest.main()