import math, pygame
from config import RAY_RANGE, PPM, SCREEN_WIDTH, SCREEN_HEIGH
from utils import WorldToScreen

def normalizeAngle(angle):
    angle = angle % (2 * math.pi)
    if angle < 0:
        angle = (2 * math.pi) + angle 
    return angle

class Ray:
    def __init__(self, angle, robot):
        self.rayAngle = normalizeAngle(angle)
        self.robot = robot
        self.rayRange = RAY_RANGE 

    def cast(self, grid):
        step_size = 0.05 
        current_dist = 0.0
        
        while current_dist < RAY_RANGE:
            check_x = self.robot.x + current_dist * math.cos(self.rayAngle)
            check_y = self.robot.y + current_dist * math.sin(self.rayAngle)
            
            
            if grid.is_obstacle(check_x, check_y):
                self.rayRange = current_dist 
                return
                
            current_dist += step_size
            
        self.rayRange = RAY_RANGE 

    def render(self, screen):
        ray_world_x = self.robot.x + self.rayRange * math.cos(self.rayAngle)
        ray_world_y = self.robot.y + self.rayRange * math.sin(self.rayAngle)
       
        screen_robot_x, screen_robot_y = WorldToScreen(self.robot.x, self.robot.y, PPM, SCREEN_WIDTH, SCREEN_HEIGH)
        screen_ray_end_x, screen_ray_end_y = WorldToScreen(ray_world_x, ray_world_y, PPM, SCREEN_WIDTH, SCREEN_HEIGH)
        
        ray_color = (255, 0, 0) 
        pygame.draw.line(screen, ray_color, (screen_robot_x, screen_robot_y), (screen_ray_end_x, screen_ray_end_y), 1)