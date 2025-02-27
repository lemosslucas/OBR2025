import cv2 
from line_detection import *
from ball_detection import *

def calculate_PID(erro, previous_erro, Kp, Kd, Ki):
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
        tuple: A tuple containing:
            - PID (int): The computed PID output.
            - previous_erro (int): The updated previous error.
    """
    # define param values
    PID = 0; I = 0; P = erro
    # limit the I on -255:255
    I = max(-255, min(I + P, 255))
    D = erro - previous_erro

    # calculate the PID
    PID = (Kp * P) + (Ki * I) + (Kd * D)

    # update the value of erro
    previous_erro = erro
    
    # return PID, previous_erro
    return PID, previous_erro

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
    #run(right_velocity, left_velocity)

def rescue_area():
    """
    Not implemented yet!
    """
    ...

def main():
    # define the constat values
    Kp = 150, Ki = 0, Kd = 0, previous_erro = 0, PID = 0
    
    # calculate the error
    erro, is_curve, has_colour = detect_line(img)
    
    # Already I go decided the magic number
    if has_colour is not None:
        # verify if is going to rescue area
        if has_colour is 'grey':
            rescue_area()
        # verify if has a 90°curve
        if has_colour is 'green':
            # curve_90(side)
            ...
        if has_colour is 'red':
            # stop()
            ...        

    if is_curve is not None:
        if is_curve is 'left':
            #left_curve()
            ...
        if is_curve is 'right':
            #right_curve()
            ... 
        
    # calculate PID
    PID, previous_erro = calculate_PID(erro, previous_erro, Kp, Kd, Ki)

    # adjust move the car
    adjust_move(PID)

if __name__ == '__main__':
    path = 'datas/lines/'
    images = [f for f in os.listdir(path) if f.endswith('.jpg')]
    
    # for a specified file
    #images = []"datas/lines/ladrilho_verde.jpg"]
    
    for image_name in images:
        print(path + image_name)
        img = cv2.imread(path + image_name)
        erro, is_curve = detect_line(img)

        image_name, type_file = image_name.split('.jpg')
        download_image(img, erro, path, image_name, is_curve)
        #print('The error in degrees:', erro)
        print(f"Memory used: {psutil.Process(os.getpid()).memory_info().rss / (1024 ** 2)} MB")
        print('-'*35)