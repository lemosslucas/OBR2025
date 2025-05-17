from gpiozero import LED
from time import sleep

# Cria o objeto LED conectado ao GPIO 23
led = LED(23)

try:
    print("Piscando LED no GPIO 23... Pressione Ctrl+C para parar.")
    while True:
        led.on()         # Acende o LED
        sleep(0.5)       # Espera 0.5 segundo
        led.off()        # Apaga o LED
        sleep(0.5)       # Espera 0.5 segundo

except KeyboardInterrupt:
    print("\nPrograma encerrado pelo usuário.")
    led.off()
