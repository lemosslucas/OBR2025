import cv2 
from line_detection import detect_line
from robot_control import (measure_distance, avoid_obstacle, 
                           adjust_move, calculate_PID, rescue_area)
from server_test import log
from constants import *

def main():
    # define the constat values
    Kp = 150; Ki = 0; Kd = 0; previous_erro = 0
    right_velocity_curve = 200; left_velocity_curve = 200

    # init the cam
    camera_board = 0
    cam = cv2.VideoCapture(camera_board)
    
    # loop to read the cam
    while cv2.waitKey(1) != 27:
        # extract the cam info
        has_frame, img = cam.read()
        
        # verify if the cam working
        if not has_frame:
            break

        # verify if has an object on front
        distance = measure_distance()
        if distance == ERROR:
            motors.stop()
            distance = measure_distance()

        log(distance)

        if distance is not None and distance <= MAX_DISTANCE:
            log('Avoiding obstacle')
            avoid_obstacle()
        
        # calculate the error
        erro, is_curve, has_colour = detect_line(img)
        log(f'erro: {erro} | is_curve {is_curve} | has_colour {has_colour}')

        # if not has line it try to come back of line
        if erro is None:
            # to ensure the robot don't run out the track
            start_time = time.time()
            timeout = 3

            # comeback until find a line 
            while erro is None and (time.time() - start_time < timeout):
                log('Lost line')
                motors.run_backward(right_velocity_curve, left_velocity_curve)
                time.sleep(0.05)

                # update cam image
                has_frame, img = cam.read()
                if not has_frame:
                    break

                erro, is_curve, has_colour = detect_line(img)
                
            motors.stop_motor()

        if has_colour is not None:
            colour, side_curve = has_colour

            # verify if is going to rescue area
            if colour == GRAY:
                log('Rescue area detected')
                rescue_area(cam)

            # verify if has a 90°curve
            elif colour == GREEN:
                # turn on the correct side
                if side_curve == LEFT:
                    log('90 degree turn on left')
                    motors.turn_right(right_velocity_curve, left_velocity_curve)
                elif side_curve == RIGHT:
                    log('90 degree turn on right')
                    motors.turn_left(right_velocity_curve, left_velocity_curve)

            elif colour == RED:
                log('finish line')
                # stop the car on the red line
                motors.stop()
                # ALL it's run fine
                break 
        
        # verify if has a curve
        if is_curve is not None:
            if is_curve is LEFT:
                log('90 degree turn on left')
                motors.turn_left(right_velocity_curve, left_velocity_curve)
            elif is_curve is RIGHT:
                log('90 degree turn on right')
                motors.turn_right(right_velocity_curve, left_velocity_curve)
        else:
            # calculate PID
            pid_state = {'I': 0}
            PID = calculate_PID(erro, previous_erro, Kp, Kd, Ki, pid_state)
            previous_erro = erro
            log(f'Pid {PID}')
            # adjust move the car
            adjust_move(PID)

    # restart the cam memory
    cam.release()
    # restart the motors
    motors.disconect()

if __name__ == '__main__':
    main()