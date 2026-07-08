import pygame
from config import *
from utils import WorldToScreen
from core.ray import Ray

class UltrasonicSensor:
    def __init__(self, robot, offset_angle, firing_round):
        self.offset_angle = offset_angle * math.pi / 180 #randian
        self.robot = robot
        self.firing_round = firing_round
        self.measured_distance = RAY_RANGE
    
    def sense(self, grid, current_round):
        if current_round != self.firing_round:
            return self.measured_distance
        center_angle = self.robot.turnDegree + self.offset_angle
        ray_angle = center_angle - (FOV/2 )
        angle_step = FOV / (ULTRASONIC_NUM_RAYS - 1) if ULTRASONIC_NUM_RAYS > 1 else 0

        closest_hit = RAY_RANGE

        for i in range(ULTRASONIC_NUM_RAYS):
            ray = Ray(ray_angle, self.robot)
            ray.cast(grid)

            if ray.rayRange < closest_hit:
                closest_hit = ray.rayRange
            ray_angle += angle_step
        
        if closest_hit < 0.02:
            self.measured_distance = 0.02
        else:
            self.measured_distance = closest_hit

        return self.measured_distance 

    
    def render(self, screen):
        center_angle = self.robot.turnDegree + self.offset_angle
        
        robot_x, robot_y = WorldToScreen(self.robot.x, self.robot.y, PPM, SCREEN_WIDTH, SCREEN_HEIGH)
        
        hit_w_x = self.robot.x + self.measured_distance * math.cos(center_angle)
        hit_w_y = self.robot.y + self.measured_distance * math.sin(center_angle)
        hit_x, hit_y = WorldToScreen(hit_w_x, hit_w_y, PPM, SCREEN_WIDTH, SCREEN_HEIGH)

        color = (0, 255, 0) if self.measured_distance >= CRITICAL_DISTANCE else (255, 0, 0)
        pygame.draw.line(screen, color, (robot_x, robot_y), (hit_x, hit_y), 2)

        for edge_angle in [center_angle - FOV/2, center_angle + FOV/2]:
            edge_w_x = self.robot.x + self.measured_distance * math.cos(edge_angle)
            edge_w_y = self.robot.y + self.measured_distance * math.sin(edge_angle)
            edge_x, edge_y = WorldToScreen(edge_w_x, edge_w_y, PPM, SCREEN_WIDTH, SCREEN_HEIGH)
            pygame.draw.line(screen, (100, 100, 100), (robot_x, robot_y), (edge_x, edge_y), 1)