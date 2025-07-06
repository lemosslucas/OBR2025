"""
Component's pins
"""
TRIG = 27
ECHO = 22
servo_arm = 14
servo_shovel = 15
BTN_PIN = 17

"""
Constant values
"""
MAX_DISTANCE = 10
MIN_DISTANCE_BALL = 200 
BALL_NOT_FOUND = -1
BALL_FOUND = 1
BALLS_SAVED = 0
ERROR = -1
TIME_OUT_SEARCH = 1
DIFF_MOTOR = 0
MIN_RECOVERY_AREA = 50
FRAMES_TO_LOST = 2
COLOR_OFFSET = 10

# constants for led signals
LINE_LOST = 2
START_ROBOT = 1
LINE_FOUND =2
GIVEWAY_RESCUE = 3
# define the color values references
BLACK = 0
GRAY = 1
GREEN = 2
RED = 3

# define the side curve values references
LEFT = 1
RIGHT = 0
DEAD_END = 2

# standard position of robot on axis-labels
robot_position_x = 0

#velocity
base_right_velocity = 130
base_left_velocity =  130
curve_velocity = 220

# define the ramp slope and the upper on the motor to upper the ramp
ramp_slope = 15 
velocity_ramp = 220
velocity_ramp_down = 80

"""
PID values
"""
Kp = 4; Ki = 0; Kd = 0; Ka = 0
pid_state = {'I': 0}
previous_error = 0 

"""
Computer Vision constants
"""
threshold_value = 52
# size of the image
desired_width = 320
desired_height = 240

MIN_AREA_GREEN = 50
curve_threshold = 50

def update_constants(kp=None, ki=None, kd=None, ka=None, threshold=None):
    global Kp, Ki, Kd, threshold_value
    if kp is not None:
        Kp = kp
    if ki is not None:
        Ki = ki
    if kd is not None:
        Kd = kd
    if ka is not None:
        Ka = ka
    if threshold is not None:
        threshold_value = threshold
