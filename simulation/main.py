import os
import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGH,PPM,ROBOT_CONFIG, ROBOT_MAX_SPEED, ROBOT_MAX_TURNING_SPEED
from core.drawRobot import Robot
from core.kinematics import ForwardKinematics
from core.drawMaze import drawMaze1
current_dir = os.path.dirname(__file__)
logo_image_path = os.path.join(current_dir, "assets", "logo.bmp")

pygame.init()



screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGH))
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

robot =  Robot()

RUNNING = True



while RUNNING:
    screen.fill((240, 240, 240))
    dt = clock.tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            RUNNING = False
            
    robot.update(dt)
    robot.render( )
    drawMaze1()
    pygame.display.update()
    
    clock.tick(60)

pygame.quit()
