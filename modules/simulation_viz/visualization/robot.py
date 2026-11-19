
import pygame
import math
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

        # Logical grid position
        self.grid_row = grid_row
        self.grid_col = grid_col

        # Visual position
        self.x = float(grid_col)
        self.y = float(grid_row)

        # Target position
        self.target_x = self.x
        self.target_y = self.y

        # Movement settings
        self.move_speed = 3.0
        self.is_moving = False
        self.forward_held = False

    # Rotate robot
    def rotate(self, angle):

        self.angle = angle

        self.image = pygame.transform.rotate(
            self.original_image,
            self.angle
        )

    # Move robot on the grid
    def move(self, row_change, col_change, map_data):

        # Don't accept another movement while moving
        if self.is_moving:
            return

        # Calculate new grid position
        new_row = self.grid_row + row_change
        new_col = self.grid_col + col_change

        # Check map boundaries
        if not (0 <= new_row < map_data["rows"]):
            return

        if not (0 <= new_col < map_data["cols"]):
            return

        # Check destination tile
        tile_type = map_data["tiles"][new_row][new_col]

        if tile_type == TILE_WALL or tile_type == TILE_OBSTACLE:
            return

        # Update logical grid position
        self.grid_row = new_row
        self.grid_col = new_col

        # Set visual destination
        self.target_x = float(new_col)
        self.target_y = float(new_row)

        # Start smooth movement
        self.is_moving = True

        # Rotate based on movement direction
        if row_change == -1:
            self.rotate(0)

        elif row_change == 1:
            self.rotate(180)

        elif col_change == -1:
            self.rotate(90)

        elif col_change == 1:
            self.rotate(270)

    # Turn robot left
    def turn_left(self):

        if self.is_moving:
            return

        self.angle = (self.angle + 90) % 360
        self.rotate(self.angle)

    # Turn robot right
    def turn_right(self):

        if self.is_moving:
            return

        self.angle = (self.angle - 90) % 360
        self.rotate(self.angle)

    # Move robot forward in the direction it faces
    def move_forward(self, map_data):

        if self.angle == 0:
            self.move(-1, 0, map_data)

        elif self.angle == 90:
            self.move(0, -1, map_data)

        elif self.angle == 180:
            self.move(1, 0, map_data)

        elif self.angle == 270:
            self.move(0, 1, map_data)

    # Update smooth robot movement
    def update(self, dt):

        # Stop if robot is not moving
        if not self.is_moving:
            return

        # Calculate distance to target
        dx = self.target_x - self.x
        dy = self.target_y - self.y

        distance = math.hypot(dx, dy)

        # Calculate movement distance for this frame
        step = self.move_speed * dt

        # Check whether destination is reached
        if distance <= step:

            self.x = self.target_x
            self.y = self.target_y

            self.is_moving = False

        else:

            # Move gradually towards destination
            self.x += (dx / distance) * step
            self.y += (dy / distance) * step

    # Draw robot
    def draw(self, screen, camera, grid_to_screen):

        # Convert visual position to screen coordinates
        x, y = grid_to_screen(
            self.y,
            self.x
        )

        # Apply camera movement
        x, y = camera.apply(x, y)

        # Center robot image on tile
        robot_rect = self.image.get_rect(
            center=(x, y + 16)
        )

        # Draw robot
        screen.blit(self.image, robot_rect)
