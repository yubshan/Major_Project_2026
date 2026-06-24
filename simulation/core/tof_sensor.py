import math
import pygame
from config import *
from utils import WorldToScreen
from core.ray import Ray

class ToFSensor:
    def __init__(self, robot, offset_angle= 0):
        self.robot = robot
        self.offset_angle = offset_angle

        self.rows = TOF_ROWS
        self.cols = TOF_COLS

        self.fov = TOF_FOV
        self.zone_angle = TOF_FOV / self.cols

        self.max_range = TOF_MAX_RANGE

        self.depth_grid = [[self.max_range] * self.cols for _ in range(self.rows)]
        self.signal_grid = [[0.0] * self.cols for _ in range(self.rows)]


    def sense(self, grid, current_round = None):
        center_angle = self.robot.turnDegree + self.offset_angle
        start_angle = center_angle - self.fov / 2

        col_distances = []
        for col in range(self.cols):
            ray_angle = start_angle + (col + 0.5) * self.zone_angle
            ray = Ray(ray_angle, self.robot)
            ray.cast(grid)
            dist = max(0.02, ray.rayRange)
            col_distances.append(dist)
        
        for row in range(self.rows):
            for col in range(self.cols):
                dist = col_distances[col]
                self.depth_grid[row][col] = dist

                self.signal_grid[row][col] = 1 - (dist / self.max_range)

        return self.depth_grid
   
    def render(self, screen):
        if not TOF_RENDER_OVERLAY:
            return
        
        robot_sx , robot_sy = WorldToScreen(self.robot.x, self.robot.y, PPM , SCREEN_WIDTH, SCREEN_HEIGH)

        center_angle = self.robot.turnDegree + self.offset_angle 
        start_angle  = center_angle - self.fov / 2.0

        for col in range(self.cols):
            ray_angle = start_angle + (0.5 + col) * self.zone_angle
            dist = self.depth_grid[0][col]

            end_wx = self.robot.x + dist * math.cos(ray_angle)
            end_wy = self.robot.y + dist * math.sin(ray_angle)

            end_sx, end_sy = WorldToScreen(end_wx, end_wy, PPM, SCREEN_WIDTH, SCREEN_HEIGH)


            signal = 1.0 - (dist / self.max_range)
            r = 0
            g = int (signal * 200)
            b = int ((1.0  - signal) * 255)


            pygame.draw.line(screen, (r,g,b), (robot_sx, robot_sy), (end_sx, end_sy), 1)

        for edge_offset in [-self.fov / 2.0, self.fov/2.0]:
            edge_angle = center_angle + edge_offset
            end_wx = self.robot.x + self.max_range * math.cos(edge_angle)
            end_wy = self.robot.y + self.max_range * math.sin(edge_angle)
            end_sx, end_sy = WorldToScreen(end_wx, end_wy, PPM , SCREEN_WIDTH, SCREEN_HEIGH)
            pygame.draw.line(screen, (0,150,255), (robot_sx, robot_sy), (end_sx, end_sy), 1)

    
