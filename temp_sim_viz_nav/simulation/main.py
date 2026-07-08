import os
import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGH,PPM,ROBOT_CONFIG, ROBOT_MAX_SPEED, ROBOT_MAX_TURNING_SPEED
from core.drawRobot import Robot
from core.map import Map
from core.occupancyGrid import OccupancyGrid

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
occupancy_grid = OccupancyGrid()

show_map = False

pygame.font.init()
try:
    hud_font = pygame.font.SysFont("monospace", 14)
except:
    hud_font = pygame.font.Font(None, 18)

RUNNING = True



while RUNNING:

    dt = clock.tick(60) / 1000.0

    screen.fill((220,220,220))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            RUNNING = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                show_map = not show_map
            if event.key == pygame.K_a:
                robot.autonomousDrive = not robot.autonomousDrive
            
    robot.update(dt, map)

    occupancy_grid.update_from_robot(robot, map)
    
    map.render(screen)
    robot.render_sensors(screen)
    robot.render()

    if show_map:
        occupancy_grid.render(screen)
    
    mode_text = "AUTO" if robot.autonomousDrive else "MANNUAL"
    map_text = "MAP: ON [M]" if show_map else "MAP OFF [M]"

    screen.blit(hud_font.render(f"Drive: {mode_text} [A]",  True, (30,30,30)), (10, 10))
    screen.blit(hud_font.render(f"{map_text}",  True, (30,30,30)), (10, 28))
    screen.blit(hud_font.render(f"Pos: ({robot.x:+.2f}, {robot.y:+.2f})  Heading: {round(robot.turnDegree * 57.3)}°",
                                True, (30, 30, 30)), (10, 46))
    


    pygame.display.update()
    clock.tick(60)

pygame.quit()
