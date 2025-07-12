from constants import ERROR
from hardware_setup import motors, green_led, red_led, pi 
from time import  sleep

def teste_led(led):
    try:    
        while True:
            led.on()         # Acende o LED
            sleep(0.5)       # Espera 0.5 segundo
            led.off()        # Apaga o LED
            sleep(0.5)       # Espera 0.5 segundo

    except KeyboardInterrupt:
        print("\nLED APAGADO.")
        led.off()

def teste_motors():
    try:
        print("Movendo para frente")
        motors.run(200, 200)
        sleep(6)

        print('parou')
        motors.stop_motor()
        sleep(3)
        
        print("Movendo para trás")
        motors.run_backward(200, 200)
        sleep(6)

        print("Parando")
        motors.stop_motor()
    except KeyboardInterrupt:
        print('Teste motor finalizdo')

def teste_rotacao():
    from robot_control import turn_until_angle
    print("Girando 90°")
    motors.run(255, 0)
    turn_until_angle(90)
    motors.stop_motor()

def teste_servo():
    from robot_control import angle_to_pulse
    try:
        print("Movendo braço para 45°")
        pi.set_servo_pulsewidth(servo_arm, angle_to_pulse(45))
        sleep(1)

        print("Movendo pá para 35°")
        pi.set_servo_pulsewidth(servo_shovel, angle_to_pulse(35))
        sleep(1)

        # Reset
        pi.set_servo_pulsewidth(servo_arm, angle_to_pulse(90))
        pi.set_servo_pulsewidth(servo_shovel, angle_to_pulse(90))
    except KeyboardInterrupt:
        print("Teste do servo finalizado")

def teste_ultrassonico():
    from robot_control import measure_distance
    try:
        print("Lendo distância")
        distancia = measure_distance()

        if distancia == ERROR:
            print("Erro na leitura do sensor!")
        else:
            print(f"Distância: {distancia:.2f} cm")
    except KeyboardInterrupt:
        print("\nFim do teste do ultrassonico")

def teste_acelerometro():
    from robot_control import read_accelerometer
    try:
        while True:
            angulo = read_accelerometer()
            print(f"Inclinação: {angulo:.2f}°")
    except KeyboardInterrupt:
        print('Fim da mediçaõ da inclinação')

def teste_botao():
    # Importa o pino do botão e o objeto 'pi' da configuração
    from constants import BTN_PIN
    from hardware_setup import pi
    from time import sleep

    print("\n--- Teste do Botão ---")
    print("Pressione o botão para ver a mensagem.")
    print("Pressione CTRL+C para voltar ao menu principal.")
    
    try:
        while True:
            if pi.read(BTN_PIN) == 0:
                print(">>> Botão Pressionado! <<<")
                sleep(0.5) 
            
            sleep(0.05)

    except KeyboardInterrupt:
        print("\n--- Fim do teste do botão ---")

if __name__ == '__main__':
    opcao = 1

    while opcao != 0:
        print('Escolha o componente a ser testado\n'
        '(1) - LED\n(2) - Acelerometro\n(3) - Servo\n(4) - Ultrassonico\n(5) - Motor\n(6) - Rotaçao dos motors\n' \
        '(0) - Sair')

        opcao = int(input(''))
        
        if opcao == 1:
            print('Led Vermelho')
            teste_led(red_led)
            print('Led Verde')
            teste_led(green_led)
        elif opcao == 2:
            teste_acelerometro()
        elif opcao == 3:
            teste_servo()
        elif opcao == 4:
            teste_ultrassonico()
        elif opcao == 5:
            teste_motors()
        elif opcao == 6:
            teste_rotacao()
        elif opcao == 7:
            teste_botao()
        else:
            print('digita certo')
