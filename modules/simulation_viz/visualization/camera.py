import pygame
class Camera:

    def __init__(self, offset_x=600, offset_y=100, speed=400):

        self.offset_x = offset_x
        self.offset_y = offset_y

        self.speed = speed
    def update(self, keys, dt):
     movement = self.speed * dt

     if keys[pygame.K_a]:
        self.offset_x -= movement

     if keys[pygame.K_d]:
        self.offset_x += movement

     if keys[pygame.K_w]:
        self.offset_y -= movement

     if keys[pygame.K_s]:
        self.offset_y += movement


    def apply(self, x, y):

        return (
            int(x + self.offset_x),
            int(y + self.offset_y)
        )