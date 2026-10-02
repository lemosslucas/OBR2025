# 🤖 OBR 2025 — Robô Autônomo de Resgate (Equipe UAILEE)

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-OS%20Linux-C51A4A?style=for-the-badge&logo=raspberry-pi&logoColor=white)](https://www.raspberrypi.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![Flask](https://img.shields.io/badge/Flask-Web%20Dashboard-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![OBR](https://img.shields.io/badge/Competi%C3%A7%C3%A3o-OBR%202025-green?style=for-the-badge)](http://www.obr.org.br/)

Repositório oficial de desenvolvimento do robô autônomo **UAILEE**, projetado e construído para competir na **Olimpíada Brasileira de Robótica (OBR 2025)** na categoria de **Resgate**.

O projeto integra visão computacional embarcada em tempo real, fusão sensorial inercial (IMU), controle dinâmico PID com compensação angular, máquina de estados para manobras complexas e servidores web para telemetria e calibração remota de sensores.

---

## 🏆 Resultados Atingidos

Durante os testes de pista oficiais e validações de percurso da Fase 1 da OBR 2025, o robô **UAILEE** atingiu resultados de alto desempenho:

* 🎯 **Pontuação Homologada em Pista:** **115 PONTOS** conquistados na pista da Fase 1 da competição.
* 🛣️ **Seguidor de Linha Robusto (PID-A):** Estabilidade contínua em retas e curvas suaves a velocidade constante, mitigando oscilações através do cálculo combinado de erro posicional e erro angular do vetor da linha.
* 🟢 **Identificação e Execução de Encruzilhadas (Marcadores Verdes):**
  * Curvas de 90° à esquerda e à direita com 100% de taxa de acerto em testes.
  * Detecção de **Beco Sem Saída** (2 marcadores verdes simultâneos) com rotação autônoma precisa de 180° e retorno pela mesma trilha.
* 🚧 **Desvio Autônomo de Obstáculos:** Detecção antecipada do obstáculo frontal com sensor ultrassônico (< 10 cm) e execução de manobra completa de contorno orientada por odometria e giroscópio com realinhamento automático na linha preta.
* 📐 **Superação Inteligente de Rampas:** Detecção da inclinação da arena via acelerômetro em tempo real ($\ge 10^\circ$), elevando o PWM para $220$ na subida (vencendo gravidade) e desacelerando para $80$ na descida (evitando perda de tração).
* 🔄 **Sistema de Auto-Recuperação de Linha:** Rotina inteligente de busca trifásica (ré curta, varredura à direita e giro amplo à esquerda) que resgata o robô em caso de desvios repentinos ou falhas na pista.
* 🛑 **Parada na Linha Vermelha:** Reconhecimento visual instantâneo do marcador vermelho e frenagem precisa no término do percurso.
* 🌐 **Calibração Remota Sem Fio:** Redução do tempo de calibração na arena de minutos para poucos segundos utilizando a interface web Flask e visualização de máscaras HSV em tempo real via Wi-Fi no Raspberry Pi.

---

## 📐 Arquitetura do Sistema

```mermaid
graph TD
    subgraph Sensores & Entrada
        CAM[Câmera Picamera2\n320x240 @ 15 FPS]
        IMU[MPU-6050 I2C\nGiroscópio + Acelerômetro]
        US[Sensor Ultrassônico HC-SR04\nTRIG / ECHO]
        BTN[Botão Físico c/ Filtro Glitch\nGPIO 17]
    end

    subgraph Processamento & Decisão (Raspberry Pi)
        VD[line_detection.py\nROI, Binarização, Contornos, HSV]
        CTRL[robot_control.py\nControlador PID-A & Máquina de Estados]
        MAIN[main.py\nLoop Principal & Threading Feed]
        LOG[logger.py\nLogs em Arquivo e Memória]
    end

    subgraph Interfaces Web & Telemetria
        CALIB[calibrator.py\nCalibrador Dinâmico HSV / Threshold]
        DASH[server_test.py\nCentral de Teste UAILEE & SSE Logs]
    end

    subgraph Atuadores & Saídas
        MOT[MotorController / Ponte H\nPWM GPIO 18, 12, 13, 6]
        SRV[Servomotores\nBraço GPIO 14 & Pá GPIO 15]
        LEDS[LEDs de Sinalização\nVerde GPIO 10 & Vermelho GPIO 9]
    end

    CAM --> VD
    VD --> CTRL
    IMU --> CTRL
    US --> CTRL
    BTN --> MAIN
    CTRL --> MOT
    CTRL --> SRV
    CTRL --> LEDS
    MAIN --> LOG
    CALIB -.-> VD
    DASH -.-> CTRL
    LOG -.-> DASH
```

---

## 🛠️ Hardware e Eletrônica

| Componente | Modelo / Especificação | Função no Robô |
| :--- | :--- | :--- |
| **Controlador Principal** | Raspberry Pi (Linux) | Processamento central, visão computacional e controle de periféricos |
| **Câmera** | Raspberry Pi Camera Module (Picamera2) | Captura contínua de imagem da pista e área de resgate (320x240 px) |
| **IMU (Giroscópio + Acelerômetro)** | MPU-6050 (Comunicação I2C, 0x68) | Medição de inclinação de rampa e integração angular no eixo Z para giros de 90° e 180° |
| **Sensor de Distância** | Ultrassônico HC-SR04 | Leitura de distância frontal em centímetros para desvio de obstáculos |
| **Motores de Tração** | Motores DC com caixa de redução | Tração diferencial do chassi |
| **Driver de Motores** | Ponte H (controlada via PWM por hardware) | Controle de sentido e velocidade dos motores esquerdo e direito |
| **Servomotores** | Micro Servos 9g / padrão | Movimentação da pá e braço coletor para a Área de Resgate |
| **LEDs de Status** | LED Difuso Verde e Vermelho | Feedback visual de inicialização, perda de linha, beco e área de resgate |
| **Botão de Controle** | Push-button com resistor pull-up | Toggle de partida e parada imediata do robô |

### Mapeamento de Pinos GPIO (`hardware_setup.py`)

| Periférico / Sinal | Pino GPIO (BCM) | Direção | Descrição |
| :--- | :---: | :---: | :--- |
| `MOTOR_LEFT_CLKWISE` | **18** | Saída | PWM motor esquerdo (sentido horário) |
| `MOTOR_LEFT_ANTI` | **12** | Saída | PWM motor esquerdo (sentido anti-horário) |
| `MOTOR_RIGHT_CLKWISE` | **13** | Saída | PWM motor direito (sentido horário) |
| `MOTOR_RIGHT_ANTI` | **6** | Saída | PWM motor direito (sentido anti-horário) |
| `TRIG` | **24** | Saída | Pulso de disparo ultrassônico (10 µs) |
| `ECHO` | **23** | Entrada | Retorno do eco ultrassônico |
| `servo_arm` | **14** | Saída | Sinal PWM servo do braço |
| `servo_shovel` | **15** | Saída | Sinal PWM servo da pá |
| `BTN_PIN` | **17** | Entrada | Botão de controle (PUD_UP, glitch filter de 5000 µs) |
| `green_led` | **10** | Saída | LED verde de status |
| `red_led` | **9** | Saída | LED vermelho de status / alerta |
| `MPU-6050 (SDA/SCL)` | **2 / 3** | I2C | Barramento I2C padrão do Raspberry Pi |

---

## 💻 Estrutura de Software e Algoritmos

### 1. Visão Computacional (`line_detection.py`)
* **Extração da Região de Interesse (ROI):** A imagem bruta de 320x240 pixels é recortada na metade inferior central para eliminar elementos espúrios fora da pista e focar estritamente na linha guia.
* **Processamento e Binarização:**
  1. Conversão de BGR para escala de cinza (`cv2.cvtColor`).
  2. Binarização invertida com limiar calibrado (`cv2.threshold` com `threshold_value = 45`).
  3. Operações morfológicas com kernel $5\times 5$: `cv2.morphologyEx` de fechamento (`MORPH_CLOSE`) para cobrir descontinuidades na fita e abertura (`MORPH_OPEN`) para eliminar ruídos.
* **Cálculo de Erro Duplo:**
  * **Erro de Posição ($P$):** A partir dos momentos de área de primeira ordem do contorno da linha ($C_x = \frac{m_{10}}{m_{00}}$), calcula o desvio em pixels em relação ao centro horizontal da câmera.
  * **Erro Angular ($A$):** Aplicação de `cv2.fitLine` no contorno para extrair o vetor diretor $(v_x, v_y)$ e calcular o ângulo da linha em relação à vertical ($\text{graus} = \arctan2(v_x, v_y) \cdot \frac{180}{\pi}$).
* **Identificação de Cores em HSV (`identify_colour`):**
  * Segmentação nos canais de Matiz (H), Saturação (S) e Brilho (V) com janelas dinâmicas e `COLOR_OFFSET`.
  * **Verde:** Identifica quadrados verdes de curva. Se houver 2 ou mais contornos com área $> \text{MIN\_AREA\_GREEN}$, sinaliza `DEAD_END` (beco); se houver 1, verifica se seu centroide está à esquerda ou à direita do centro da imagem.
  * **Vermelho:** Identifica a faixa de parada final da pista.
  * **Cinza:** Identifica o ladrilho de entrada da Área de Resgate.

### 2. Controle e Navegação (`robot_control.py`)
* **Controlador PID-A Estendido:**
  $$PID = (K_p \cdot P) + (K_i \cdot I) + (K_d \cdot D) + K_a \cdot A$$
  * $K_p = 4.0$: Ação proporcional sobre o desvio de posição.
  * $K_i = 0.0$: Ação integral com anti-windup (zerada na troca de sinal do erro).
  * $K_d = 0.0$: Ação derivativa sobre a taxa de variação do erro.
  * $K_a = 0.1$: Ação angular antecipatória, corrigindo a trajetória antes da curva acentuada.
* **Ajuste Diferencial de Motores:**
  $$V_{\text{direita}} = \text{clamp}(V_{\text{base}} - PID, 0, 255)$$
  $$V_{\text{esquerda}} = \text{clamp}(V_{\text{base}} + PID, 0, 255)$$
* **Giroscópio e Calibração de Bias:**
  * O giroscópio MPU-6050 é calibrado no repouso com 200 amostras (`calibrate_gyro`). A função `turn_until_angle` integra $\Delta t \cdot (\omega_z - \text{bias}_z)$ para rotações perfeitas de 90° e 180°.
* **Compensação Dinâmica de Rampas:**
  * Leitura da inclinação através de $\arctan2(a_y, a_z)$. Se $\text{inclinação} \ge 10^\circ$, aciona potência de subida ($V = 220$). Se $\le -10^\circ$, reduz a velocidade para $V = 80$.
* **Desvio de Obstáculos:**
  * Manobra autônoma: Stop $\to$ Giro 90° Esq $\to$ Avanço $\to$ Giro 90° Dir $\to$ Avanço $\to$ Giro 90° Dir $\to$ Avanço $\to$ Giro 90° Esq $\to$ Busca e re-enquadramento da linha.

### 3. Detecção de Vítimas na Área de Resgate (`ball_detection.py`)
* Detecção geométrica de círculos via **Transformada de Hough para Círculos** (`cv2.HoughCircles`).
* Aplicação de máscara circular para calcular a cor média HSV e classificar vítimas vivas (prateadas/cinzas) e mortas (pretas) para transporte até a área de salvamento.

---

## 🌐 Interfaces Web e Telemetria

### 1. Calibrador em Tempo Real (`calibrator.py`)
Servidor Flask (`http://<ip_do_raspberry>:5000`) desenvolvido para facilitar a regulagem na pista de competição:
* **Streaming MJPEG:** Vídeo da câmera com sobreposição dos contornos e caixas delimitadoras coloridas.
* **Visualização de Máscaras:** Feeds dedicados para visualizar a imagem binária da linha (`/processed_feed/threshold`) e máscaras individuais para Verde, Vermelho e Cinza.
* **Amostrador HSV Interativo:** Permite clicar ou enviar coordenadas de uma região (ROI) para ler a cor média em HSV diretamente do ambiente de prova.
* **Ajuste Dinâmico:** Sliders para calibrar limites de threshold e ranges HSV sem necessidade de reiniciar a aplicação.

### 2. Central de Teste UAILEE (`server_test.py`)
Dashboard unificado para controle e diagnóstico do robô em operação:
* **Comandos Remotos:** Botões de `Começar` e `Parar` com inicialização de thread de controle assíncrona.
* **Ajuste Fino de Parâmetros:** Controle deslizante para $K_p, K_i, K_d, K_a$ e threshold.
* **Telemetria de Sistema:** Monitoramento contínuo de uso de CPU, memória RAM, temperatura do processador (`/sys/class/thermal/thermal_zone0/temp`) e estado de subtensão/throttling da fonte (`vcgencmd get_throttled`).
* **Console de Logs SSE:** Terminal web ao vivo recebendo mensagens em tempo real via Server-Sent Events.

---

## 📁 Estrutura de Diretórios do Projeto

```
OBR2025/
├── constants.py           # Definição de constantes, velocidades, pinos e parâmetros PID
├── hardware_setup.py      # Inicialização de GPIO, pigpio, sensores (MPU-6050, HC-SR04) e LEDs
├── motors.py              # Classe MotorController para acionamento PWM de motores DC
├── line_detection.py      # Algoritmos de visão computacional (linha, curvas e marcadores HSV)
├── ball_detection.py      # Detecção de esferas com Hough Circles e classificação de vítimas
├── robot_control.py       # Funções de PID, manobras especiais (obstáculo, beco, rampa, giros)
├── main.py                # Ponto de entrada principal da operação autônoma do robô
├── calibrator.py          # Servidor Flask de calibração de visão e HSV em tempo real
├── server_test.py         # Dashboard web "Central de Teste UAILEE" com telemetria e SSE
├── logger.py              # Módulo de logging seguro thread-safe com gravação em disco
├── teste.py / teste123.py # Scripts de teste de bancada individual para cada atuador e sensor
├── testecam.py            # Script rápido para validação da captura com Picamera2
├── datas/                 # Banco de dados de imagens capturadas para testes de bancada
│   ├── lines/             # Ladrilhos de curvas, encruzilhadas e analisados
│   ├── balls/             # Imagens de teste com bolinhas de resgate
│   └── reliefs/           # Imagens de testes com obstáculos e relevos
├── logs/                  # Registros textuais das execuções em tempo real do robô
├── pdfs/                  # Documentações técnicas em PDF e notebooks Jupyter exportados
│   ├── notebooks/         # Notebooks (.ipynb) de modelagem de visão computacional
│   ├── code-documentation.pdf
│   ├── eletronic-documentation.pdf
│   ├── line-detection.pdf
│   └── model-to-detect-balls.pdf
├── static/                # Arquivos CSS e JavaScript para os dashboards web Flask
└── templates/             # Templates HTML (index.html e calibrator.html)
```

---

## 🚀 Como Executar o Projeto

### Pré-requisitos
No Raspberry Pi com Raspberry Pi OS (Linux):
```bash
# Instalar dependências de sistema e Python
sudo apt-get update
sudo apt-get install python3-pip pigpio python3-pigpio python3-opencv

# Instalar bibliotecas Python necessárias
pip3 install flask picamera2 mpu6050-raspberrypi psutil numpy
```

### 1. Iniciar o Daemon de GPIO (`pigpiod`)
O controle de PWM dos motores e servos utiliza o daemon `pigpio`:
```bash
sudo pigpiod
```

### 2. Executar o Robô em Modo Autônomo
Para rodar a rotina de competição diretamente no robô com acionamento pelo botão físico:
```bash
python3 main.py
```
> O robô inicializará a câmera e fará a calibração do giroscópio (mantenha o robô parado por ~2 segundos). Ao pressionar o botão de partida (GPIO 17), o LED verde piscará e a navegação começará.

### 3. Executar o Servidor de Calibração
Para calibrar as cores das curvas e threshold na iluminação da arena:
```bash
python3 calibrator.py
```
Acesse pelo navegador do computador ou celular conectado na mesma rede: `http://<IP_DO_RASPBERRY>:5000`

### 4. Executar a Central de Teste e Telemetria
Para monitorar a telemetria, ajustar constantes PID e acionar o robô via web:
```bash
python3 server_test.py
```
Acesse: `http://<IP_DO_RASPBERRY>:5000`

---

## 👥 Equipe e Autores

Projeto desenvolvido para a **OBR 2025**:
* **Lucas Lemos Ricaldoni** ([@lemosslucas](https://github.com/lemosslucas))
* **Mateus Pedrosa** ([@mateusdcp13](https://github.com/mateusdcp13))
* **Equipe UAILEE**
