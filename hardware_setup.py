import pigpio
from gpiozero import LED
from mpu6050 import mpu6050
from motors import MotorController
from logger import log 

"""
Component's pins
"""
TRIG = 24
ECHO = 23
servo_arm = 14
servo_shovel = 15
BTN_PIN = 17

# initalize the compontens
pi = pigpio.pi()
accelerometer = mpu6050(0x68)
motors = MotorController()
green_led = LED(10)
red_led = LED(9)

# BUTTON
pi.set_mode(BTN_PIN, pigpio.INPUT)
pi.set_pull_up_down(BTN_PIN, pigpio.PUD_UP)
pi.set_glitch_filter(BTN_PIN, 5000)

# ultrassonic
try:
    pi.set_mode(TRIG, pigpio.OUTPUT)
    pi.set_mode(ECHO, pigpio.INPUT)
except Exception as e:
    log(f'Error ao configurar o ultrassonico {e}')

