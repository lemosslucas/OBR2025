#include "motors.h"

// define motors ports
const int MOTOR_LEFT_CLKWISE = 3;
const int MOTOR_LEFT_ANTI = 4;
const int MOTOR_RIGHT_CLKWISE = 7;
const int MOTOR_RIGHT_ANTI = 8;

const int MOTOR_PWM_LEFT = 5;
const int MOTOR_PWM_RIGHT = 6;

void setup_motor() {
  pinMode(MOTOR_LEFT_CLKWISE, OUTPUT);
  pinMode(MOTOR_LEFT_ANTI, OUTPUT);
  pinMode(MOTOR_RIGHT_CLKWISE, OUTPUT);
  pinMode(MOTOR_RIGHT_ANTI, OUTPUT);

  pinMode(MOTOR_PWM_LEFT, OUTPUT);
  pinMode(MOTOR_PWM_RIGHT, OUTPUT);
}

/**
 * @brief Sets the state of the motors.
 *
 * Controls the direction of each motor.
 *
 * @param leftCw LEFT motor clockwise state (HIGH/LOW).
 * @param leftCcw LEFT motor counterclockwise state (HIGH/LOW).
 * @param rightCw RIGHT motor clockwise state (HIGH/LOW).
 * @param rightCcw RIGHT motor counterclockwise state (HIGH/LOW).
 */
void set_state_motor(int leftCw, int leftCcw, int rightCw, int rightCcw) {
    digitalWrite(MOTOR_LEFT_ANTI, leftCcw);
    digitalWrite(MOTOR_LEFT_CLKWISE, leftCw);
    digitalWrite(MOTOR_RIGHT_ANTI, rightCcw);
    digitalWrite(MOTOR_RIGHT_CLKWISE, rightCw);
}

/**
 * @brief Moves the vehicle forward at the specified speeds.
 *
 * @param velocityRight Speed of the RIGHT motor (0 to 255).
 * @param velocityLeft Speed of the LEFT motor (0 to 255).
 */
void run(int velocityRight, int velocityLeft) {
    // set motor states
    set_state_motor(HIGH, LOW, HIGH, LOW);
    // set motors velocity
    analogWrite(MOTOR_PWM_LEFT, velocityLeft);
    analogWrite(MOTOR_PWM_RIGHT, velocityRight);
}

/**
 * @brief Stops all motors, bringing the vehicle to a halt.
 */
void stop_motor() {
    // set motor states
    set_state_motor(LOW, LOW, LOW, LOW);
}

/**
 * @brief Moves the vehicle backward at the specified speeds.
 *
 * @param velocityRight Speed of the RIGHT motor (0 to 255).
 * @param velocityLeft Speed of the LEFT motor (0 to 255).
 */
void run_backward(int velocityRight, int velocityLeft) {
    // set motor states
    set_state_motor(LOW, HIGH, LOW, HIGH);  
    //set motor velocity
    analogWrite(MOTOR_PWM_LEFT, velocityLeft);
    analogWrite(MOTOR_PWM_RIGHT, velocityRight);
}

/**
 * @brief Performs a 90-degree right turn.
 *
 * Adjusts motor states and speed to execute a right turn.
 * 
 * @param velocityRight Speed of the RIGHT motor (0 to 255).
 * @param velocityLeft Speed of the LEFT motor (0 to 255).
 * @note The `delay(600)` determines the turn duration; adjust as needed.
 */
void turn_right(int velocityRight, int velocityLeft) {
    // set motor states
    set_state_motor(LOW, HIGH, HIGH, LOW);
    //set motor velocity
    analogWrite(MOTOR_PWM_LEFT, velocityLeft + 40);
    analogWrite(MOTOR_PWM_RIGHT, velocityRight);
    delay(600);
}

/**
 * @brief Performs a 90-degree left turn.
 *
 * Adjusts motor states and speed to execute a left turn.
 * 
 * @param velocityRight Speed of the RIGHT motor (0 to 255).
 * @param velocityLeft Speed of the LEFT motor (0 to 255).
 * @note The `delay(600)` determines the turn duration; adjust as needed.
 */
void turn_left(int velocityRight, int velocityLeft) {
    //set motor states
    set_state_motor(HIGH, LOW, LOW, HIGH);
    //set motor velocity
    analogWrite(MOTOR_PWM_LEFT, velocityLeft);
    analogWrite(MOTOR_PWM_RIGHT, velocityRight + 40);
    delay(600);
}