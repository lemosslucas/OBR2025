import pigpio
from gpiozero import LED
from mpu6050 import mpu6050
from motors import MotorController
from constants import TRIG, ECHO
from logger import log 

# initalize the compontens
pi = pigpio.pi()
accelerometer = mpu6050(0x68)
motors = MotorController()

green_led = LED(9)
red_led = LED(10)
headlight = LED(5) # conferir a porta

# ultrassonic
try:
    pi.set_mode(TRIG, pigpio.OUTPUT)
    pi.set_mode(ECHO, pigpio.INPUT)
except Exception as e:
    log(f'Error ao configurar o ultrassonico {e}')

def disconnect_all_hardware():
    """
        Clean all components.
    """
    log('Componentes disconectados!')
    motors.disconect() 
    pi.stop() 

    try:
        green_led.close()
        red_led.close()
    except Exception as e:
        log(f"Erro ao fechar LEDs: {e}")
