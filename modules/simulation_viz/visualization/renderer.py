import pygame

from constants import TILE_WIDTH, TILE_HEIGHT
from visualization.isometric import grid_to_screen


class Renderer:

    def __init__(self, screen):
        self.screen = screen

    def draw_tile(self, row, col, camera):

        # Convert grid coordinates to world coordinates
        x, y = grid_to_screen(row, col)

        # Apply camera position
        x, y = camera.apply(x, y)

        # Define diamond corners
        points = [
            (x, y),
            (x + TILE_WIDTH // 2, y + TILE_HEIGHT // 2),
            (x, y + TILE_HEIGHT),
            (x - TILE_WIDTH // 2, y + TILE_HEIGHT // 2)
        ]

        # Draw tile
        pygame.draw.polygon(
            self.screen,
            (120, 170, 120),
            points
        )

        # Draw outline
        pygame.draw.polygon(
            self.screen,
            (40, 40, 40),
            points,
            2
        )