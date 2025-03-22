import cv2 
from line_detection import *
from ball_detection import *
from robot_control import *

def main():
    # define the constat values
    Kp = 150; Ki = 0; Kd = 0; previous_erro = 0; PID = 0
    right_velocity_curve = 200; left_velocity_curve = 200

    # init the cam
    s = 'camera-path'
    cam = cv2.VideoCapture(s)
    
    # loop to read the cam
    while cv2.waitKey(1) != 27:
        # extract the cam info
        has_frame, img = cam.read()
        
        # verify if the cam working
        if not has_frame:
            break

        # verify if has an object on front
        distance = measure_distance()
        if distance is not None and distance <= MAX_DISTANCE:
            avoid_obstacle()
        
        # calculate the error
        erro, is_curve, has_colour = detect_line(img)
        
        # if not has line it try to come back of line
        if erro is None:
            motors.run_backward(right_velocity_curve, left_velocity_curve)
            time.sleep(0.5)
            motors.stop_motor()

        # I still have to decided the magic numbers
        if has_colour is not None:
            colour, side_curve = has_colour

            # verify if is going to rescue area
            if colour == 'grey':
                rescue_area()

            # verify if has a 90°curve
            elif colour == 'green':
                # turn on the correct side
                if side_curve == 'left':
                    motors.turn_right(right_velocity_curve, left_velocity_curve)
                elif side_curve == 'right':
                    motors.turn_left(right_velocity_curve, left_velocity_curve)

            elif colour == 'red':
                # stop the car on the red line
                motors.stop()
                # ALL it's run fine
                break 
        
        # verify if has a curve
        if is_curve is not None:
            if is_curve is 'left':
                motors.turn_left(right_velocity_curve, left_velocity_curve)
            elif is_curve is 'right':
                motors.turn_right(right_velocity_curve, left_velocity_curve)
        else:
            # calculate PID
            PID = PID_functions.calculate_PID(erro, previous_erro, Kp, Kd, Ki)
            previous_erro = erro

            # adjust move the car
            adjust_move(PID)

    # restart the cam memory
    cam.release()

if __name__ == '__main__':
    main()