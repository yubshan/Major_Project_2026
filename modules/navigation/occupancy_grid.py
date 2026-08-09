import numpy as np

from shared.bresenham import bresenham_line

GRID_WIDTH = 50
GRID_HEIGHT = 50

FREE = 0
OCCUPIED = 1
UNKNOWN = 2

class OccupancyGrid:

    def __init__(self):
        self.data = np.full(
            (GRID_HEIGHT, GRID_WIDTH),
            UNKNOWN,
            dtype=np.int8
        )
    
    def _is_valid_cell(self, row, col):
        return (
            0 <= row < GRID_HEIGHT
            and
            0 <= col < GRID_WIDTH
        )
    
    def get_cell(self, row, col):
        if not self._is_valid_cell(row, col):
            raise IndexError("Grid cell is out of bounds")

        return self.data[row, col]
    
    def set_cell(self, row, col, value):
        if not self._is_valid_cell(row, col):
            raise IndexError("Grid cell is out of bounds")

        if value not in (FREE, OCCUPIED, UNKNOWN):
            raise ValueError("Invalid occupancy value")

        self.data[row, col] = value

    def update_ray(self, start, end, obstacle_detected=True):
        cells = bresenham_line(start, end)

        if obstacle_detected:
            for cell in cells[:-1]:
                row, col = cell
                self.set_cell(row, col, FREE)

            row, col = cells[-1]
            self.set_cell(row, col, OCCUPIED)

        else:
            for cell in cells:
                row, col = cell
                self.set_cell(row, col, FREE)