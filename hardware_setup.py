import serial
import time
from logger import log 
from threading import Lock

# connect with arduino
try:
    ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
    time.sleep(2)
    log("Conexão com Arduino estabelecida.")
except serial.SerialException as e:
    log(f"Erro ao conectar com o Arduino: {e}")
    ser = None

serial_lock = Lock()
