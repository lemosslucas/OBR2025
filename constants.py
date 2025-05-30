import pigpio
from gpiozero import LED
from mpu6050 import mpu6050
from motors import MotorController
import time 
from time import sleep

# Global objects
pi = pigpio.pi()
accelerometer = mpu6050(0x68)
motors = MotorController()

"""
Component's pins
"""
TRIG = 22
ECHO = 27
servo_arm = 14
servo_shovel = 15

green_led = LED(23)
red_led = LED(24)

# Motor GPIO pins
MOTOR_LEFT_CLKWISE = 18
MOTOR_LEFT_ANTI = 12
MOTOR_RIGHT_CLKWISE = 13
MOTOR_RIGHT_ANTI = 19

# Inicialization of the pins
pi.set_mode(TRIG, pigpio.OUTPUT)
pi.set_mode(ECHO, pigpio.INPUT)

"""
Constant values
"""
MAX_DISTANCE = 8
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
Kp = 100; Ki = 200; Kd = 150

"""
Computer Vision constants
"""
threshold_value = 50
