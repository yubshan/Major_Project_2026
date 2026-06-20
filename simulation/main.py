import os
import pygame
import math
from config import screen_width, screen_height, robot_config, ppm

current_dir = os.path.dirname(__file__)
logo_image_path = os.path.join(current_dir, "assets", "logo.bmp")

pygame.init()



screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Autonomous-Rescue-Robot-Simulator")

# Create a clock object to control the frame rate safely
clock = pygame.time.Clock()

try:
    app_icon = pygame.image.load(logo_image_path)
    app_icon_scaled = pygame.transform.scale(app_icon, (32, 32))
    pygame.display.set_icon(app_icon_scaled)
except pygame.error as e:
    print(f"Warning: The Error we got: {e}")
    print("using default window icon.")



def MeterToPixel(length, breath, ppm):
    return length * ppm ,  breath * ppm

def WorldToScreen(w_x, w_y, ppm, screen_width, screen_height):
    x_screen = int(ppm * w_x) + screen_width // 2
    y_screen = screen_height // 2 -int(ppm * w_y) 

    return x_screen, y_screen

def ScreenToWorld(s_x, s_y, ppm, screen_width, screen_height):
    x_world = (s_x - screen_width // 2) / ppm
    y_world = (s_y + screen_height // 2) / ppm

    return x_world, y_world

def DrawRobot(x_position, y_position, turningRadius , ppm,screen_width, screen_height, robot_config):

    ##robot dimension in meter
    robot_width_m = robot_config["robot_dimension"]["width"]
    robot_height_m = robot_config["robot_dimension"]["height"]
    chasis_width_m = robot_config["robot_chasis"]["width"]
    chasis_height_m = robot_config["robot_chasis"]["height"]
    wheel_width_m = robot_config["robot_wheel"]["width"]
    wheel_height_m = robot_config["robot_wheel"]["height"]

    
    ## robot dimensions to pixel
    #dimension 
    robot_width_px, robot_height_px =  MeterToPixel(robot_width_m, robot_height_m, ppm )
    #chasis
    chasis_width_px, chasis_height_px = MeterToPixel(chasis_width_m,chasis_height_m, ppm)
    #wheel 
    wheel_width_px, wheel_height_px = MeterToPixel(wheel_width_m, wheel_height_m, ppm)
    # rescue symbol
    c_l, c_b = 16, 6


    ## robot colors
    wheel_color = (45, 45, 45)   #gray
    chasis_color = (255, 90, 0) #yellow
    white= (255,255, 255)

    ## robot surface
    combined_object = pygame.Surface((robot_width_px,robot_height_px), pygame.SRCALPHA)

    ## robot component position on robot surface
    chasis_x = (robot_width_px // 2 - chasis_width_px // 2 )
    chasis_y = (robot_height_px // 2 - chasis_height_px // 2 )
    l_wheel_x = chasis_x - int(wheel_width_px)
    lr_wheel_y = ((robot_height_px//2) - (wheel_height_px // 2))
    r_wheel_x = chasis_x + int(chasis_width_px)
    line_x = (chasis_x + int(chasis_width_px) // 2 ) - c_b // 2
    line_y = (chasis_y + int(chasis_height_px) // 2 )  - c_l // 2

    ## Robot Graphics
    #mainBody
    pygame.draw.rect(combined_object, chasis_color, (chasis_x, chasis_y, chasis_width_px, chasis_height_px), border_radius=6)
    
    # #Two wheel
    pygame.draw.rect(combined_object, wheel_color, (l_wheel_x, lr_wheel_y ,wheel_width_px, wheel_height_px), border_radius=3)
    pygame.draw.rect(combined_object, wheel_color, (r_wheel_x, lr_wheel_y  ,wheel_width_px, wheel_height_px), border_radius=3)

    # #rescue symbol 
    pygame.draw.rect(combined_object, white, (line_x, line_y, c_b, c_l)) #vertical bar
    pygame.draw.rect(combined_object, white, (line_y, line_x, c_l, c_b)) # Horizontal bar


    ## Rotate surface
    heading_degree = math.degrees(turningRadius) - 90
    rotated_surface = pygame.transform.rotate(combined_object, heading_degree)

    screen_x , screen_y = WorldToScreen(x_position, y_position,ppm, screen_width, screen_height)
    new_rect = rotated_surface.get_rect(center=(screen_x, screen_y))
    ##draw the combine model
    
    screen.blit(rotated_surface, new_rect)

RUNNING = True
ROBOT_X_POSITION = 0
ROBOT_Y_POSITION = 0
ROBOT_TURNING_DEGREE = 0


LINEAR_VELOCITY = 0
ANGULAR_VELOCITY = 0


MOVE_SPEED = 2
TURNING_SPEED = 3


while RUNNING:
    screen.fill((240, 240, 240))
    dt = clock.tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            RUNNING = False
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                LINEAR_VELOCITY = MOVE_SPEED
            if event.key == pygame.K_DOWN:
                LINEAR_VELOCITY = -MOVE_SPEED
            if event.key == pygame.K_LEFT:
                ANGULAR_VELOCITY = TURNING_SPEED
            if event.key == pygame.K_RIGHT:
                ANGULAR_VELOCITY = -TURNING_SPEED
    
        if event.type == pygame.KEYUP:
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                ANGULAR_VELOCITY = 0
            if event.key in (pygame.K_UP, pygame.K_DOWN):
                LINEAR_VELOCITY = 0
    
  
    ROBOT_X_POSITION += LINEAR_VELOCITY * math.cos(ROBOT_TURNING_DEGREE) * dt
    ROBOT_Y_POSITION += LINEAR_VELOCITY * math.sin(ROBOT_TURNING_DEGREE) * dt
    ROBOT_TURNING_DEGREE += ANGULAR_VELOCITY * dt


    ROBOT_TURNING_DEGREE = math.atan2(math.sin(ROBOT_TURNING_DEGREE), math.cos(ROBOT_TURNING_DEGREE))
  
    DrawRobot(ROBOT_X_POSITION, ROBOT_Y_POSITION,ROBOT_TURNING_DEGREE,ppm, screen_width, screen_height, robot_config)
    
    pygame.display.update()
    
    clock.tick(60)

pygame.quit()
