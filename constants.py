import time 
from time import sleep

"""
Component's pins
"""
TRIG = 22
ECHO = 27
servo_arm = 14
servo_shovel = 15

"""
Constant values
"""
MAX_DISTANCE = 10
MIN_DISTANCE_BALL = 200 
BALL_NOT_FOUND = -1
BALL_FOUND = 1
BALLS_SAVED = 0
ERROR = -1

# define the color values references
BLACK = 0
GRAY = 1
GREEN = 2
RED = 3

# define the side curve values references
LEFT = 1
RIGHT = 0

# standard position of robot on axis-labels
robot_position_x = 0

#velocity
base_right_velocity = 180
base_left_velocity = 180

# define the ramp slope and the upper on the motor to upper the ramp
ramp_slope = 15 
velocity_ramp = 20

"""
PID values
"""
Kp = 1; Ki = 0.01; Kd = 0.1
pid_state = {'I': 0}
previous_error = 0 

"""
Computer Vision constants
"""
threshold_value = 133
# size of the image
desired_width = 320
desired_height = 240

curve_threshold = 50

def update_constants(kp=None, ki=None, kd=None, threshold=None):
    global Kp, Ki, Kd, threshold_value
    if kp is not None:
        Kp = kp
    if ki is not None:
        Ki = ki
    if kd is not None:
        Kd = kd
    if threshold is not None:
        threshold_value = threshold
