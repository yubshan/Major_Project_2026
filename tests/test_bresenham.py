import unittest
from unittest import result

from shared.bresenham import bresenham_line

class TestBresenham(unittest.TestCase):

    def test_horizontal_line(self):
        result = bresenham_line((25, 25), (25, 29))

        expected = [
            (25, 25),
            (25, 26),
            (25, 27),
            (25, 28),
            (25, 29)
        ]

        self.assertEqual(result, expected)

    def test_vertical_line(self):
        result = bresenham_line((25, 25), (29, 25))

        expected = [
            (25, 25),
            (26, 25),
            (27, 25),
            (28, 25),
            (29, 25)
        ]

        self.assertEqual(result, expected)

    def test_diagonal_line(self):
        result = bresenham_line((25, 25), (29, 29))

        expected = [
            (25, 25),
            (26, 26),
            (27, 27),
            (28, 28),
            (29, 29)
        ]

        self.assertEqual(result, expected)

    def test_reverse_horizontal_line(self):
        result = bresenham_line((25, 29), (25, 25))

        expected = [
            (25, 29),
            (25, 28),
            (25, 27),
            (25, 26),
            (25, 25)
        ]

        self.assertEqual(result, expected)


    def test_non_45_degree_line(self):
        result = bresenham_line((25, 25), (29, 27))

        expected = [
            (25, 25),
            (26, 25),
            (27, 26),
            (28, 26),
            (29, 27)
        ]

        self.assertEqual(result, expected)
    
if __name__ == "__main__":
    unittest.main()