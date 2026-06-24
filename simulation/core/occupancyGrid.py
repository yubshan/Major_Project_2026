import math
import pygame 
from config import *
from utils import WorldToScreen

UNKNOWN = 0.5
FREE = 0.0
OCCUPIED = 1.0

FREE_WEIGHT = 0.06
OCCUPIED_WEIGHT= 0.40  

FREE_THRESHOLD = 0.28
OCCUPIED_THRESHOLD = 0.75

OVERLAY_ALPHA = 200  # transparent- 0 opaque - 255


class OccupancyGrid:
    def __init__(self):
        self.cells = [
            [UNKNOWN] * GRID_WIDTH 
            for _ in range(GRID_HEIGHT)
        ]
        self.surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGH), pygame.SRCALPHA)
        self.dirty = True
    

    def update_from_robot(self, robot, env_map):
        for sensor in robot.sensors:
            # 1. Time-of-Flight Sensor (Fires every frame)
            if hasattr(sensor, "cols") and hasattr(sensor, "depth_grid"):
                center_angle = robot.turnDegree + sensor.offset_angle
                start_angle = center_angle - sensor.fov / 2.0

                for col in range(sensor.cols):
                    ray_angle = start_angle + (0.5 + col) * sensor.zone_angle
                    hit_distance = sensor.depth_grid[0][col]

                    is_hit = hit_distance < sensor.max_range

                    self.trace_ray(robot.x, robot.y, ray_angle, hit_distance, mark_occupied=is_hit,
                                    f_weight=0.04, o_weight=0.50, max_r=sensor.max_range)
            # 2. Ultrasonic Sensors (Sequenced Round Robin Firing)
            else:
                if robot.current_round != sensor.firing_round:
                    continue

                center_angle = robot.turnDegree + sensor.offset_angle
                hit_distance = sensor.measured_distance

                is_valid_hit = hit_distance < (RAY_RANGE - 0.05)
                ray_angle = center_angle - FOV/2
                angle_step = FOV / (ULTRASONIC_NUM_RAYS - 1) if ULTRASONIC_NUM_RAYS > 1 else 0

                for i in range(ULTRASONIC_NUM_RAYS):
                    is_center_ray = (i == ULTRASONIC_NUM_RAYS // 2)

                    self.trace_ray(robot.x, robot.y, ray_angle, hit_distance, mark_occupied=(is_center_ray and is_valid_hit),
                                   f_weight=0.01, o_weight=0.25, max_r=RAY_RANGE)
                    ray_angle += angle_step
        self.dirty = True


    def trace_ray(self, origin_x, origin_y, angle, hit_distance, mark_occupied=True, f_weight=0.06, o_weight=0.40, max_r=RAY_RANGE):
        origin_col, origin_row = self.world_to_cell(origin_x, origin_y)
        hit_x = origin_x + hit_distance * math.cos(angle)
        hit_y = origin_y + hit_distance * math.sin(angle)
        hit_col, hit_row = self.world_to_cell(hit_x, hit_y)

        ray_cells = self.bersenham_calculation(origin_col, origin_row, hit_col, hit_row)

        for i, (col, row) in enumerate(ray_cells):
            if 0 <= col < GRID_WIDTH and 0 <= row < GRID_HEIGHT:
                dist_to_hit = len(ray_cells) - i
                # Clears completely up to the boundary cell edge
                if dist_to_hit > 1:
                    self.update_cell(row, col, FREE, f_weight)

        ray_hit_obstacle = hit_distance < (max_r - 0.05)
        if mark_occupied and ray_hit_obstacle:
            if 0 <= hit_col < GRID_WIDTH and 0 <= hit_row < GRID_HEIGHT:
                self.update_cell(hit_row, hit_col, OCCUPIED, o_weight)


    def update_cell(self, row, col, new_value, weight):
        current = self.cells[row][col]
        updated = current * (1.0 - weight) + new_value * weight
        self.cells[row][col] = max(0.05, min(0.95, updated))


    def bersenham_calculation(self, c0, r0, c1, r1):
        cells = []
        dc = abs(c1 - c0)
        dr = abs(r1 - r0)
        sc = 1 if c0 < c1 else -1
        sr = 1 if r0 < r1 else -1
        err = dc - dr
 
        c, r = c0, r0

        while True:
            if c == c1 and r == r1:
                break
            cells.append((c, r))
            e2 = 2 * err
            if e2 > -dr:
                err -= dr
                c += sc
            if e2 < dc:
                err += dc
                r += sr
 
        return cells


    def world_to_cell(self, world_x, world_y):
        half_w = (GRID_WIDTH * GRID_CELL_SIZE) // 2
        half_h = (GRID_HEIGHT * GRID_CELL_SIZE) // 2

        col = int((world_x + half_w) / GRID_CELL_SIZE)
        row = int((half_h - world_y) / GRID_CELL_SIZE)
        return col, row

    def render(self, screen):
        if self.dirty == True:
            self.redraw_surface()
            self.dirty = False
        screen.blit(self.surface, (0, 0))

    def redraw_surface(self):
        self.surface.fill((0, 0, 0, 0))

        cell_px = int(GRID_CELL_SIZE * PPM)

        for row in range(GRID_HEIGHT):
            for col in range(GRID_WIDTH):
                value = self.cells[row][col]

                if value < FREE_THRESHOLD:
                    color = (240, 240, 240, OVERLAY_ALPHA)
                elif value > OCCUPIED_THRESHOLD and self._is_supported_occupied(row, col):
                    color = (40, 40, 40, OVERLAY_ALPHA)
                else:
                    color = (160, 160, 160, OVERLAY_ALPHA)  

                # Convert grid cell centre to world, then to screen
                half_w = (GRID_WIDTH * GRID_CELL_SIZE) / 2
                half_h = (GRID_HEIGHT * GRID_CELL_SIZE) / 2
 
                world_x = (col * GRID_CELL_SIZE) - half_w + GRID_CELL_SIZE / 2
                world_y = half_h - (row * GRID_CELL_SIZE) - GRID_CELL_SIZE / 2
 
                scr_x, scr_y = WorldToScreen(world_x, world_y, PPM, SCREEN_WIDTH, SCREEN_HEIGH)
 
                pygame.draw.rect(
                    self.surface, color,
                    (scr_x - cell_px // 2,
                     scr_y - cell_px // 2,
                     cell_px, cell_px)
                )

    def _is_supported_occupied(self, row, col):
        neighbour_count = 0
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if 0 <= nr < GRID_HEIGHT and 0 <= nc < GRID_WIDTH:
                    if self.cells[nr][nc] > OCCUPIED_THRESHOLD:
                        neighbour_count += 1
        return neighbour_count >= 2


    def get_belief(self, world_x: float, world_y: float) -> float:
        col, row = self.world_to_cell(world_x, world_y)
        if 0 <= col < GRID_WIDTH and 0 <= row < GRID_HEIGHT:
            return self.cells[row][col]
        return UNKNOWN

    def is_known_free(self, world_x: float, world_y: float) -> bool:
        return self.get_belief(world_x, world_y) < FREE_THRESHOLD

    def is_known_occupied(self, world_x: float, world_y: float) -> bool:
        return self.get_belief(world_x, world_y) > OCCUPIED_THRESHOLD