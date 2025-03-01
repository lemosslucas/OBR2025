#ifndef PID_H
#define PID_H

#include <stdio.h>
int calculate_PID(int erro, int previous_erro, int Kp, int Kd, int Ki);

#endif // PID_H