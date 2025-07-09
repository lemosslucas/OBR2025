import numpy as np
import cv2
import time
import serial

from constants import (base_left_velocity, base_right_velocity,curve_velocity,
                       ERROR, FRAMES_TO_LOST, MIN_RECOVERY_AREA)
import constants

from hardware_setup import ser, serial_lock
from logger import log 
from line_detection import detect_line
from motors import MotorController, send_command

if ser:
    motors = MotorController()
else:
    motors = None

def set_led(color_name, state):
    """Envia um comando para ligar (1) ou desligar (0) um LED."""
    cmd = f"L,{color_name},{state}\n"
    send_command(cmd)

def measure_distance():
    """Requisita a distância do Arduino e espera pela resposta."""
    with serial_lock:
        if not ser or not ser.is_open:
            return ERROR # Retorna um valor alto se a serial não estiver disponível

        send_command("R,dist\n") # Envia a requisição
        try:
            response = ser.readline().decode('utf-8').strip()
            if response.startswith("D,"):
                # Extrai o valor da distância da resposta "D,15"
                return int(response.split(',')[1])
        except (serial.SerialException, IndexError, ValueError):
            return ERROR # Retorna valor alto em caso de erro de comunicação
        return ERROR # Retorna valor alto se não receber resposta válida

def led_feedback(color_name, times=1):
    """Envia comandos seriais para piscar um LED."""
    for _ in range(times):
        send_command(f"L,{color_name},1\n")
        time.sleep(0.1)
        send_command(f"L,{color_name},0\n")
        time.sleep(0.1)

def get_roi(img):
    """
    This function is typically used to reduce or standardize the input image size
    for further processing, such as region of interest (ROI) extraction or 
    computational efficiency in vision algorithms.

    Parameters:
        img (numpy.ndarray): The input image to be resized.

    Returns:
        numpy.ndarray: The resized image with dimensions (desired_width, desired_height).
    """
    # para tentar o ROI
    h, w, _ = img.shape
#   print(f'h={h}, w={w}')
    slice_point = h // 2 
    roi = img[slice_point:h, 60:w-60]

    return roi

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
    # posicional error
    P = error[0]
    # angular error
    pid_state['I'] += P

    # anti wind up
    if (P > 0 and previous_error < 0) or (P < 0 and previous_error > 0):
        log('PID Integral zerado para evitar windup.')
        pid_state['I'] = 0

    # Clamp integral term between -255 and 255
    pid_state['I'] = max(-255, min(255, pid_state['I']))

    D = error[0] - previous_error

    PID = (Kp * P) + (Ki * pid_state['I']) + (Kd * D) 
    PID = PID + constants.Ka * error[1]

    log(f'Erro {error} | Pid {PID} | Kp: {Kp} | Kd: {Kd} | Ki: {Ki}')
    return PID

def adjust_move(PID, base_right_velocity, base_left_velocity):
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

    right_velocity = max(0, min(base_right_velocity - PID, 255))
    left_velocity = max(0, min(base_left_velocity + PID, 255))
 
    # update the vel of the car
    motors.run(right_velocity, left_velocity)

# function to found the line
def try_comeback_line(move_function, get_current_img, duration=1.5):
    """
    Attempts to recover the line after it has been lost by moving the robot for a fixed duration.

    During the specified time window, the robot continuously checks for the presence of the line.
    If the line is detected again, the robot stops and the function returns success.

    Parameters:
        move_function (function): A function that drives the robot (e.g., backward or turning).
        get_current_img (function): A function that returns the current image frame for line detection.
        duration (float, optional): Maximum time in seconds to try recovering the line. Default is 1.5 seconds.

    Returns:
        bool: True if the line was successfully recovered, False otherwise.
    """
    # stop the motors
    motors.stop_motor()
    time.sleep(0.3)

    # count the start time 
    start_time = time.time()
    t = 0

    while time.time() - start_time < duration:
        if t >= FRAMES_TO_LOST:
            return True
        print(f"tentativa {t}")

        # to avoid a color detec_error
        erro, _, _, area = detect_line(get_current_img(), None)
        
        # ensure the robot has back on the line
        if erro is not None and area > MIN_RECOVERY_AREA:
            log('Voltamos')
            motors.stop_motor() 
            t+=1
            #return True
        
        move_function(curve_velocity, curve_velocity)
        time.sleep(0.05)
    
    motors.stop_motor()
    return False
"""
Accelerometer
"""
def get_gyro():
    with serial_lock:
        if not ser or not ser.is_open:
            return None
        
        send_command("R,imu\n") # Envia a nova requisição
        try:
            response = ser.readline().decode('utf-8').strip()
            if response.startswith("I,"):
                parts = response.split(',')
                # Retorna um dicionário com os dados
                return {
                    'ax': float(parts[1]), 'ay': float(parts[2]), 'az': float(parts[3]),
                    'gx': float(parts[4]), 'gy': float(parts[5]), 'gz': float(parts[6]),
                }
        except Exception as e:
            log(f"Erro ao ler dados do IMU: {e}")
            return None
        return None
    
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
        data = get_gyro()
        if data:
            # calculate the inclination of robot using x and z labels
            inclination_angle = np.arctan2(data['ay'], data['az']) * (180 / np.pi)

            # return the inclination of robot
            return inclination_angle
        return ERROR
    except Exception as e:
        log("Deu merda no acelerometro")
        return ERROR
    
