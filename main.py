import cv2 
from picamera2 import Picamera2
from line_detection import detect_line, process_image
from robot_control import (measure_distance, avoid_obstacle, calibrate_gyro,
                           adjust_move, calculate_PID, rescue_area, turn_until_angle, led_feedback)
from logger import log
from constants import *
import constants
import time
from hardware_setup import red_led, green_led, motors, disconnect_all_hardware

robot_running = True
img = None

# init the cam
try:
    cam = Picamera2()
    config = cam.create_preview_configuration(main={"size": (desired_width, desired_height)}, 
                                              controls={"FrameRate": 15})
    cam.configure(config)
    cam.start()
    log('aguardando a inicializacao da camera')
    time.sleep(1)    
    log("Camera ligou")
    green_led.on()
except RuntimeError as e:
    log('Deu erro na camera')
    red_led.on()

def get_current_img():
    return img

def update_camera_feed():
    """
    Uma função simples que roda em uma thread separada
    para manter a variável global 'img' sempre atualizada.
    """
    global img, img_roi
    while True:
        try:
            # Apenas captura o array e atualiza a variável global
            img_cam = cam.capture_array()
            from robot_control import get_roi
            img_roi = get_roi(img_cam)
            img = process_image(img_roi)
        except Exception as e:
            log(f"Falha ao capturar frame para o feed: {e}")
            # Uma pequena pausa antes de tentar novamente
            time.sleep(0.5)

gyro_bias_z = calibrate_gyro(200)

def run_robot_control():
    # define global variables
    global robot_running, img

    # loop to read the cam
    while robot_running:
        led_feedback(green_led, START_ROBOT)
        # extract the cam info
        if img is None:
            log("Aguardando primeiro frame da camera")
            time.sleep(0.1)
            continue

        # verify if has an object on front
        distance_tries = 0
        distance = measure_distance()

        # read the distance 3 times
        while distance_tries <= 3:
            distance = measure_distance()
            # verify if has error on the read
            if distance == ERROR:
                log('Erro na leitura do ultrassonico')
                distance_tries += 1
                time.sleep(0.05)
            else: 
                break

        log(f'Distance {distance:.2f} cm')

        if distance is not None and distance <= MAX_DISTANCE:
            log('Avoiding obstacle')
            avoid_obstacle(cam, gyro_bias_z)
        
        # calculate the error
        erro, is_curve, has_colour = detect_line(img, img_roi)
        log(f'erro: {erro} | is_curve {is_curve} | has_colour {has_colour}')

        # if not has line it try to come back of line
        if erro is None:
            log("Perdeu a linha, deu merda")
            motors.stop_motor()
            led_feedback(red_led, LINE_LOST)

            # function to found the line
            def search_step(move_function, duration=1.5):
                start_time = time.time()
                while time.time() - start_time < duration:
                    move_function(base_right_velocity, base_left_velocity)
                    time.sleep(0.01)
                    erro, _, _ = detect_line(get_current_img(), None) # Só precisa do erro aqui
                    if erro is not None:
                        log('Voltamos')
                        led_feedback(green_led, LINE_FOUND) 
                        return True
                return False

            # try forward
            if search_step(motors.run_backward):
                continue # Volta pro loop principal

            # try turn right
            if search_step(motors.turn_right, duration=2.0): 
                continue

            # try turn left
            if search_step(motors.turn_left, duration=2.0):
                continue

            log("Não foi possível recuperar a linha.")
            motors.stop_motor()
            red_led.on()
            robot_running = False    

        if has_colour is not None:
            colour, side_curve = has_colour

            # verify if is going to rescue area
            if colour == GRAY:
                log('Rescue area detected')
                #rescue_area(cam)

            # verify if has a 90°curve
            elif colour == GREEN:
                # turn on the correct side
                if side_curve == LEFT:
                    log('90 degree turn on left')
                    motors.run(0, base_left_velocity)
                    turn_until_angle(90, gyro_bias_z=gyro_bias_z)
                elif side_curve == RIGHT:
                    log('90 degree turn on right')
                    motors.run(base_right_velocity, 0)
                    turn_until_angle(90, gyro_bias_z=gyro_bias_z)

            elif colour == RED:
                log('finish line')
                # stop the car on the red line
                motors.stop_motor()
                robot_running = False
                disconnect_all_hardware()
                # ALL it's run fine
                break 
        
        # verify if has a curve
        if is_curve is not False:
            if is_curve is LEFT:
                log('90 degree turn on left')
                motors.turn_left(base_right_velocity, base_left_velocity)
                turn_until_angle(90, gyro_bias_z=gyro_bias_z)
            elif is_curve is RIGHT:
                log('90 degree turn on right')
                motors.turn_right(base_right_velocity, base_left_velocity)
                turn_until_angle(90, gyro_bias_z=gyro_bias_z)
        else:
            PID = calculate_PID(erro, constants.previous_error, constants.Kp, constants.Kd, constants.Ki, pid_state)
            # adjust move the car
            adjust_move(PID)
        
        if erro is not None:
            constants.previous_error = erro
            
    red_led.on()

if __name__ == '__main__':
    gyro_bias_z = calibrate_gyro(200)
