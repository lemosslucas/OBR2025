import cv2 
from line_detection import *
from ball_detection import *
import ctypes 
# for control rasbery pi's board
#import pigpio as PIN

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
    # defint the base velocity
    base_right_velocity = 180
    base_left_velocity = 180

    # update the velocity values
    right_velocity = max(0, min(base_right_velocity - PID, 255))
    left_velocity = max(0, min(base_left_velocity + PID, 255))

    # update the vel of the car
    motors.run(right_velocity, left_velocity)

def rescue_area():
    """
    Not implemented yet!
    """
    ball_colour, ball_position = find_ball(img)
    # precisa fazer com oq o carro siga a dirença de onde esta a bola
    
def main():
    # define the constat values
    Kp = 150; Ki = 0; Kd = 0; previous_erro = 0; PID = 0
    right_velocity_curve = 200; left_velocity_curve = 200

    while True:
        # calculate the error
        erro, is_curve, has_colour = detect_line(img)
        
        # I still have to decided the magic numbers
        if has_colour is not None:
            colour, side_curve = has_colour
            # verify if is going to rescue area
            if colour is 'grey':
                rescue_area()
            # verify if has a 90°curve
            if colour is 'green':
                # turn on the correct side
                if side_curve is 'left':
                    motors.turn_right(right_velocity_curve, left_velocity_curve)
                if side_curve is 'right':
                    motors.turn_left(right_velocity_curve, left_velocity_curve)
            if colour is 'red':
                # stop the car on the red line
                motors.stop()
                break

        if is_curve is not None:
            if is_curve is 'left':
                motors.turn_left(right_velocity_curve, left_velocity_curve)
            if is_curve is 'right':
                motors.turn_right(right_velocity_curve, left_velocity_curve)
            
        # calculate PID
        PID = PID_functions.calculate_PID(erro, previous_erro, Kp, Kd, Ki)
        previous_erro = erro

        # adjust move the car
        adjust_move(PID)


if __name__ == '__main__':
    main()