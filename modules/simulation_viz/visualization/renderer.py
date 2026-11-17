
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

    def draw_wall(self, row, col, camera):

        # Get isometric screen coordinates
        x, y = grid_to_screen(row, col)
        x, y = camera.apply(x, y)

        # Wall dimensions
        wall_height = 48

        half_width = TILE_WIDTH // 2
        half_height = TILE_HEIGHT // 2

        # Bottom diamond corners
        right = (x + half_width, y + half_height)
        bottom = (x, y + TILE_HEIGHT)
        left = (x - half_width, y + half_height)

        # Top diamond corners
        top_up = (x, y - wall_height)
        right_up = (x + half_width, y + half_height - wall_height)
        bottom_up = (x, y + TILE_HEIGHT - wall_height)
        left_up = (x - half_width, y + half_height - wall_height)

        # Left visible face
        pygame.draw.polygon(
            self.screen,
            (105, 110, 120),
            [left, bottom, bottom_up, left_up]
        )

        # Right visible face
        pygame.draw.polygon(
            self.screen,
            (75, 80, 90),
            [bottom, right, right_up, bottom_up]
        )

        # Top face
        pygame.draw.polygon(
            self.screen,
            (155, 160, 170),
            [top_up, right_up, bottom_up, left_up]
        )

        # Draw outlines
        pygame.draw.polygon(
            self.screen,
            (35, 35, 40),
            [left, bottom, right, right_up, top_up, left_up],
            2
        )

    def draw_obstacle(self, row, col, camera):

        # Get isometric screen coordinates
        x, y = grid_to_screen(row, col)
        x, y = camera.apply(x, y)

        obstacle_height = 24

        half_width = TILE_WIDTH // 2
        half_height = TILE_HEIGHT // 2

        # Bottom diamond corners
        left = (x - half_width, y + half_height)
        bottom = (x, y + TILE_HEIGHT)
        right = (x + half_width, y + half_height)

        # Raised corners
        left_up = (left[0], left[1] - obstacle_height)
        bottom_up = (bottom[0], bottom[1] - obstacle_height)
        right_up = (right[0], right[1] - obstacle_height)
        top_up = (x, y - obstacle_height)

        # Left face
        pygame.draw.polygon(
            self.screen,
            (180, 100, 50),
            [left, bottom, bottom_up, left_up]
        )

        # Right face
        pygame.draw.polygon(
            self.screen,
            (140, 70, 35),
            [bottom, right, right_up, bottom_up]
        )

        # Top face
        pygame.draw.polygon(
            self.screen,
            (230, 150, 80),
            [top_up, right_up, bottom_up, left_up]
        )
