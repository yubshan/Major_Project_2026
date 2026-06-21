import pygame
import math
from utils import MeterToPixel, WorldToScreen
from config import ROBOT_MAX_SPEED, ROBOT_MAX_TURNING_SPEED, PPM, SCREEN_HEIGH, SCREEN_WIDTH, ROBOT_CONFIG, RAY_RANGE
from core.kinematics import ForwardKinematics

class Robot:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.turnDegree = 0
        self.LinearVelocity = 0
        self.AngulatVelocity = 0
        self.moveSpeed = ROBOT_MAX_SPEED
        self.turnSpeed = ROBOT_MAX_TURNING_SPEED
        self.rayRange = RAY_RANGE

    def update(self, dt):
        keys = pygame.key.get_pressed()
        

        self.LinearVelocity = 0
        self.AngularVelocity = 0  
        
        if keys[pygame.K_UP]:
            self.LinearVelocity = self.moveSpeed
        elif keys[pygame.K_DOWN]:
            self.LinearVelocity = -self.moveSpeed
            
        if keys[pygame.K_LEFT]:
            self.AngularVelocity = self.turnSpeed
        elif keys[pygame.K_RIGHT]:
            self.AngularVelocity = -self.turnSpeed
            
        x_update_by, y_update_by, turned_by = ForwardKinematics(
            self.LinearVelocity, self.AngularVelocity, self.turnDegree, dt
        )
        
        self.x += x_update_by
        self.y += y_update_by
        self.turnDegree += turned_by


    def render (self):
        screen = pygame.display.get_surface()
        ##robot dimension in meter
        robot_width_m = ROBOT_CONFIG["robot_dimension"]["width"]
        robot_height_m = ROBOT_CONFIG["robot_dimension"]["height"]
        chasis_width_m = ROBOT_CONFIG["robot_chasis"]["width"]
        chasis_height_m = ROBOT_CONFIG["robot_chasis"]["height"]
        wheel_width_m = ROBOT_CONFIG["robot_wheel"]["width"]
        wheel_height_m = ROBOT_CONFIG["robot_wheel"]["height"]

        ## robot dimensions to pixel
        #dimension 
        robot_width_px, robot_height_px =  MeterToPixel(robot_width_m, robot_height_m, PPM )
        #chasis
        chasis_width_px, chasis_height_px = MeterToPixel(chasis_width_m,chasis_height_m, PPM)
        #wheel 
        wheel_width_px, wheel_height_px = MeterToPixel(wheel_width_m, wheel_height_m, PPM)
        # rescue symbol
        c_l, c_b = 16, 6

         ## robot colors
        wheel_color = (45, 45, 45)   #gray
        chasis_color = (255, 90, 0) #yellow
        white= (255,255, 255)

         ## robot surface
        combined_object = pygame.Surface((robot_width_px,robot_height_px), pygame.SRCALPHA)

        ## robot component position on robot surface
        chasis_x = (robot_width_px // 2 - chasis_width_px // 2 )
        chasis_y = (robot_height_px // 2 - chasis_height_px // 2 )
        l_wheel_x = chasis_x - int(wheel_width_px)
        lr_wheel_y = ((robot_height_px//2) - (wheel_height_px // 2))
        r_wheel_x = chasis_x + int(chasis_width_px)
        line_x = (chasis_x + int(chasis_width_px) // 2 ) - c_b // 2
        line_y = (chasis_y + int(chasis_height_px) // 2 )  - c_l // 2

        ## Robot Graphics
        #mainBody
        pygame.draw.rect(combined_object, chasis_color, (chasis_x, chasis_y, chasis_width_px, chasis_height_px), border_radius=6)
        
        # #Two wheel
        pygame.draw.rect(combined_object, wheel_color, (l_wheel_x, lr_wheel_y ,wheel_width_px, wheel_height_px), border_radius=3)
        pygame.draw.rect(combined_object, wheel_color, (r_wheel_x, lr_wheel_y  ,wheel_width_px, wheel_height_px), border_radius=3)

        # #rescue symbol 
        pygame.draw.rect(combined_object, white, (line_x, line_y, c_b, c_l)) #vertical bar
        pygame.draw.rect(combined_object, white, (line_y, line_x, c_l, c_b)) # Horizontal bar


        ## Rotate surface
        heading_degree = math.degrees(self.turnDegree) - 90
        rotated_surface = pygame.transform.rotate(combined_object, heading_degree)

        screen_x , screen_y = WorldToScreen(self.x, self.y,PPM, SCREEN_WIDTH, SCREEN_HEIGH)
        new_rect = rotated_surface.get_rect(center=(screen_x, screen_y))
    
        

        screen.blit(rotated_surface, new_rect)