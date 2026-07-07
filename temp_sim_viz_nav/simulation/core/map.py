import pygame
from config import *
from utils import WorldToScreen


FREE = 0 
WALL = 1
FIRE = 2
VICTIM = 3
COLLAPSE_ZONE = 4

class Map:
    def __init__(self):
        self.grid = [[FREE for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

        # Outer boundary walls
        for i in range(GRID_WIDTH):
            self.grid[0][i] = WALL
            self.grid[GRID_HEIGHT - 1][i] = WALL
        for i in range(GRID_HEIGHT):
            self.grid[i][0] = WALL
            self.grid[i][GRID_WIDTH - 1] = WALL

        # Horizontal divider wall with wide opening (cols 15-25 are open = 2 metres)
        for col in range(1, 15):
            self.grid[20][col] = WALL
        for col in range(25, GRID_WIDTH - 1):
            self.grid[20][col] = WALL

        # Isolated 3x3 box in top half
        for r in range(7, 10):
            for c in range(28, 31):
                self.grid[r][c] = VICTIM

        # Isolated 3x3 box in bottom half
        for r in range(28, 31):
            for c in range(10, 13):
                self.grid[r][c] = COLLAPSE_ZONE
        
        for r in range (75, 78):
            for c in range (10, 13):
                self.grid[r][c] = FIRE

                
        for r in range (30, 33):
            for c in range (60, 63):
                self.grid[r][c] = FIRE


        for r in range (60, 63):
            for c in range (50, 53):
                self.grid[r][c] = FIRE


            

    def world_to_grid(self, x, y):
        col = int((x + (GRID_WIDTH * GRID_CELL_SIZE) / 2) / GRID_CELL_SIZE)
        row = int(((GRID_HEIGHT * GRID_CELL_SIZE) / 2 - y) / GRID_CELL_SIZE)
        return col, row

    def is_obstacle(self, x, y):
        col, row = self.world_to_grid(x, y)
        
        if 0 <= col < GRID_WIDTH and 0 <= row < GRID_HEIGHT:
            return self.grid[row][col] != FREE
        return True

    def cell_type(self, x, y):
        col, row = self.world_to_grid(x, y)
        if 0 <= col <GRID_WIDTH and 0 <= row < GRID_HEIGHT:
            return self.grid[row][col]
    
    def is_passable(self,x, y):
        col, row = self.world_to_grid(x, y)
        return self.grid[row][col] == FREE
    
    def is_victim(self, x, y):
        col, row = self.world_to_grid(x, y)
        return self.grid[row][col] == VICTIM

    def render(self, screen):
        half_w = (GRID_WIDTH * GRID_CELL_SIZE) / 2
        half_h = (GRID_HEIGHT * GRID_CELL_SIZE) / 2
        
        cell_px = int(GRID_CELL_SIZE * PPM)
        
        colors = {
            WALL: (80, 80, 80),
            FIRE: (255, 69, 0),
            VICTIM: (0, 255, 0),
            COLLAPSE_ZONE: (139, 69, 19)
        }

        for row in range(GRID_HEIGHT):
            for col in range(GRID_WIDTH):
                cell_type = self.grid[row][col]

                if cell_type != FREE:
                    world_x = (col * GRID_CELL_SIZE) - half_w + (GRID_CELL_SIZE / 2)
                    world_y = half_h - (row * GRID_CELL_SIZE) - (GRID_CELL_SIZE / 2)
                    scr_x, scr_y = WorldToScreen(world_x, world_y, PPM, SCREEN_WIDTH, SCREEN_HEIGH)

                    pygame.draw.rect(
                        screen, 
                        colors.get(cell_type, (0, 0, 0)),
                        (scr_x - cell_px // 2, scr_y - cell_px // 2, cell_px, cell_px)
                    )