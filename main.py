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
        if distance == ERROR:
            motors.stop()
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
            if colour == GRAY:
                # joining on the rescue area
                motors.run(base_right_velocity, base_left_velocity)
                time.sleep(2)

                # loop to get the balls
                while True:
                    # update the image
                    has_frame, img = cam.read()
                    
                    # save the state on rescue area
                    state = rescue_area(img)

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

            # verify if has a 90°curve
            elif colour == GREEN:
                # turn on the correct side
                if side_curve == LEFT:
                    motors.turn_right(right_velocity_curve, left_velocity_curve)
                elif side_curve == RIGHT:
                    motors.turn_left(right_velocity_curve, left_velocity_curve)

            elif colour == RED:
                # stop the car on the red line
                motors.stop()
                # ALL it's run fine
                break 
        
        # verify if has a curve
        if is_curve is not None:
            if is_curve is LEFT:
                motors.turn_left(right_velocity_curve, left_velocity_curve)
            elif is_curve is RIGHT:
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