
import pygame
from pathlib import Path


class Robot:

    def __init__(self, image_path, grid_row=2, grid_col=2):

        # Load robot image
        self.image = pygame.image.load(
            str(image_path)
        ).convert_alpha()

        # Resize robot image
        self.image = pygame.transform.scale(
            self.image,
            (48, 48)
        )

        # Initial grid position
        self.grid_row = grid_row
        self.grid_col = grid_col

    def draw(self, screen, camera, grid_to_screen):

        # Convert grid position to screen coordinates
        x, y = grid_to_screen(
            self.grid_row,
            self.grid_col
        )

        # Apply camera movement
        x, y = camera.apply(x, y)

        # Center robot image on tile
        robot_rect = self.image.get_rect(
            center=(x, y + 16)
        )

        # Draw robot
        screen.blit(self.image, robot_rect)
