import time
# Importa as funções e objetos necessários que se comunicam via serial
from robot_control import (measure_distance, read_accelerometer, 
                           turn_until_angle, motors)
from motors import send_command # Usaremos para o novo teste do servo
from constants import ERROR

# Esta função agora usa o mesmo comando serial do projeto principal
def teste_leds():
    print("\n--- Teste dos LEDs ---")
    print("LED vermelho piscará 5 vezes.")
    try:
        for _ in range(5):
            send_command("L,vermelho,1\n") # Liga o LED vermelho
            time.sleep(0.3)
            send_command("L,vermelho,0\n") # Desliga
            time.sleep(0.3)
        
        print("LED verde piscará 5 vezes.")
        for _ in range(5):
            send_command("L,verde,1\n") # Liga o LED verde
            time.sleep(0.3)
            send_command("L,verde,0\n") # Desliga
            time.sleep(0.3)

    except KeyboardInterrupt:
        print("\nTeste de LED interrompido.")
    finally:
        # Garante que os LEDs terminem desligados
        send_command("L,vermelho,0\n")
        send_command("L,verde,0\n")
    print("--- Fim do teste de LEDs ---")


def teste_motors():
    print("\n--- Teste dos Motores ---")
    try:
        print("Movendo para frente por 2 segundos...")
        motors.run(150, 150)
        time.sleep(2)

        print('Parando por 1 segundo...')
        motors.stop_motor()
        time.sleep(1)
        
        print("Movendo para trás por 2 segundos...")
        motors.run_backward(150, 150)
        time.sleep(2)

        print("Parando.")
        motors.stop_motor()
    except KeyboardInterrupt:
        print('\nTeste de motor finalizado pelo usuário.')
    finally:
        motors.stop_motor()
    print("--- Fim do teste dos Motores ---")


def teste_rotacao():
    print("\n--- Teste de Rotação (Giroscópio) ---")
    try:
        print("Girando 90 graus para a direita...")
        # Para girar para a direita, o motor esquerdo vai para frente e o direito para trás
        motors.turn_right(200, 200)
        turn_until_angle(90, gyro_bias_z=0) # Usando o bias do seu main.py
        
        time.sleep(1) # Pausa

        print("Girando 90 graus para a esquerda...")
        motors.turn_left(200, 200)
        turn_until_angle(90, gyro_bias_z=0)

    except KeyboardInterrupt:
        print('\nTeste de rotação finalizado pelo usuário.')
    finally:
        motors.stop_motor()
    print("--- Fim do teste de rotação ---")


def teste_ultrassonico():
    print("\n--- Teste do Ultrassônico ---")
    try:
        print("Realizando uma leitura de distância...")
        distancia = measure_distance()

        if distancia == 999 or distancia == ERROR:
            print("Erro na leitura do sensor! Verifique a conexão.")
        else:
            print(f"Distância medida: {distancia:.2f} cm")
    except KeyboardInterrupt:
        print("\nFim do teste do ultrassônico.")
    print("--- Fim do teste do ultrassônico ---")


def teste_acelerometro():
    print("\n--- Teste do Acelerômetro (Inclinação) ---")
    print("Pressione CTRL+C para parar.")
    try:
        while True:
            angulo = read_accelerometer()
            # O read_accelerometer já trata o erro, então podemos imprimir diretamente
            print(f"Ângulo de inclinação (eixo Y): {angulo:.2f}°", end='\r')
            time.sleep(0.2)
    except KeyboardInterrupt:
        print('\n--- Fim da medição da inclinação ---')


# Esta função agora testa o botão da maneira que o projeto funciona:
# lendo a mensagem serial enviada pelo Arduino.
def teste_botao():
    from hardware_setup import ser
    print("\n--- Teste do Botão ---")
    print("Pressione o botão no robô para ver a mensagem.")
    print("Pressione CTRL+C para voltar ao menu.")
    
    try:
        while True:
            if ser and ser.is_open:
                message = ser.readline().decode('utf-8').strip()
                if message == "BTN,1":
                    print(">>> Mensagem 'BTN,1' recebida do Arduino! Teste OK! <<<")
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n--- Fim do teste do botão ---")

if __name__ == '__main__':
    # Garante que as correções de bugs do IMU sejam aplicadas
    print("Lembrete: Certifique-se de que os bugs no arquivo 'robot_control.py' foram corrigidos para os testes de rotação e acelerômetro funcionarem.")
    
    while True:
        print('\n--- MENU DE TESTES DO ROBÔ ---')
        print('(1) - Testar LEDs')
        print('(2) - Testar Acelerômetro (Inclinação)')
        print('(4) - Testar Sensor Ultrassônico')
        print('(5) - Testar Motores (Frente/Trás)')
        print('(6) - Testar Rotação com Giroscópio')
        print('(7) - Testar Botão de Partida')
        print('(0) - Sair')

        try:
            opcao = int(input('Escolha o componente a ser testado: '))
            
            if opcao == 1:
                teste_leds()
            elif opcao == 2:
                teste_acelerometro()
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
