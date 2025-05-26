#include <pigpio.h>
#include <unistd.h>

#define LOW 0
#define DELAY_TIME 600000

// define motors ports
const int MOTOR_LEFT_CLKWISE = 18;
const int MOTOR_LEFT_ANTI = 12;
const int MOTOR_RIGHT_CLKWISE = 13;
const int MOTOR_RIGHT_ANTI = 19;

void setup_motor() {
    gpioInitialise();
    gpioSetMode(MOTOR_LEFT_CLKWISE, PI_OUTPUT);
    gpioSetMode(MOTOR_LEFT_ANTI, PI_OUTPUT);
    gpioSetMode(MOTOR_RIGHT_CLKWISE, PI_OUTPUT);
    gpioSetMode(MOTOR_RIGHT_ANTI, PI_OUTPUT);

    set_state_motor(LOW, LOW, LOW, LOW);
}

/**
 * @brief Sets the state of the motors.
 *
 * Controls the direction of each motor.
 *
 * @param leftCw LEFT motor clockwise state (PWM).
 * @param leftCcw LEFT motor counterclockwise state (PWM).
 * @param rightCw RIGHT motor clockwise state (PWM).
 * @param rightCcw RIGHT motor counterclockwise state (PWM).
 */
void set_state_motor(int leftCw, int leftCcw, int rightCw, int rightCcw) {
    gpioPWM(MOTOR_LEFT_ANTI, leftCcw);
    gpioPWM(MOTOR_LEFT_CLKWISE, leftCw);
    gpioPWM(MOTOR_RIGHT_ANTI, rightCcw);
    gpioPWM(MOTOR_RIGHT_CLKWISE, rightCw);
}

/**
 * @brief Moves the vehicle forward at the specified speeds.
 *
 * @param velocityRight Speed of the RIGHT motor (0 to 255).
 * @param velocityLeft Speed of the LEFT motor (0 to 255).
 */
void run(int velocityRight, int velocityLeft) {
    // set motor states and velocity
    set_state_motor(velocityLeft, LOW, velocityRight, LOW);
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
    set_state_motor(LOW, velocityLeft, LOW, velocityRight);  
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
    set_state_motor(velocityLeft + 40, LOW, velocityRight, LOW);
    usleep(DELAY_TIME);
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
    set_state_motor(velocityLeft, LOW, LOW, velocityRight + 40);
    usleep(DELAY_TIME);
}
