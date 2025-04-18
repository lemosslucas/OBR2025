# for control rasbery pi's board
import pigpio
import ctypes 
import time
from ball_detection import *
# pip install mpu6050-raspberrypi
from mpu6050 import mpu6050

# initialize the accelerometer
accelerometer = mpu6050(0x68)

# define the ramp slope and the upper on the motor to upper the ramp
ramp_slope = 15 
velocity_ramp = 20

# initialize pigpio
pi = pigpio.pi()

# define the magic number
MAX_DISTANCE = 8

# define Pins
TRIG = 9
ECHO = 10

# set pins
pi.set_mode(TRIG, pigpio.OUTPUT)
pi.set_mode(ECHO, pigpio.INPUT)

#set servo pins
servo_arm = 17
servo_shovel = 18

# load C files
PID_functions = ctypes.CDLL(("./c_files/PID.so"))
motors = ctypes.CDLL("./c_files/motors.so")

# Define arguments and returns of function
PID_functions.calculate_PID.argtypes = (ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int)
PID_functions.calculate_PID.restype = ctypes.c_int

motors.run.argtypes = [ctypes.c_int, ctypes.c_int]
motors.run_backward.argtypes = [ctypes.c_int, ctypes.c_int]
motors.turn_right.argtypes = [ctypes.c_int, ctypes.c_int]
motors.turn_left.argtypes = [ctypes.c_int, ctypes.c_int]
motors.stop_motor.argtypes = []

# defint the base velocity
base_right_velocity = 180
base_left_velocity = 180

def adjust_move(PID):
    """
    Adjusts the velocity of the robot's motors based on the PID output.

    This function updates the right and left velocities of the robot using the given PID value.
    The velocities are adjusted from a base value by subtracting the PID from the right velocity
    and adding the PID to the left velocity. The velocities are clamped to the range [0, 255] to ensure
    they stay within acceptable motor speed limits.

    Parameters:
        PID (int): The output of the PID controller, used to adjust the velocity of the robot's motors.
                     A positive PID value decreases the right velocity and increases the left velocity.
    """

    # update the velocity values
    right_velocity = max(0, min(base_right_velocity - PID, 255))
    left_velocity = max(0, min(base_left_velocity + PID, 255))

    if read_accelerometer() >= ramp_slope:
        right_velocity = max(0, min(velocity_ramp, 255))
        left_velocity = max(0, min(velocity_ramp, 255))
        
    # update the vel of the car
    motors.run(right_velocity, left_velocity)

def avoid_obstacle():
    """
    Executes a sequence of movements to avoid an obstacle detected by the ultrasonic sensor.

    The robot:
    1. Stops for 1 second.
    2. Turns left by reducing the left motor speed for 2 seconds.
    3. Moves forward for 4 seconds.
    4. Turns right by reducing the right motor speed for 1 second.
    5. Moves forward for 8 seconds.
    6. Turns right again for 1 second.
    7. Moves forward for 4 seconds.

    This function assumes that `motors.run(right_velocity, left_velocity)`
    controls the motors, where `right_velocity` and `left_velocity` define
    the speed of the right and left motors, respectively.
    """
    # define the velocity
    right_velocity = 255; left_velocity = 255
    
    # stop to ensure the moves
    motors.stop()
    time.sleep(1)
    
    # maybe this not be useful
    #motors.run_backward(right_velocity, left_velocity)
    #time.sleep(2)
    
    # turn on left
    motors.run(right_velocity, left_velocity/2)
    time.sleep(2)
    
    # run forward
    motors.run(right_velocity, left_velocity)
    time.sleep(4)

    # turn on right
    motors.run(right_velocity/2, left_velocity)
    time.sleep(1)

    # run forward
    motors.run(right_velocity, left_velocity)
    time.sleep(8)

    # turn on right
    motors.run(right_velocity/2, left_velocity)
    time.sleep(1)

    # run forward
    motors.run(right_velocity, left_velocity)
    time.sleep(4)

