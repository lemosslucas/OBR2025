import cv2 
from line_detection import detect_line, process_image
from robot_control import (measure_distance, avoid_obstacle,
                           adjust_move, calculate_PID, led_feedback, turn_90, try_comeback_line,
                           read_accelerometer, do_dead_end, set_led, motors)
from logger import log
from constants import *
import constants
import time
from hardware_setup import ser, serial_lock
from threading import Thread

from picamera2 import Picamera2 

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
    set_led('verde', 1)
except RuntimeError as e:
    log('Deu erro na camera')
    set_led('vermelho', 1)
except IndexError as e:
    log('deu erro')
    set_led('vermelho', 1)


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

def run_robot_control():
    # define global variables
    global robot_running, img
    error_none = 0

    # loop to read the cam
    while robot_running:
        set_led('vermelho', 0)
        
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
            avoid_obstacle(cam)
        
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
            led_feedback("verde", LINE_LOST)

            # try forward
            if try_comeback_line(motors.run_backward, get_current_img, duration=2):
                led_feedback("verde", LINE_FOUND)
                continue 
                
            # try turn right
            if try_comeback_line(motors.turn_right, get_current_img, duration=2.0):
                led_feedback("verde", LINE_FOUND) 
                continue

            # try turn left
            if try_comeback_line(motors.turn_left, get_current_img, duration=2.0):
                led_feedback("verde", LINE_FOUND)
                continue

            log("Não foi possível recuperar a linha.")
            motors.stop_motor()
            set_led('vermelho', 1)
            robot_running = False    
            

        if has_colour is not None:
            colour, side_curve = has_colour

            # verify if is going to rescue area
            if colour == GRAY:
                log('Rescue area detected')
                led_feedback("vermelho", GIVEWAY_RESCUE)

            # verify if has a 90°curve
            elif colour == GREEN:
                # turn on the correct side
                if side_curve == LEFT:
                    log('90 degree turn on left')
                    turn_90(motors.turn_left,  get_current_img)
                elif side_curve == RIGHT:
                    log('90 degree turn on right')
                    turn_90(motors.turn_right,  get_current_img)
                elif side_curve == DEAD_END:
                    do_dead_end()

            elif colour == RED:
                log('finish line')
                # stop the car on the red line
                motors.stop_motor()
                robot_running = False
                # ALL it's run fine
                break 
        
        # verify if has a curve
        if is_curve is not False:
            if is_curve is LEFT:
                log('90 degree turn on left')
                turn_90(motors.turn_left, get_current_img)
                
            elif is_curve is RIGHT:
                log('90 degree turn on right')
                turn_90(motors.turn_right, get_current_img)
                
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
    set_led('vermelho', 0)

def listen_for_arduino():
    """Thread que ouve por mensagens do Arduino (como o botão)."""
    global robot_running
    log("Thread de escuta do Arduino iniciada.")
    while True:
        with serial_lock:
            if ser and ser.is_open and ser.in_waiting > 0:
                try:
                    # O timeout na configuração da serial faz com que não bloqueie para sempre
                    message = ser.readline().decode('utf-8').strip()
                    if message == "BTN,1":
                        robot_running = not robot_running # Inverte o estado
                        if robot_running:
                            log("Comando de partida recebido do Arduino!")
                            set_led("vermelho", 0)
                            led_feedback("verde", 2) # Pisca 2x para confirmar
                        else:
                            log("Comando de parada recebido do Arduino!")
                            motors.stop_motor()
                            set_led("vermelho", 1)
                except Exception as e:
                    # Em caso de erro de decodificação, etc.
                    time.sleep(0.1)
            else:
                # Se a serial não estiver conectada, espera um pouco
                time.sleep(0.5)
        time.sleep(0.05)


if __name__ == '__main__':
    log("Iniciando a thread do feed da câmera...")
    camera_thread = Thread(target=update_camera_feed, daemon=True)
    camera_thread.start()

    log("Iniciando a thread de escuta do Arduino...")
    arduino_listener_thread = Thread(target=listen_for_arduino, daemon=True)
    arduino_listener_thread.start()

    log("Setup completo. Aguardando comando de partida do botão...")
    set_led("verde", 1)

    try:
        while True:
            # if true, run the contol.
            if robot_running:
                run_robot_control()
            else:
                time.sleep(0.1)

    except KeyboardInterrupt:
        log("parei pelo teclado")
    
    finally:
        motors.stop_motor()
        set_led("vermelho", 1)
        if ser and ser.is_open:
            ser.close()
        log("Motores parados e programa finalizado.")
