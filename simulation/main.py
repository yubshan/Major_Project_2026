import os 
import pygame
import math

# --- 1. SIMULATION SCALE AND SETUP ---
PPM = 150  # Pixels Per Meter (1 meter = 150 pixels)

pygame.init()
screen = pygame.display.set_mode((800, 800))
pygame.display.set_caption("Autonomous-Rescue-Robot-Simulator")
clock = pygame.time.Clock()

# --- 2. ROBOT PHYSICAL STATE (In Meters and Radians) ---
# Start the robot at the world center (0, 0)
world_x = 0.0      
world_y = 0.0
theta = 0.0        # Orientation angle in radians (0 means facing East/Right)

# Robot control speeds
linear_velocity = 0.0   # Forward/backward speed (meters per second)
angular_velocity = 0.0  # Turning speed (radians per second)

# Max capabilities of our motors
MAX_LINEAR_SPEED = 1.2   # 1.2 meters per second forward
MAX_TURNING_SPEED = 3.0  # 3.0 radians per second rotation

def drawRobot(w_x, w_y, heading_rad):
    # Create the unrotated base model surface (facing up by default in your design)
    # To align with math standard (0 rad = East/Right), we design it facing Right, 
    # or we adjust the rotation angle. Let's adjust the angle for your exact sprite design.
    base_surface = pygame.Surface((60, 60), pygame.SRCALPHA)

    wheel_color = (45, 45, 45)   
    chasis_color = (255, 90, 0) 
    white = (255, 255, 255)

    # Your custom drawing shapes
    pygame.draw.rect(base_surface, wheel_color, (2, 4, 10, 52), border_radius=3)
    pygame.draw.rect(base_surface, wheel_color, (48, 4, 10, 52), border_radius=3)
    pygame.draw.rect(base_surface, chasis_color, (12, 8, 36, 44), border_radius=6)
    pygame.draw.rect(base_surface, white, (27, 22, 6, 16)) 
    pygame.draw.rect(base_surface, white, (22, 27, 16, 6)) 

    # Pygame rotates counter-clockwise in degrees.
    # Your original drawing faces "Up" (-Y in screen space), which is mathematically +90 degrees.
    # We subtract 90 to align your graphic perfectly with the physics engine direction.
    heading_degrees = math.degrees(heading_rad) - 90
    rotated_surface = pygame.transform.rotate(base_surface, heading_degrees)

    # Convert real-world meters to screen coordinates (Origin at screen center 400, 400)
    screen_x = int(400 + w_x * PPM)
    screen_y = int(400 - w_y * PPM) # Negative because screen Y goes down, world Y goes up

    # Get the bounding rectangle of the rotated surface and center it on our coordinates
    # This prevents the robot from wobbling violently when it spins
    new_rect = rotated_surface.get_rect(center=(screen_x, screen_y))
    
    screen.blit(rotated_surface, new_rect.topleft)


RUNNING = True

while RUNNING:
    screen.fill((240, 240, 240))

    # Calculate delta time dynamically (seconds passed since last frame)
    # clock.tick(60) limits frame rate, and returns the milliseconds passed.
    dt = clock.tick(60) / 1000.0 

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            RUNNING = False
            
        # Mapping arrow keys to actual physical steering (Tank Drive style)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                linear_velocity = MAX_LINEAR_SPEED
            if event.key == pygame.K_DOWN:
                linear_velocity = -MAX_LINEAR_SPEED
            if event.key == pygame.K_LEFT:
                angular_velocity = MAX_TURNING_SPEED
            if event.key == pygame.K_RIGHT:
                angular_velocity = -MAX_TURNING_SPEED
    
        if event.type == pygame.KEYUP:
            if event.key in (pygame.K_UP, pygame.K_DOWN):
                linear_velocity = 0.0
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                angular_velocity = 0.0
    
    # --- 3. KINEMATICS ENGINE UPDATE ---
    # Update position based on current heading angle
    world_x += linear_velocity * math.cos(theta) * dt
    world_y += linear_velocity * math.sin(theta) * dt
    
    # Update rotation angle based on turning velocity
    theta += angular_velocity * dt

    # Keep theta wrapped cleanly between -PI and +PI
    theta = math.atan2(math.sin(theta), math.cos(theta))
  
    # --- 4. RENDER ELEMENT ---
    drawRobot(world_x, world_y, theta)
    
    pygame.display.update()

pygame.quit()