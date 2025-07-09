#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

#define LOW 0 
#define HIGH 1

Adafruit_MPU6050 mpu;

// Pinos
const int MOTOR_LEFT_CLKWISE = 6; 
const int MOTOR_LEFT_ANTI = 9;  
const int MOTOR_RIGHT_CLKWISE = 10;  
const int MOTOR_RIGHT_ANTI = 11;

const int TRIG_PIN = 3;
const int ECHO_PIN = 4;

const int GREEN_LED_PIN = A0;
const int RED_LED_PIN = A1;
const int BTN_PIN = A2;

// String para armazenar os dados recebidos
String inputString = ""; 
bool stringComplete = false; // Flag para indicar que um comando foi recebido
bool lastButtonState = HIGH;

void setup() {
  // Inicializa a comunicação serial
  Serial.begin(9600);
  inputString.reserve(200); // Reserva memória para a string de entrada

  // Configura os pinos dos motores como saída
  pinMode(MOTOR_LEFT_CLKWISE, OUTPUT);
  pinMode(MOTOR_LEFT_ANTI, OUTPUT);
  pinMode(MOTOR_RIGHT_CLKWISE, OUTPUT);
  pinMode(MOTOR_RIGHT_ANTI, OUTPUT);

  // Configura outros pinos
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  pinMode(BTN_PIN, INPUT_PULLUP); 

  // Garante que os motores estão parados na inicialização
  controlMotor(0, 0);
  if (!mpu.begin()) {
    // Se falhar, fica piscando o LED vermelho para sempre para indicar um erro de hardware
    while (1) {
      digitalWrite(RED_LED_PIN, HIGH);
      delay(250);
      digitalWrite(RED_LED_PIN, LOW);
      delay(250);
    }
  }

  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);

  // Configura a faixa de medição do giroscópio
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);

  // Configura o filtro do sensor
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);

}

void loop() {
  bool currentButtonState = digitalRead(BTN_PIN);

  if (currentButtonState == LOW && lastButtonState == HIGH) {
      Serial.println("BTN,1"); // Envia o comando de botão pressionado
      delay(50); // Debounce
  }
  lastButtonState = currentButtonState;

  // Se um comando completo foi recebido do Pi
  if (stringComplete) {
      inputString.trim(); // Remove espaços em branco

      // Processa o comando
      if (inputString.startsWith("M")) {
      // Comando de Motor: M,velEsq,velDir
      int firstComma = inputString.indexOf(',');
      int secondComma = inputString.indexOf(',', firstComma + 1);
      
      String leftVelStr = inputString.substring(firstComma + 1, secondComma);
      String rightVelStr = inputString.substring(secondComma + 1);
      
      controlMotor(leftVelStr.toInt(), rightVelStr.toInt());
      } else if (inputString.startsWith("L")) { // Comando de LED: L,cor,estado
          int firstComma = inputString.indexOf(',');
          int secondComma = inputString.indexOf(',', firstComma + 1);
          String colorStr = inputString.substring(firstComma + 1, secondComma);
          int state = inputString.substring(secondComma + 1).toInt();

          if (colorStr == "verde") {
            digitalWrite(GREEN_LED_PIN, state);
          } else if (colorStr == "vermelho") {
            digitalWrite(RED_LED_PIN, state);
          }
      } else if (inputString.startsWith("R,dist")) { // Requisição de Distância
          int distancia = calcula_distancia();
          Serial.print("D,");
          Serial.println(distancia); // Responde com a distância
      } else if (inputString.startsWith("R,imu")) {
          sensors_event_t a, g, temp;
          mpu.getEvent(&a, &g, &temp);
          // Formato da Resposta: "I,ax,ay,az,gx,gy,gz\n"
          Serial.print("I,");
          Serial.print(a.acceleration.x); Serial.print(",");
          Serial.print(a.acceleration.y); Serial.print(",");
          Serial.print(a.acceleration.z); Serial.print(",");
          Serial.print(g.gyro.x); Serial.print(",");
          Serial.print(g.gyro.y); Serial.print(",");
          Serial.println(g.gyro.z);
        }
      
      // Limpa a string para o próximo comando
      inputString = "";
      stringComplete = false;
  }
}

int calcula_distancia() {
  //filtro para a leitura do sensor
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  unsigned long duracao = pulseIn(ECHO_PIN, HIGH, 25000); 
  return duracao / 29 / 2;
}

// Função que é chamada sempre que um dado chega na serial
void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '\n') { // Fim do comando
      stringComplete = true;
    } else {
      inputString += inChar;
    }
  }
}

// Função para controlar os dois motores
void controlMotor(int leftSpeed, int rightSpeed) {
  // Controle do motor esquerdo
  if (leftSpeed >= 0) {
    analogWrite(MOTOR_LEFT_CLKWISE, leftSpeed);
    analogWrite(MOTOR_LEFT_ANTI, LOW);
  } else {
    analogWrite(MOTOR_LEFT_CLKWISE, LOW);
    analogWrite(MOTOR_LEFT_ANTI, -leftSpeed);
  }

  // Controle do motor direito
  if (rightSpeed >= 0) {
    analogWrite(MOTOR_RIGHT_CLKWISE, rightSpeed);
    analogWrite(MOTOR_RIGHT_ANTI, LOW);
  } else {
    analogWrite(MOTOR_RIGHT_CLKWISE, LOW);
    analogWrite(MOTOR_RIGHT_ANTI, -rightSpeed);
  }
}