def measure_distance():
    """
    Measures the distance to the nearest object in front of the robot using an ultrasonic sensor.

    The function sends a 10-microsecond pulse to the TRIG pin, waits for the response 
    from the ECHO pin, and calculates the distance based on the time taken for the 
    sound wave to return.

    Returns:
        float: Distance to the nearest object in centimeters.
    """
    # turn on the sensor
    pi.write(TRIG, 1)
    time.sleep(0.00001)
    # turn of the sensor
    pi.write(TRIG, 0)

    # wait the echo get trig sinal
    while pi.read(ECHO) == 0:
        start = time.time()

    while pi.read(ECHO) == 1:
        end = time.time()

    # calculate the wave duration
    duration = end - start 
    # 34300 velocity of sound
    distance = (duration  * 34300) / 2 

    # return the distance in cm
    return distance

# standard position of robot on axis-labels
robot_position_x = 0
MIN_DISTANCE_BALL = 200 
BALL_NOT_FOUND = -1
BALL_FOUND = 1

def rescue_area(img):
    """
    Not implemented yet!
    """
    
    # find the balls on the area
    ball_colour, (x, y) = find_ball(img)

    if x is None or y is None:
        return BALL_NOT_FOUND

    # if the robot is so near at the ball it stop and catch the ball
    if y > MIN_DISTANCE_BALL:
        motors.stop()

        # catch the ball
        pi.set_servo_pulsewidht(servo_arm, angle_to_pulse(45))
        time.sleep(1)
        pi.set_servo_pulsewidht(servo_shovel, angle_to_pulse(35))
        time.sleep(1)
    
    # calculate the distance
    error = np.abs(robot_position_x - x)

    # calculate the proportional error
    kp = 0.1
    proportional = int(kp * error)

    #calculate the new velocity to go into the ball
    right_velocity = max(0, min(base_right_velocity - proportional, 255))
    left_velocity = max(0, min(base_left_velocity + proportional, 255))

    # run into the ball position
    motors.run(right_velocity, left_velocity)

    # find where need put the ball
    # basket_color, basket_position = find_basket(img)

def search_balls_on_rescue_area(img, start_search):
    """
    Searching the balls on rescue area
    """

    # turn trying to find the balls
    motors.run(-base_right_velocity, base_left_velocity)
    # search again
    ball_colour, (x, y) = find_ball(img)
    
    if x is not None or y is not None:
        # stop the car on position where has a balls
        motors.stop()

        # return ball was found and start_search time
        return True, start_search
    
    # end time was search was completed
    end_search = time.time()
    
    # if the search time is bigger than 10 sec
    if np.abs(start_search - end_search) > 10:
        # run to a new position
        motors.run(base_left_velocity, base_left_velocity)
        time.sleep(2)
        
        # return the reseted start time
        start_search = time.time()

    # return the ball wasn't found and start_search time
    return False, start_search 

def angle_to_pulse(angle):
    """
    Converts an angle in degrees to a pulse width in microseconds 
    for controlling a servo motor.

    The pulse width is calculated assuming a typical servo motor 
    with a range from 500µs (0 degrees) to 2500µs (180 degrees).

    Args:
        angle (float): The angle in degrees (0 to 180).

    Returns:
        float: The corresponding pulse width in microseconds.
    """
    return 500 + (angle / 180.0) * 2000

def read_accelerometer():
    """
    Reads the current accelerometer data and calculates the 
    inclination angle of the robot in degrees.

    The angle is computed using the arctangent of the x and z 
    axes values, assuming the robot is tilting mainly in the 
    x-z plane.

    Returns:
        float: The inclination angle of the robot in degrees.
    """
    # read the current position of robot
    data = accelerometer.get_accel_data() 

    # calculate the inclination of robot using x and z labels
    inclination_angle = np.arctan2(data['x'], data['z']) * (180 / np.pi)

    # return the inclination of robot
    return inclination_angle