import os
import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGH,PPM,ROBOT_CONFIG, ROBOT_MAX_SPEED, ROBOT_MAX_TURNING_SPEED
from core.drawRobot import Robot
from core.rayCaster import RayCaster
from core.map import Map

current_dir = os.path.dirname(__file__)
logo_image_path = os.path.join(current_dir, "assets", "logo.bmp")

pygame.init()



screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGH))
pygame.display.set_caption("Autonomous-Rescue-Robot-Simulator")


clock = pygame.time.Clock()

try:
    app_icon = pygame.image.load(logo_image_path)
    app_icon_scaled = pygame.transform.scale(app_icon, (32, 32))
    pygame.display.set_icon(app_icon_scaled)
except pygame.error as e:
    print(f"Warning: The Error we got: {e}")
    print("using default window icon.")

map = Map()
robot =  Robot()
raycaster = RayCaster(robot)

RUNNING = True



while RUNNING:
    screen.fill((240, 240, 240))
    dt = clock.tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            RUNNING = False
            
    robot.update(dt)
    raycaster.castAllRays(map)


    map.render(screen)
    robot.render()

    raycaster.render(screen)
    pygame.display.update()
    clock.tick(60)

pygame.quit()
