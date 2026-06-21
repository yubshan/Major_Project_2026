import pygame
from config import *
from core.ray import Ray

class RayCaster:
    def __init__(self, robot):
        self.rays = []
        self.robot = robot

    def castAllRays(self, grid):
        self.rays=[]
        rayAngle = self.robot.turnDegree - FOV / 2

        for i in range(NUM_RAYS):
            ray = Ray(rayAngle, self.robot)
            ray.cast(grid)
            self.rays.append(ray)

            rayAngle += FOV / NUM_RAYS  
    def render(self, screen):
        for ray in self.rays:
            ray.render(screen)
