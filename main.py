import cv2 
from line_detection import detect_line, process_image
from robot_control import (measure_distance, avoid_obstacle, calibrate_gyro,
                           adjust_move, calculate_PID, led_feedback, turn_90, try_comeback_line,
                           read_accelerometer, do_dead_end)
from logger import log
from constants import *
import constants
import time
from hardware_setup import red_led, green_led, motors, disconnect_all_hardware, pi
from threading import Thread

from picamera2 import Picamera2
import pigpio

robot_running = False
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
except IndexError as e:
    log('deu erro')
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

def toggle_robot_state(gpio, level, tick):
    global robot_running
    # Inverte o estado (True -> False, False -> True)
    robot_running = not robot_running 
    
    if robot_running:
        log("Btn pressionado, ligando")
        led_feedback(green_led, START_ROBOT)
        red_led.off()
    else:
        log("Btn pressionado, parando")
        motors.stop_motor()
        red_led.on()

pi.callback(BTN_PIN, pigpio.FALLING_EDGE, toggle_robot_state)
gyro_bias_z = calibrate_gyro(300)


def run_robot_control():
    # define global variables
    global robot_running, img
    error_none = 0

    # loop to read the cam
    while robot_running:
        red_led.off()
        
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
        error, is_curve, has_colour, _ = detect_line(img, img_roi)
        log(f'erro: {error} | is_curve {is_curve} | has_colour {has_colour}')

        # if not has line it try to come back of line
        angulo = read_accelerometer()
        
        # avoid false positive
        if error is None and (angulo <= ramp_slope or angulo >= -ramp_slope):
            error_none += 1        

        if error_none >= FRAMES_TO_LOST:
            error_none = 0
            log("Perdeu a linha, deu merda")
            motors.stop_motor()
            led_feedback(red_led, LINE_LOST)

            # try forward
            if try_comeback_line(motors.run_backward, get_current_img, duration=2):
                led_feedback(green_led, LINE_FOUND)
                continue 
                
            # try turn right
            if try_comeback_line(motors.turn_right, get_current_img, duration=2.0):
                led_feedback(green_led, LINE_FOUND) 
                continue

            # try turn left
            if try_comeback_line(motors.turn_left, get_current_img, duration=2.0):
                led_feedback(green_led, LINE_FOUND)
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
                led_feedback(red_led, GIVEWAY_RESCUE)

            # verify if has a 90°curve
            elif colour == GREEN:
                # turn on the correct side
                if side_curve == LEFT:
                    log('90 degree turn on left')
                    turn_90(motors.turn_left, gyro_bias_z, get_current_img)
                elif side_curve == RIGHT:
                    log('90 degree turn on right')
                    turn_90(motors.turn_right, gyro_bias_z, get_current_img)
                elif side_curve == DEAD_END:
                    do_dead_end(gyro_bias_z)

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
                turn_90(motors.turn_left, gyro_bias_z, get_current_img)
                
            elif is_curve is RIGHT:
                log('90 degree turn on right')
                turn_90(motors.turn_right, gyro_bias_z, get_current_img)
                
        else:
            PID = calculate_PID(error, constants.previous_error, constants.Kp, constants.Kd, constants.Ki, pid_state)

            # verify if the robot is on the ramp and adjust the velociry
            if angulo >= ramp_slope:
                print('subindo: ', angulo)
                adjust_move(PID, velocity_ramp, velocity_ramp)
            elif angulo <= -ramp_slope:
                print('descendo: ', angulo)
                adjust_move(PID, velocity_ramp_down, velocity_ramp_down)
            else:
                # adjust move the car
                adjust_move(PID, base_right_velocity, base_left_velocity)
            
            if error is not None:
                constants.previous_error = error[0]

    # turn off the leds
    red_led.on()

if __name__ == '__main__':
    print('esperando  o sinal')

    log("Iniciando a thread do feed da câmera...")
    camera_thread = Thread(target=update_camera_feed, daemon=True)
    camera_thread.start()

    try:
        while True:
            # if true, run the contol.
            if robot_running:
                run_robot_control()

    except KeyboardInterrupt:
        log("parei pelo teclado")
    finally:
        disconnect_all_hardware()
