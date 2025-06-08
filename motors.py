import pigpio
import time

# Motor GPIO pins (inversed)
MOTOR_LEFT_CLKWISE = 18
MOTOR_LEFT_ANTI = 12
MOTOR_RIGHT_CLKWISE = 13
MOTOR_RIGHT_ANTI = 20

LOW = 0

class MotorController:
    def __init__(self):
        """
        Initializes the motor controller and connects to the pigpiod daemon.
        """
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("Error: pigpiod is not running!")

        self.setup_motor()

    def setup_motor(self):
        """
        Sets the GPIO modes to output and ensures all motors are stopped.
        """
        self.pi.set_mode(MOTOR_LEFT_CLKWISE, pigpio.OUTPUT)
        self.pi.set_mode(MOTOR_LEFT_ANTI, pigpio.OUTPUT)
        self.pi.set_mode(MOTOR_RIGHT_CLKWISE, pigpio.OUTPUT)
        self.pi.set_mode(MOTOR_RIGHT_ANTI, pigpio.OUTPUT)
        self.stop_motor()

    def set_state_motor(self, leftCw, leftCcw, rightCw, rightCcw):
        """
        Sets the state of the motors via PWM.

        Args:
            leftCw (int): LEFT motor clockwise speed (0–255).
            leftCcw (int): LEFT motor counterclockwise speed (0–255).
            rightCw (int): RIGHT motor clockwise speed (0–255).
            rightCcw (int): RIGHT motor counterclockwise speed (0–255).
        """
        self.pi.set_PWM_dutycycle(MOTOR_LEFT_ANTI, leftCcw)
        self.pi.set_PWM_dutycycle(MOTOR_LEFT_CLKWISE, leftCw)
        self.pi.set_PWM_dutycycle(MOTOR_RIGHT_ANTI, rightCcw)
        self.pi.set_PWM_dutycycle(MOTOR_RIGHT_CLKWISE, rightCw)

    def run(self, velocityRight, velocityLeft):
        """
        Moves the robot forward with specified motor speeds.

        Args:
            velocityRight (int): RIGHT motor speed (0–255).
            velocityLeft (int): LEFT motor speed (0–255).
        """
        self.set_state_motor(velocityLeft, LOW, velocityRight, LOW)

    def stop_motor(self):
        """
        Stops all motors, bringing the robot to a halt.
        """
        self.set_state_motor(LOW, LOW, LOW, LOW)

    def run_backward(self, velocityRight, velocityLeft):
        """
        Moves the robot backward with specified motor speeds.

        Args:
            velocityRight (int): RIGHT motor speed (0–255).
            velocityLeft (int): LEFT motor speed (0–255).
        """
        self.set_state_motor(LOW, velocityLeft, LOW, velocityRight)

    def turn_right(self, velocityRight, velocityLeft):
        """
        Performs a 90-degree right turn.

        Args:
            velocityRight (int): RIGHT motor speed (0–255).
            velocityLeft (int): LEFT motor speed (0–255).

        """
        self.set_state_motor(velocityLeft, LOW, LOW, velocityRight)

    def turn_left(self, velocityRight, velocityLeft):
        """
        Performs a 90-degree left turn.

        Args:
            velocityRight (int): RIGHT motor speed (0–255).
            velocityLeft (int): LEFT motor speed (0–255).

        """
        self.set_state_motor(LOW, velocityLeft, velocityRight, LOW)

    def disconect(self):
        """
        Stops all motors and disconnects from the pigpiod daemon.
        """
        self.stop_motor()
        self.pi.stop()
