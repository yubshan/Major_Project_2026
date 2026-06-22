import pygame
from config import *
from utils import WorldToScreen


class Map:
    def __init__(self):
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

        # 1. Standard Outer Boundary Walls
        for i in range(GRID_WIDTH):
            self.grid[0][i] = 1
            self.grid[GRID_HEIGHT - 1][i] = 1
        for i in range(GRID_HEIGHT):
            self.grid[i][0] = 1
            self.grid[i][GRID_WIDTH - 1] = 1

        # =========================================================================
        # TOUGH HAZARD 1: The "Gated Wall" with an Offset Bottleneck Choke Point
        # =========================================================================
        # A massive wall splits the map horizontally at row 14, leaving only a 
        # tiny 2-cell opening at the far left. Immediately after passing it, 
        # another wall forces a sharp right turn.
        if 14 < GRID_HEIGHT:
            for col in range(5, GRID_WIDTH - 1):  # Leaves a narrow gate at cols 1-4
                self.grid[14][col] = 1
                
        if 18 < GRID_HEIGHT:
            for col in range(1, min(38, GRID_WIDTH - 5)): # Forces a tight snake movement
                self.grid[18][col] = 1

        # # =========================================================================
        # # TOUGH HAZARD 2: The "Deceptive Funnel" (Narrowing V-Shape to a Tight Slit)
        # # =========================================================================
        # # This funnels the robot into a path that gets narrower and narrower, 
        # # ending in a microscopic door (2 cells wide) at the bottom corner.
        # # This tests if your WARNING_ZONE slowing logic prevents high-speed crashes.
        # funnel_start_row = 22
        # for i in range(12):
        #     r = funnel_start_row + i
        #     c_left = 10 + i
        #     c_right = (GRID_WIDTH - 10) - i
            
        #     if r < GRID_HEIGHT and c_left < c_right:
        #         # Left diagonal wall of the funnel
        #         self.grid[r][c_left] = 1
        #         # Right diagonal wall of the funnel
        #         self.grid[r][c_right] = 1
                
        # # The tiny exit door at the bottom of the funnel (row 34)
        # if 34 < GRID_HEIGHT:
        #     for col in range(1, GRID_WIDTH - 1):
        #         # Block everything at the bottom except a small central gap
        #         if abs(col - (GRID_WIDTH // 2)) > 1:
        #             self.grid[34][col] = 1

        # =========================================================================
        # TOUGH HAZARD 3: The "Offset Teeth" Chicane
        # =========================================================================
        # Interlocking vertical pillars that force the robot to execute an S-curve.
        # If the robot spins too wide here, its shoulders will hit a tooth.
        teeth_row_start = 2
        teeth_row_end = 10
        if teeth_row_end < GRID_HEIGHT:
            self.grid[teeth_row_start][15] = 1
            for r in range(teeth_row_start, teeth_row_end):
                self.grid[r][15] = 1 # Downward tooth 1
                self.grid[GRID_HEIGHT - 1 - r][25] = 1 # Upward tooth 2
                
        # =========================================================================
        # TOUGH HAZARD 4: Isolated Deceptive Boulders
        # =========================================================================
        # Floating 1x1 or 2x2 blocks right in the middle of paths to force 
        # the robot to make micro-corrections while tracking walls.
        boulders = [
            (6, 30), (7, 30),
            (25, 5), 
            (40, 20), (40, 21)
        ]
        for r, c in boulders:
            if r < GRID_HEIGHT and c < GRID_WIDTH:
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
