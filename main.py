import cv2 
from picamera2 import Picamera2
from line_detection import detect_line
from robot_control import (measure_distance, avoid_obstacle, 
                           adjust_move, calculate_PID, rescue_area, turn_until_angle)
from logger import log
from constants import *
import time
from hardware_setup import red_led, green_led, motors, disconnect_all_hardware

robot_running = True
img = None

# init the cam
try:
    cam = Picamera2()
    config = cam.create_preview_configuration(main={"size": (desired_width, desired_height)}, controls={"FrameRate": 15})
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
    global img
    while True:
        try:
            # Apenas captura o array e atualiza a variável global
            img = cam.capture_array()
        except Exception as e:
            log(f"Falha ao capturar frame para o feed: {e}")
            # Uma pequena pausa antes de tentar novamente
            time.sleep(0.5)

def run_robot_control():
    # define global variables
    global robot_running, img

    # loop to read the cam
    while robot_running:
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
        erro, is_curve, has_colour = detect_line(img)
        log(f'erro: {erro} | is_curve {is_curve} | has_colour {has_colour}')

        # if not has line it try to come back of line
        if erro is None:
            # to ensure the robot don't run out the track
            start_time = time.time()
            timeout = 3

            # comeback until find a line 
            while erro is None and (time.time() - start_time < timeout) and robot_running:
                log('Lost line')
                motors.run_backward(base_right_velocity, base_left_velocity)
                time.sleep(0.05)

                # update cam image
                try:
                    # Tenta capturar uma nova imagem para reavaliar a posição
                    img = cam.capture_array()
                except Exception as e:
                    log(f"Erro na imagem tentando voltar para a linha: {e}")
                    # Se a câmera falhar aqui, não há como se recuperar, então saia do loop
                    break
                            
                # get the error to verify if has back to the line
                erro, is_curve, has_colour = detect_line(img)
            
            if erro is None:
                # lost the line and stop the motors and the car
                log("Perdeu a linha, deu merda")
                motors.stop_motor()
                robot_running = False
            
            log("Robo conseguiu voltar pra linha! ")
                

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
                    motors.turn_right(base_right_velocity, base_left_velocity)
                    turn_until_angle(90)
                elif side_curve == RIGHT:
                    log('90 degree turn on right')
                    motors.turn_left(base_right_velocity, base_left_velocity)
                    turn_until_angle(-90)

            elif colour == RED:
                log('finish line')
                # stop the car on the red line
                motors.stop_motor()
                robot_running = False
                # ALL it's run fine
                break 
        
        # verify if has a curve
        if is_curve is not None:
            if is_curve is LEFT:
                log('90 degree turn on left')
                motors.turn_left(base_right_velocity, base_left_velocity)
            elif is_curve is RIGHT:
                log('90 degree turn on right')
                motors.turn_right(base_right_velocity, base_left_velocity)
        else:
            PID = calculate_PID(erro, previous_error, Kp, Kd, Ki, pid_state)
            log(f'Pid {PID}')
            # adjust move the car
            adjust_move(PID)
        
        if erro is not None:
            previous_erro = erro
            
        # off gren led
        green_led.off()

    # restart the cam memory
    cam.release()
    # restart the motors
    disconnect_all_hardware()

if __name__ == '__main__':
    run_robot_control()