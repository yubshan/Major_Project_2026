
import pygame
from constants import TILE_WALL, TILE_OBSTACLE


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

        # Store original image for rotation
        self.original_image = self.image.copy()

        # Initial rotation angle
        self.angle = 0

        # Initial grid position
        self.grid_row = grid_row
        self.grid_col = grid_col

    # Rotate robot
    def rotate(self, angle):

        self.angle = angle

        self.image = pygame.transform.rotate(
            self.original_image,
            self.angle
        )
    
    # Move robot on the grid
    def move(self, row_change, col_change, map_data):

        # Calculate new grid position
        new_row = self.grid_row + row_change
        new_col = self.grid_col + col_change

        # Check map boundaries
        if not (0 <= new_row < map_data["rows"]):
            return

        if not (0 <= new_col < map_data["cols"]):
            return

        # Check whether the destination tile is blocked
        tile_type = map_data["tiles"][new_row][new_col]

        if tile_type == TILE_WALL or tile_type == TILE_OBSTACLE:
            return

        # Update robot position
        self.grid_row = new_row
        self.grid_col = new_col
    

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