def verify_lost_line(get_current_img, timeout=5.0):
    """
    """
    # timeout to avoid infite loop
    start_time = time.time()
    line_lost_count = 0

    while (time.time() - start_time) < timeout:
        erro, _, _, _ =  detect_line(get_current_img(), None)

        # add a counter to avoid false-positive
        if erro is None:
            print(line_lost_count)
            line_lost_count += 1
        else:
            line_lost_count = 0

        if line_lost_count >= FRAMES_TO_LOST:
            print('perdeu a linha')
            return True
        
        # run until lost the line or the time finsih
        motors.run(base_right_velocity, base_left_velocity)
        time.sleep(0.05)
        
    print('achei a linha')
    # line was not lost
    return False

def turn_90(turn_function, get_current_img):
    """
    Executes a 90-degree turn maneuver using a specified turn function and gyroscope feedback.

    The maneuver consists of four steps:
        1. Move forward until the line is lost.
        2. Stop the motors and wait briefly.
        3. Execute a 90-degree turn using the provided turn function and gyroscope feedback.
        4. Stop the motors again and wait before resuming the main path.

    This function uses a timeout to prevent infinite loops during the initial line loss detection phase.

    Parameters:
        turn_function (function): A function responsible for initiating the motor turn motion.
         (float): The gyroscope Z-axis bias used to calculate angular displacement.
        get_current_img (function): A function that returns the current camera image for line detection.
    """
    if verify_lost_line(get_current_img, timeout=1.0):
        time.sleep(0.4)

        print('parei pra virar')
        # stop the motors: 2 move
        motors.stop_motor()
        time.sleep(0.5)

        # turn on the side 
        turn_function(curve_velocity, curve_velocity)
        turn_until_angle(85, )
        
        log('curva de 90 feita')
    else:
        log('era uma intersecao')

def do_dead_end():
    """
    """
    # run 0.2 sec
    time.sleep(0.2)
    log('beco sem saida')
  
    # turn 90 degre on right
    motors.turn_right(curve_velocity, curve_velocity)
    turn_until_angle(90, )
  
    # run backward until find the line again
    motors.run_backward(base_right_velocity, base_left_velocity)
    time.sleep(2)
    
    # stop to syc the motors
    motors.stop_motor()
    time.sleep(0.2)

    # turn on right again to finsish 180 curve
    motors.turn_right(curve_velocity, curve_velocity)
    turn_until_angle(90, )
    motors.stop_motor()
    time.sleep(0.2)

def turn_until_angle(target_angle=90, ):
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

    while abs(angle_z) < target_angle:
        try:
            data = get_gyro()
            current_time = time.time()
            delta_time = current_time - start_time
            start_time = current_time

            # get the angular velocity
            angular_velocity_rad = data['gz'] 

            # convert to degree
            angular_velocity = angular_velocity_rad * (180/np.pi)
            
            angle_z += angular_velocity * delta_time

            print(angle_z)
            time.sleep(0.01)
        except Exception as e:
            log(f'Deu merda lendo o osciloscopio {e}')
            motors.stop_motor()
            return
    
    motors.stop_motor()
    print('Rotation finished')
    time.sleep(0.5)
    
def avoid_obstacle(cam, ):
    """
    Executes a predefined sequence of movements to avoid an obstacle.
    Turning on 

    The robot performs:
    1. A short stop to stabilize.
    2. A 90° left turn.
    3. Moves forward for 4 seconds.
    4. A 90° right turn.
    5. Moves forward for 4 seconds.
    6. A ~75° right turn (to realign to original path).

    The function assumes that:
    - `motors.run(right_velocity, left_velocity)` controls the motors.
    - `turn_until_angle(angle)` rotates the robot using IMU data.
    - Motor values are calibrated such that turning is achieved by stopping one side.
    """
    # define the velocity
    right_velocity = 255; left_velocity = 255
    
    # state 1
    motors.stop_motor()
    time.sleep(0.3)

    # state 2
    motors.run_backward(right_velocity, left_velocity)
    time.sleep(0.4)

    # state 3
    motors.run(right_velocity, 0)
    turn_until_angle(85)
    
    # state 4
    motors.run(right_velocity, left_velocity)
    time.sleep(0.1)

    # state 5
    motors.run(0, left_velocity)
    turn_until_angle(85)

    # state 6
    motors.run(right_velocity, left_velocity)
    time.sleep(0.5)

    # state 7
    motors.run(0, left_velocity)
    turn_until_angle(45)

    # state 8
    motors.run(right_velocity, left_velocity)
    time.sleep(0.5)

    #state 9
    motors.run(right_velocity, 0)
    turn_until_angle(45)
    
    log('Desvio feito! Procurando a linha')
    motors.run(150, 150)

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

if __name__ == "__main__":
    pass
