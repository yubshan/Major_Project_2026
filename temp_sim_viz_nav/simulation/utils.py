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
