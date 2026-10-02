from constants import servo_arm, servo_shovel, ERROR, BTN_PIN
from hardware_setup import motors, green_led, red_led, pi 
from time import sleep

def teste_leds():
    print("\n--- Teste dos LEDs ---")
    print("LED vermelho piscará 5 vezes.")
    try:
        for _ in range(5):
            red_led.on()
            sleep(0.3)
            red_led.off()
            sleep(0.3)
        
        print("LED verde piscará 5 vezes.")
        for _ in range(5):
            green_led.on()
            sleep(0.3)
            green_led.off()
            sleep(0.3)

    except KeyboardInterrupt:
        print("\nTeste dos LEDs interrompido.")
    finally:
        red_led.off()
        green_led.off()
    print("--- Fim do teste de LEDs ---")

def teste_motors():
    try:
        print("Movendo para frente (PWM 200)")
        motors.run(200, 200)
        sleep(6)

        print("Parando...")
        motors.stop_motor()
        sleep(3)
        
        print("Movendo para trás (PWM 200)")
        motors.run_backward(200, 200)
        sleep(6)

        print("Parando...")
        motors.stop_motor()
    except KeyboardInterrupt:
        motors.stop_motor()
        print("\nTeste de motor finalizado.")

def teste_rotacao():
    from robot_control import turn_until_angle
    print("Girando 90° com giroscópio MPU-6050...")
    motors.run(255, 0)
    turn_until_angle(90)
    motors.stop_motor()
    print("Rotação de 90° concluída.")

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
        print("Retornando para posição neutra (90°)...")
        pi.set_servo_pulsewidth(servo_arm, angle_to_pulse(90))
        pi.set_servo_pulsewidth(servo_shovel, angle_to_pulse(90))
    except KeyboardInterrupt:
        print("\nTeste do servo finalizado.")

def teste_ultrassonico():
    from robot_control import measure_distance
    try:
        print("Lendo distância frontal (HC-SR04)... Pressione CTRL+C para parar.")
        while True:
            distancia = measure_distance()
            if distancia == ERROR:
                print("Erro na leitura do sensor!")
            else:
                print(f"Distância: {distancia:.2f} cm")
            sleep(0.5)
    except KeyboardInterrupt:
        print("\nFim do teste do ultrassônico.")

def teste_acelerometro():
    from robot_control import read_accelerometer
    try:
        print("Lendo inclinação (acelerômetro)... Pressione CTRL+C para parar.")
        while True:
            angulo = read_accelerometer()
            print(f"Inclinação: {angulo:.2f}°")
            sleep(0.2)
    except KeyboardInterrupt:
        print("\nFim da medição de inclinação.")

def teste_botao():
    print("\n--- Teste do Botão de Partida ---")
    print("Pressione o botão físico (GPIO 17) para ver o acionamento.")
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
    while True:
        print('\n--- MENU DE TESTES DO ROBÔ ---')
        print('(1) - Testar LEDs (Vermelho e Verde)')
        print('(2) - Testar Acelerômetro (Inclinação de Rampa)')
        print('(3) - Testar Servos (Braço e Pá)')
        print('(4) - Testar Sensor Ultrassônico (Distância)')
        print('(5) - Testar Motores DC (Frente / Trás)')
        print('(6) - Testar Rotação 90° com Giroscópio')
        print('(7) - Testar Botão de Partida')
        print('(0) - Sair')

        try:
            opcao = int(input('Escolha o componente a ser testado: '))
            
            if opcao == 1:
                teste_leds()
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
            elif opcao == 0:
                print("Encerrando testes.")
                break
            else:
                print("Opção inválida, tente novamente.")
        except ValueError:
            print("Digite um número válido.")
        except KeyboardInterrupt:
            print("\nEncerrando testes.")
            break
