
from pathlib import Path
import sys
import pygame

from simulation.map_loader import MapLoader
from config import *
from constants import *
from visualization.renderer import Renderer
from visualization.camera import Camera
from visualization.robot import Robot
from visualization.isometric import grid_to_screen


# Load map data
BASE_DIR = Path(__file__).resolve().parent
map_path = BASE_DIR / "assets" / "maps" / "level1.json"

map_loader = MapLoader(map_path)
map_data = map_loader.load_map()

print("Map loaded successfully!")
print("Map name:", map_data["name"])
print("Rows:", map_data["rows"])
print("Columns:", map_data["cols"])


# Initialize Pygame
pygame.init()

screen = pygame.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT)
)

pygame.display.set_caption(WINDOW_TITLE)

clock = pygame.time.Clock()

renderer = Renderer(screen)

camera = Camera(
    offset_x=600,
    offset_y=100,
    speed=400
)
# Initialize rescue robot
robot_image_path = BASE_DIR / "assets" / "robot" / "robot.png"

robot = Robot(
    robot_image_path,
    grid_row=1,
    grid_col=1
)
print("Starting position:", robot.grid_row, robot.grid_col)
robot.rotate(0)




running = True

# Main game loop
while running:

    dt = clock.tick(FPS) / 1000

   
    
    # Handle events
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_i:
                robot.forward_held = True

            elif event.key == pygame.K_j:
                robot.turn_left()

            elif event.key == pygame.K_l:
                robot.turn_right()

        elif event.type == pygame.KEYUP:

            if event.key == pygame.K_i:
                robot.forward_held = False


    # Get keyboard input
    keys = pygame.key.get_pressed()

    # Camera movement using WASD
    camera.update(keys, dt)
    # Update robot smooth movement
    robot.update(dt)
    # Continue moving while I is held
    if robot.forward_held and not robot.is_moving:
     robot.move_forward(map_data)

    # Clear screen
    screen.fill(BACKGROUND_COLOR)

    # Render map
    for row in range(map_data["rows"]):
        for col in range(map_data["cols"]):

            tile_type = map_data["tiles"][row][col]

            renderer.draw_tile(row, col, camera)

            if tile_type == TILE_WALL:
                renderer.draw_wall(row, col, camera)

            elif tile_type == TILE_OBSTACLE:
                renderer.draw_obstacle(row, col, camera)

    # Draw rescue robot
    robot.draw(screen, camera, grid_to_screen)

    # Display robot grid position
    font = pygame.font.SysFont(None, 28)

    position_text = font.render(
        f"Robot Position: ({robot.grid_row}, {robot.grid_col})",
        True,
        (255, 255, 255)
    )

    screen.blit(position_text, (20, 20))

    # Update display
    pygame.display.flip()

pygame.quit()
sys.exit()


