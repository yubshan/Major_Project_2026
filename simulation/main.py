import os
import pygame
import math
from config import screen_width, screen_height, robot_config, ppm, robot_max_speed, robot_max_turning_speed
from core.drawRobot import DrawRobot
from core.kinematics import ForwardKinematics
current_dir = os.path.dirname(__file__)
logo_image_path = os.path.join(current_dir, "assets", "logo.bmp")

pygame.init()



screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Autonomous-Rescue-Robot-Simulator")

# Create a clock object to control the frame rate safely
clock = pygame.time.Clock()

try:
    app_icon = pygame.image.load(logo_image_path)
    app_icon_scaled = pygame.transform.scale(app_icon, (32, 32))
    pygame.display.set_icon(app_icon_scaled)
except pygame.error as e:
    print(f"Warning: The Error we got: {e}")
    print("using default window icon.")


RUNNING = True
ROBOT_X_POSITION = 0
ROBOT_Y_POSITION = 0
ROBOT_TURNING_DEGREE = 0


LINEAR_VELOCITY = 0
ANGULAR_VELOCITY = 0


while RUNNING:
    screen.fill((240, 240, 240))
    dt = clock.tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            RUNNING = False
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                LINEAR_VELOCITY = robot_max_speed
            if event.key == pygame.K_DOWN:
                LINEAR_VELOCITY = -robot_max_speed
            if event.key == pygame.K_LEFT:
                ANGULAR_VELOCITY = robot_max_turning_speed
            if event.key == pygame.K_RIGHT:
                ANGULAR_VELOCITY = -robot_max_turning_speed
    
        if event.type == pygame.KEYUP:
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                ANGULAR_VELOCITY = 0
            if event.key in (pygame.K_UP, pygame.K_DOWN):
                LINEAR_VELOCITY = 0
    
    x_update_by, y_update_by, turned_by = ForwardKinematics(LINEAR_VELOCITY, ANGULAR_VELOCITY, ROBOT_TURNING_DEGREE, dt)
    ROBOT_X_POSITION += x_update_by
    ROBOT_Y_POSITION += y_update_by
    ROBOT_TURNING_DEGREE += turned_by
  
    DrawRobot(ROBOT_X_POSITION, ROBOT_Y_POSITION,ROBOT_TURNING_DEGREE, ppm, screen_width, screen_height, robot_config)
    
    pygame.display.update()
    
    clock.tick(60)

pygame.quit()
