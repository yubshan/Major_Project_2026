import pygame
from config import *
from utils import WorldToScreen


class Map:
    def __init__(self):
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

        # Outer boundary walls
        for i in range(GRID_WIDTH):
            self.grid[0][i] = 1
            self.grid[GRID_HEIGHT - 1][i] = 1
        for i in range(GRID_HEIGHT):
            self.grid[i][0] = 1
            self.grid[i][GRID_WIDTH - 1] = 1

        # Horizontal divider wall with wide opening (cols 15-25 are open = 2 metres)
        for col in range(1, 15):
            self.grid[20][col] = 1
        for col in range(25, GRID_WIDTH - 1):
            self.grid[20][col] = 1

        # Isolated 3x3 box in top half
        for r in range(7, 10):
            for c in range(28, 31):
                self.grid[r][c] = 1

        # Isolated 3x3 box in bottom half
        for r in range(28, 31):
            for c in range(10, 13):
                self.grid[r][c] = 1

    def world_to_grid(self, x, y):
        col = int((x + (GRID_WIDTH * GRID_CELL_SIZE) / 2) / GRID_CELL_SIZE)
        row = int(((GRID_HEIGHT * GRID_CELL_SIZE) / 2 - y) / GRID_CELL_SIZE)
        return col, row

    def is_obstacle(self, x, y):
        col, row = self.world_to_grid(x, y)
        if 0 <= col < GRID_WIDTH and 0 <= row < GRID_HEIGHT:
            return self.grid[row][col] == 1
        return True

    def render(self, screen):
        half_w = (GRID_WIDTH * GRID_CELL_SIZE) / 2
        half_h = (GRID_HEIGHT * GRID_CELL_SIZE) / 2

        for row in range(GRID_HEIGHT):
            for col in range(GRID_WIDTH):
                if self.grid[row][col] == 1:
                    world_x = (col * GRID_CELL_SIZE) - half_w + (GRID_CELL_SIZE / 2)
                    world_y = half_h - (row * GRID_CELL_SIZE) - (GRID_CELL_SIZE / 2)

                    scr_x, scr_y = WorldToScreen(world_x, world_y, PPM, SCREEN_WIDTH, SCREEN_HEIGH)

                    cell_px = int(GRID_CELL_SIZE * PPM)
                    pygame.draw.rect(
                        screen, (80, 80, 80),
                        (scr_x - cell_px // 2, scr_y - cell_px // 2, cell_px, cell_px)
                    )