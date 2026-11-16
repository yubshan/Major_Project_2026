import sys
import pygame

print("1. Python started")

from config import *
from constants import *
from visualization.renderer import Renderer
from visualization.camera import Camera

print("2. Modules imported")

pygame.init()
print("3. Pygame initialized")

screen = pygame.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT)
)

pygame.display.set_caption(WINDOW_TITLE)

print("4. Display created")

clock = pygame.time.Clock()

renderer = Renderer(screen)

camera = Camera(
    offset_x=600,
    offset_y=100,
    speed=400
)

print("5. Renderer and camera created")

running = True

while running:

    dt = clock.tick(FPS) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    camera.update(keys, dt)

    screen.fill(BACKGROUND_COLOR)

    for row in range(MAP_ROWS):
        for col in range(MAP_COLS):
            renderer.draw_tile(row, col, camera)

    pygame.display.flip()

pygame.quit()
sys.exit()