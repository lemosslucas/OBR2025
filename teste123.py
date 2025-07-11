from constants import servo_arm, servo_shovel, ERROR
from hardware_setup import motors, green_led, red_led, pi 
from time import sleep

def teste_leds():
    print("\n--- Teste dos LEDs ---")
    print("LED vermelho piscará 5 vezes.")
    try:
        for _ in range(5):
            red_led.on()         # Acende o LED vermelho
            sleep(0.3)           # Espera 0.3 segundo
            red_led.off()      # Apaga o LED vermelho
            sleep(0.3)           # Espera 0.3 segundo
        
        print("LED verde piscará 5 vezes.")
        for _ in range(5):
            green_led.on()       # Acende o LED verde
            sleep(0.3)           # Espera 0.3 segundo
            green_led.off()      # Apaga o LED verde
            sleep(0.3)           # Espera 0.3 segundo

    except KeyboardInterrupt:
        print("\nTeste dos LEDs interrompido.")
    finally:
        # Garante que os LEDs terminem desligados
        red_led.off()
        green_led.off()
    print("--- Fim do teste de LEDs ---")

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

    while True:
        print('\n--- MENU DE TESTES DO ROBÔ ---')
        print('(1) - Testar LEDs')
        print('(2) - Testar Acelerômetro (Inclinação)')
        # print('(3) - Testar Servos')
        print('(4) - Testar Sensor Ultrassônico')
        print('(5) - Testar Motores (Frente/Trás)')
        print('(6) - Testar Rotação com Giroscópio')
        print('(7) - Testar Botão de Partida')
        print('(0) - Sair')

        try:
            opcao = int(input('Escolha o componente a ser testado: '))
            
            if opcao == 1:
                teste_leds()
                # print('Led Vermelho')
                # teste_led(red_led)
                # print('Led Verde')
                # teste_led(green_led)
            elif opcao == 2:
                teste_acelerometro()
            # elif opcao == 3:
            #     teste_servo()
            elif opcao == 4:
                teste_ultrassonico()
            elif opcao == 5:
                teste_motors()
            elif opcao == 6:
                teste_rotacao()
            elif opcao == 7:
                teste_botao()
            elif opcao == 0:
                print("Saindo do programa de testes.")
                break
            else:
                print('Opção inválida. Tente novamente.')
        
        except ValueError:
            print("Entrada inválida. Por favor, digite um número.")
        
        # Pausa para o usuário ler a saída antes de mostrar o menu novamente
        input("\nPressione Enter para continuar...")