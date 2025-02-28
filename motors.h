#ifndef MOTORS_H
#define MOTORS_H

#include <Arduino.h>

// Define motor control functions
void setup_motor();
void run(int velocityRight, int velocityLeft);
void stop_motor();
void run_backward(int velocityRight, int velocityLeft);
void turn_right(int velocityRight, int velocityLeft);
void turn_left(int velocityRight, int velocityLeft);

#endif
