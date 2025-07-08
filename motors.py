from hardware_setup import ser

def send_command(command):
    if ser and ser.is_open:
        ser.write(command.encode('utf-8'))

class MotorController:
    def run(self, velocityRight, velocityLeft):
        """Moves the robot forward with specified motor speeds."""
        cmd = f"M,{int(velocityLeft)},{int(velocityRight)}\n"
        send_command(cmd)

    def stop_motor(self):
        """Stops all motors."""
        cmd = "M,0,0\n"
        send_command(cmd)

    def run_backward(self, velocityRight, velocityLeft):
        """Moves the robot backward with specified motor speeds."""
        cmd = f"M,{-int(velocityLeft)},{-int(velocityRight)}\n"
        send_command(cmd)

    def turn_right(self, velocityRight, velocityLeft):
        """Performs a right turn."""
        # Nesse protocolo, para virar à direita, 
        # o motor esquerdo vai para frente e o direito para trás.
        cmd = f"M,{int(velocityLeft)},{-int(velocityRight)}\n"
        send_command(cmd)

    def turn_left(self, velocityRight, velocityLeft):
        """Performs a left turn."""
        cmd = f"M,{-int(velocityLeft)},{int(velocityRight)}\n"
        send_command(cmd)
