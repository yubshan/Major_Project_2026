import math
def ForwardKinematics(linearVelocity, angularVelocity, theta, dt):
    x_update_by = linearVelocity * math.cos(theta) * dt
    y_update_by = linearVelocity * math.sin(theta) * dt
    turned_by = angularVelocity * dt

    return x_update_by, y_update_by, turned_by