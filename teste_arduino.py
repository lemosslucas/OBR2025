import serial
import time

porta = '/dev/ttyUSB0'  # ou /dev/ttyACM0

arduino = serial.Serial(porta, 9600, timeout=1)
time.sleep(2)  # aguarda o Arduino reiniciar após conexão USB

# Liga o LED
arduino.write(b'LED_ON\n')
resposta = arduino.readline().decode().strip()
print("Arduino:", resposta)

# Aguarda 5 segundos com o LED ligado
time.sleep(5)

# Desliga o LED
arduino.write(b'LED_OFF\n')
resposta = arduino.readline().decode().strip()
print("Arduino:", resposta)

arduino.close()

