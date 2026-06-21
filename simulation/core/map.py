import pygame
from config import *
from utils import WorldToScreen


class Map:
    def __init__(self):
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

        for i in range(GRID_WIDTH):
            self.grid[0][i] = 1
            self.grid[GRID_HEIGHT - 1][i] = 1
        for i in range(GRID_HEIGHT):
            self.grid[i][0] = 1
            self.grid[i][GRID_WIDTH-1] = 1
        
        self.grid[15][20] = 1
        self.grid[16][20] = 1
        self.grid[17][20] = 1

        self.grid[35][35] = 1
        self.grid[34][34] = 1
        self.grid[35][34] = 1
        self.grid[34][35] = 1

    def world_to_grid(self, x, y):
        col = int((x + (GRID_WIDTH * GRID_CELL_SIZE) / 2) / GRID_CELL_SIZE)
        row = int(((GRID_HEIGHT * GRID_CELL_SIZE) / 2 - y) / GRID_CELL_SIZE)
        return col, row
    
    def is_obstacle(self, x, y):
        col, row = self.world_to_grid(x, y)
        if 0 <= col < GRID_WIDTH and 0 <= row < GRID_HEIGHT:
            return self.grid[row][col] == 1
        return True
    
    def render (self, screen):
        half_w = (GRID_WIDTH * GRID_CELL_SIZE) / 2
        half_h = (GRID_HEIGHT * GRID_CELL_SIZE) / 2

        for row in range(GRID_HEIGHT):
            for col in range(GRID_WIDTH):
                if self.grid[row][col] == 1:
                    world_x = (col * GRID_CELL_SIZE) - half_w + (GRID_CELL_SIZE / 2)
                    world_y = half_h - (row * GRID_CELL_SIZE) - (GRID_CELL_SIZE / 2)
                    
                    scr_x, scr_y = WorldToScreen(world_x, world_y, PPM, SCREEN_WIDTH, SCREEN_HEIGH)
                    
                    cell_px = int(GRID_CELL_SIZE * PPM)
                    pygame.draw.rect(screen, (80, 80, 80), (scr_x - cell_px//2, scr_y - cell_px//2, cell_px, cell_px))
