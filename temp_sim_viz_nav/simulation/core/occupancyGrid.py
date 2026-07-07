import math 
import pygame
from config import *
from utils import WorldToScreen

# Structural Constants
FREE = 0 
WALL = 1
FIRE = 2
VICTIM = 3
COLLAPSE_ZONE = 4

class OccupancyGrid():
    def __init__(self):
        self.cells = [[0.0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.hazard_cell = [[FREE for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    
    def world_to_cell(self, world_x, world_y):
        half_w = (GRID_WIDTH * GRID_CELL_SIZE) / 2
        half_h = (GRID_HEIGHT * GRID_CELL_SIZE) / 2

        col = int((world_x + half_w) / GRID_CELL_SIZE)
        row = int((half_h - world_y) / GRID_CELL_SIZE)
        return col, row
    
    def get_line_cells(self, x0, y0, x1, y1):
        """
        Bresenham's Line Algorithm.
        Returns a list of (x, y) grid tuples from (x0, y0) to (x1, y1).
        """
        cells = []
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            cells.append((x0, y0))
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
                
        return cells

    def update_from_tos_sensor(self, env_map, robot, tof_sensor):
        L_OCC = 3
        L_FREE = -3

        start_col, start_row = self.world_to_cell(robot.x, robot.y)
        center_angle = robot.turnDegree + tof_sensor.offset_angle
        start_angle = center_angle - tof_sensor.fov / 2

        for col in range(tof_sensor.cols):
            ray_angle = start_angle + (0.5 + col) * tof_sensor.zone_angle
            hit_distance = tof_sensor.depth_grid[0][col]

            hit_wx = robot.x + hit_distance * math.cos(ray_angle) 
            hit_wy = robot.y + hit_distance * math.sin(ray_angle) 

            end_col, end_row = self.world_to_cell(hit_wx, hit_wy)
            end_col = max(0, min(end_col, GRID_WIDTH - 1))
            end_row = max(0, min(end_row, GRID_HEIGHT - 1))

            ray_path = self.get_line_cells(start_col, start_row, end_col, end_row)

            for cell_c, cell_r in ray_path[:-1]:
                if 0 <= cell_c < GRID_WIDTH and 0 <= cell_r < GRID_HEIGHT:
                    self.cells[cell_r][cell_c] += L_FREE

            if hit_distance < tof_sensor.max_range:
                final_c, final_r = ray_path[-1]
                if 0 <= final_c < GRID_WIDTH and 0 <= final_r < GRID_HEIGHT:
                    self.cells[final_r][final_c] += L_OCC

            for cell_c, cell_r in ray_path:
                if 0 <= cell_c < GRID_WIDTH and 0 <= cell_r < GRID_HEIGHT:
                    self.hazard_cell[cell_r][cell_c] = env_map.cell_type(cell_r, cell_c)

    def update_map_from_ultrasonic(self, env_map, robot, us_sensor):
        L_OCC = 3
        L_FREE = -3

        start_col, start_row = self.world_to_cell(robot.x, robot.y)
        center_angle = robot.turnDegree + us_sensor.offset_angle
        ray_angle = center_angle - (FOV / 2)
        angle_step = FOV / (ULTRASONIC_NUM_RAYS - 1) if ULTRASONIC_NUM_RAYS > 1 else 0

        for i in range(ULTRASONIC_NUM_RAYS):
            hit_wx = robot.x + us_sensor.measured_distance * math.cos(ray_angle)
            hit_wy = robot.y + us_sensor.measured_distance * math.sin(ray_angle)
            
            end_col, end_row = self.world_to_cell(hit_wx, hit_wy)
            end_col = max(0, min(end_col, GRID_WIDTH - 1))
            end_row = max(0, min(end_row, GRID_HEIGHT - 1))

            ray_path = self.get_line_cells(start_col, start_row, end_col, end_row)

            for cell_c, cell_r in ray_path[:-1]:
                if 0 <= cell_c < GRID_WIDTH and 0 <= cell_r < GRID_HEIGHT:
                    self.cells[cell_r][cell_c] += L_FREE

            if us_sensor.measured_distance < RAY_RANGE:
                final_c, final_r = ray_path[-1]
                if 0 <= final_c < GRID_WIDTH and 0 <= final_r < GRID_HEIGHT:
                    self.cells[final_r][final_c] += L_OCC

            for cell_c, cell_r in ray_path:
                if 0 <= cell_c < GRID_WIDTH and 0 <= cell_r < GRID_HEIGHT:
                    self.hazard_cell[cell_r][cell_c] = env_map.cell_type(cell_r, cell_c)

            ray_angle += angle_step

    def update_from_robot(self, robot, env_map):
        for sensor in robot.sensors:
            if hasattr(sensor, 'cols') and hasattr(sensor, 'depth_grid'):
                self.update_from_tos_sensor(env_map, robot, sensor)
            else:
                self.update_map_from_ultrasonic(env_map, robot, sensor)

    def render(self, screen):
        """
        Renders the occupancy map with high-visibility solid colors 
        for hazards so they don't get swallowed by fine grid resolutions.
        """
        half_w = (GRID_WIDTH * GRID_CELL_SIZE) / 2
        half_h = (GRID_HEIGHT * GRID_CELL_SIZE) / 2

        for row in range(GRID_HEIGHT):
            for col in range(GRID_WIDTH):
                # 1. Project world coordinates to screen rect
                cell_wx = (col * GRID_CELL_SIZE) - half_w
                cell_wy = half_h - (row * GRID_CELL_SIZE)
                
                sx1, sy1 = WorldToScreen(cell_wx, cell_wy, PPM, SCREEN_WIDTH, SCREEN_HEIGH)
                sx2, sy2 = WorldToScreen(cell_wx + GRID_CELL_SIZE, cell_wy - GRID_CELL_SIZE, PPM, SCREEN_WIDTH, SCREEN_HEIGH)
                
                width = sx2 - sx1
                height = sy2 - sy1
                cell_rect = pygame.Rect(sx1, sy1, width, height)

                # 2. Check hazard states first (String & Integer Safe)
                hazard = self.hazard_cell[row][col]
                hazard_str = str(hazard).lower()

                is_fire = (hazard == FIRE or hazard_str == 'fire' or hazard == 2)
                is_victim = (hazard == VICTIM or hazard_str == 'victim' or hazard == 3)
                is_collapse = (hazard == COLLAPSE_ZONE or hazard_str == 'collapse_zone' or hazard == 4)

                # 3. Render Logic: Hazards completely paint over the cell for high visibility
                if is_fire:
                    pygame.draw.rect(screen, (255, 60, 60), cell_rect)  # Solid Bright Red
                elif is_victim:
                    pygame.draw.rect(screen, (60, 255, 60), cell_rect)  # Solid Bright Green
                elif is_collapse:
                    pygame.draw.rect(screen, (255, 150, 0), cell_rect) # Solid Orange
                else:
                    # No hazard? Draw standard grayscale occupancy tracking
                    raw_log_odds = self.cells[row][col]
                    clamped_log_odds = max(-20.0, min(20.0, raw_log_odds))
                    prob = 1.0 / (1.0 + math.exp(-clamped_log_odds))

                    gray_intensity = int((1.0 - prob) * 255)
                    base_color = (gray_intensity, gray_intensity, gray_intensity)
                    pygame.draw.rect(screen, base_color, cell_rect)

                # 4. Draw subtle grid borders (use a faint color so it doesn't distract)
                pygame.draw.rect(screen, (50, 50, 50), cell_rect, 1)