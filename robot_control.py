import numpy as np
from constants import (base_left_velocity,
                       base_right_velocity, ramp_slope, velocity_ramp,
                       servo_arm, servo_shovel, robot_position_x,
                       BALL_FOUND, BALL_NOT_FOUND, BALLS_SAVED, MIN_DISTANCE_BALL,
                       TRIG, ECHO, ERROR)

from hardware_setup import motors, pi, accelerometer
from ball_detection import find_ball
import time
from server_test import log 

def calculate_PID(error, previous_error, Kp, Kd, Ki, pid_state):
    """
    Computes the PID control output based on the given error values and PID constants.

    The PID control formula is:
        PID = (Kp * P) + (Ki * I) + (Kd * D)

    where:
        - P (Proportional) is the current error.
        - I (Integral) accumulates past errors, clamped between -255 and 255.
        - D (Derivative) is the rate of change of the error.

    Parameters:
        error (int): The current error value.
        previous_error (int): The error from the previous iteration.
        Kp (int): The proportional gain constant.
        Kd (int): The derivative gain constant.
        Ki (int): The integral gain constant.

    Returns:
        int: The computed PID output.
    """
    P = error
    pid_state['I'] += P

    # Clamp integral term between -255 and 255
    pid_state['I'] = max(-255, min(255, pid_state['I']))

    D = error - previous_error

    PID = (Kp * P) + (Ki * pid_state['I']) + (Kd * D)

    return PID

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

def turn_until_angle(target_angle=90):
    """
    Rotates the robot until it reaches the specified angle using accelerometer data.

    The function integrates angular acceleration over time to estimate the angle rotated
    around the Z-axis (yaw), assuming rotation occurs primarily in that axis.

    Parameters:
        target_angle (float): The angle in degrees to rotate before stopping. Defaults to 90 degrees.

    Note:
        This implementation assumes 'accelerometer.get.accel_data()' returns a dictionary
        with a key 'z' representing the angular acceleration (or angular velocity) in the Z-axis.
    """
    angle_z = 0
    start_time = time.time()

    log(f'Começando o giro de {target_angle}')

    while abs(angle_z) < target_angle:
        try:
            data = accelerometer.get_gyro_data()
            current_time = time.time()
            delta_time = current_time - start_time
            start_time = current_time

            # get the angular velocity
            angle_z += data['z'] * delta_time
            print(f'Angle z {angle_z:.2f}')
            time.sleep(0.01)
        except Exception as e:
            log(f'Deu merda lendo o osciloscopio {e}')
    
    print('Rotation finished')
    motors.stop_motor()

def avoid_obstacle():
    """
    Executes a predefined sequence of movements to avoid an obstacle.

    The robot performs:
    1. A short stop to stabilize.
    2. A 90° left turn.
    3. Moves forward for 4 seconds.
    4. A 90° right turn.
    5. Moves forward for 4 seconds.
    6. A ~75° right turn (to realign to original path).
    7. Moves forward for 2 seconds.

    The function assumes that:
    - `motors.run(right_velocity, left_velocity)` controls the motors.
    - `turn_until_angle(angle)` rotates the robot using IMU data.
    - Motor values are calibrated such that turning is achieved by stopping one side.
    """
    # define the velocity
    right_velocity = 255; left_velocity = 255
    
    # state 1
    motors.stop()
    time.sleep(0.5)

    # state 2
    motors.run(right_velocity, 0)
    turn_until_angle(90)
    
    # state 3
    motors.run(right_velocity, left_velocity)
    time.sleep(4)

    # state 4
    motors.run(0, left_velocity)
    turn_until_angle(90)

    # state 5
    motors.run(right_velocity, left_velocity)
    time.sleep(4)

    # state 6
    motors.run(0, left_velocity)
    turn_until_angle(75)

    # state 7
    motors.run(right_velocity, left_velocity)
    time.sleep(2)

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
    
    timeout = time.time() + 1

    # wait for the ECHO pin to go HIGH
    while pi.read(ECHO) == 0:
        pulse_start = time.time()

        # to ensure an error situation
        if pulse_start > timeout:
            print("ECHO nao ligou!")
            return ERROR

    timeout = time.time() + 1

    # wait for the ECHO pin go to LOW
    while pi.read(ECHO) == 1:
        pulse_end = time.time()

        # to ensure an error situation
        if pulse_end > timeout:
            print("TRIG nao ligou")
            return ERROR

    # calculate the wave duration
    duration = pulse_end - pulse_start

    # 34300 velocity of sound
    distance = (duration  * 34300) / 2

    # return the distance in cm
    return distance

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
    try: 
        # read the current position of robot
        data = accelerometer.get_accel_data() 

        # calculate the inclination of robot using x and z labels
        inclination_angle = np.arctan2(data['x'], data['z']) * (180 / np.pi)

        # return the inclination of robot
        return inclination_angle
    except Exception as e:
        log("Deu merda no acelerometro")
        return ERROR
    
def rescue_area(cam):
    # joining on the rescue area
    motors.run(base_right_velocity, base_left_velocity)
    time.sleep(2)

    # loop to get the balls
    while True:
        # update the image
        has_frame, img = cam.read()
        
        # save the state on rescue area
        state = catch_balls_on_rescue_area(img)

        # try to find a ball
        if state == BALL_NOT_FOUND:
            # clock the initial time to search
            start_search = time.time()
            
            while True:
                # update the image
                has_frame, img = cam.read()

                # searching the balls on rescue area
                ball_found, start_search = search_balls_on_rescue_area(img, start_search)
                
                # stop the loop when ball was found
                if ball_found:
                    break

        # all the bals was saved                
        if state == BALLS_SAVED:
            # finish the work on rescue area
            break

def catch_balls_on_rescue_area(img):
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
        pi.set_servo_pulsewidth(servo_arm, angle_to_pulse(45))
        time.sleep(1)
        pi.set_servo_pulsewidth(servo_shovel, angle_to_pulse(35))
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

if __name__ == "__main__":
    adjust_move(0)