import pygame
import math
from utils import MeterToPixel, WorldToScreen
def DrawRobot(x_position, y_position, turningRadius , ppm, screen_width, screen_height, robot_config):

    screen = pygame.display.get_surface()

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
   
    

    screen.blit(rotated_surface, new_rect)
