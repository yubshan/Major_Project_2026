import pygame

from constants import TILE_WIDTH, TILE_HEIGHT
from visualization.isometric import grid_to_screen


class Renderer:
    def __init__(self, screen):
        self.screen = screen

    def draw_tile(self, row, col, offset_x=600, offset_y=100):
        """
        Draw one isometric tile.
        """

        x, y = grid_to_screen(row, col)

        x += offset_x
        y += offset_y

        points = [
            (x, y),
            (x + TILE_WIDTH // 2, y + TILE_HEIGHT // 2),
            (x, y + TILE_HEIGHT),
            (x - TILE_WIDTH // 2, y + TILE_HEIGHT // 2),
        ]

        pygame.draw.polygon(
            self.screen,
            (120, 170, 120),
            points
        )

        pygame.draw.polygon(
            self.screen,
            (40, 40, 40),
            points,
            2
        )