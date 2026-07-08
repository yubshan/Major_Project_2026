import sys
import pygame

from config import *
from constants import *
from visualization.renderer import Renderer

pygame.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(WINDOW_TITLE)

clock = pygame.time.Clock()

renderer = Renderer(screen)

running = True

while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BACKGROUND_COLOR)

    # Draw the floor
    for row in range(MAP_ROWS):
        for col in range(MAP_COLS):
            renderer.draw_tile(row, col)

    pygame.display.flip()

    clock.tick(FPS)

pygame.quit()
sys.exit()