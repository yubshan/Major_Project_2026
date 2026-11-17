
from pathlib import Path
import sys
import pygame

from simulation.map_loader import MapLoader
from config import *
from constants import *
from visualization.renderer import Renderer
from visualization.camera import Camera


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

running = True

# Main game loop
while running:

    dt = clock.tick(FPS) / 1000

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Camera movement
    keys = pygame.key.get_pressed()
    camera.update(keys, dt)

       # Clear screen
    screen.fill(BACKGROUND_COLOR)

    # Render map from JSON data
    for row in range(map_data["rows"]):
        for col in range(map_data["cols"]):

            tile_type = map_data["tiles"][row][col]

            # Draw floor underneath every tile
            renderer.draw_tile(row, col, camera)

            # Draw wall on top of floor
            if tile_type == TILE_WALL:
                renderer.draw_wall(row, col, camera)

            # Draw obstacle on top of floor
            elif tile_type == TILE_OBSTACLE:
                renderer.draw_obstacle(row, col, camera)

    # Update display
    pygame.display.flip()


pygame.quit()
sys.exit()

   
