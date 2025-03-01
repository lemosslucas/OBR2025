#include <stdio.h>

/**
 * @brief Computes the PID control output based on the given error values and PID constants.
 *
 * The PID control formula is:
 *     PID = (Kp * P) + (Ki * I) + (Kd * D)
 *
 * where:
 *     - P (Proportional) is the current error.
 *     - I (Integral) accumulates past errors, clamped between -255 and 255.
 *     - D (Derivative) is the rate of change of the error.
 *
 * @param error The current error value.
 * @param previous_error The error from the previous iteration.
 * @param Kp The proportional gain constant.
 * @param Kd The derivative gain constant.
 * @param Ki The integral gain constant.
 *
 * @return The computed PID output.
 */
int calculate_PID(int erro, int previous_erro, int Kp, int Kd, int Ki) {
    // define param values
    int PID = 0;
    int P = erro;
    static int I = 0;
    // limit the I on -255:255
    I = I + P;
    if (I > 255) {I = 255;}
    if (I < -255) {I = -255;}

    int D = erro - previous_erro;
  
    // calculate the PID
    PID = (Kp * P) + (Ki * I) + (Kd * D);
  
    // atualiza o valor do PID
    return PID;
}