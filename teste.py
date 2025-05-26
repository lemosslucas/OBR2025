from gpiozero import LED
from mpu6050 import mpu6050
from time import sleep

from robot_control import *
from motors import MotorController

# define os pinos
led_verde = LED(23)
led_vermelho = LED(24)

# define ultrassonic Pins
TRIG = 22
ECHO = 27

# set pins
pi.set_mode(TRIG, pigpio.OUTPUT)
pi.set_mode(ECHO, pigpio.INPUT)

#set servo pins
servo_arm = 14
servo_shovel = 15

# initialize the accelerometer
accelerometer = mpu6050(0x68)

def teste_led(led):
    try:
        print("Piscando LED no GPIO 23... Pressione Ctrl+C para parar.")
        while True:
            led.on()         # Acende o LED
            sleep(0.5)       # Espera 0.5 segundo
            led.off()        # Apaga o LED
            sleep(0.5)       # Espera 0.5 segundo

    except KeyboardInterrupt:
        print("\nLED APAGADO.")
        led.off()

motores = MotorController()
def teste_motores():
    print("Movendo para frente")
    motores.run(180, 180)
    time.sleep(2)

    print("Movendo para trás")
    motores.run_backward(180, 180)
    time.sleep(2)

    print("Parando")
    motores.stop_motor()

def teste_rotacao():
    print("Girando 90°")
    motores.run(255, 0)
    turn_until_angle(90)
    motores.stop_motor()

def teste_servo():
    print("Movendo braço para 45°")
    pi.set_servo_pulsewidth(servo_arm, angle_to_pulse(45))
    time.sleep(1)

    print("Movendo pá para 35°")
    pi.set_servo_pulsewidth(servo_shovel, angle_to_pulse(35))
    time.sleep(1)

    # Reset
    pi.set_servo_pulsewidth(servo_arm, angle_to_pulse(90))
    pi.set_servo_pulsewidth(servo_shovel, angle_to_pulse(90))

def teste_ultrassonico():
    print("Lendo distância...")
    distancia = measure_distance()
    if distancia == ERROR:
        print("Erro na leitura do sensor!")
    else:
        print(f"Distância: {distancia:.2f} cm")

def teste_acelerometro():
    angulo = read_accelerometer()
    print(f"Inclinação: {angulo:.2f}°")

if __name__ == '__main__':
    opcao = 1

    while opcao != 0:
        print('Escolha o componente a ser testado\n'
        '(1) - LED\n(2) - Acelerometro\n(3) - Servo\n(4) - Ultrassonico\n(5) - Motor\n(6) - Rotaçao dos motores')

        opcao = int(input(''))
        
        if opcao == 1:
            print('Led Vermelho')
            teste_led(led_vermelho)
            print('Led Verde')
            teste_led(led_verde)
        elif opcao == 2:
            teste_acelerometro()
        elif opcao == 3:
            teste_servo()
        elif opcao == 4:
            teste_ultrassonico()
        elif opcao == 5:
            teste_motores()
        elif opcao == 6:
            teste_rotacao()