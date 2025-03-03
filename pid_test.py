import ctypes
import os
import time

# Carrega a DLL
pid_dll = ctypes.CDLL("./c_files/PID2.dll")

# Define os tipos dos argumentos e o tipo de retorno da função
pid_dll.calculate_PID.argtypes = (ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int)
pid_dll.calculate_PID.restype = ctypes.c_int

def calculate_PID(erro, previous_erro, Kp, Kd, Ki):
    """
    Computes the PID control output based on the given error values and PID constants.

    The PID control formula is:
        PID = (Kp * P) + (Ki * I) + (Kd * D)
    
    where:
        - P (Proportional) is the current error.
        - I (Integral) accumulates past errors, clamped between -255 and 255.
        - D (Derivative) is the rate of change of the error.

    Parameters:
        error (int): The current error value.
        previous_error (int): The error from the previous iteration.
        Kp (int): The proportional gain constant.
        Kd (int): The derivative gain constant.
        Ki (int): The integral gain constant.

    Returns:
        tuple: A tuple containing:
            - PID (int): The computed PID output.
            - previous_erro (int): The updated previous error.
    """
    # define param values
    PID = 0; I = 0; P = erro
    # limit the I on -255:255
    I = max(-255, min(I + P, 255))
    D = erro - previous_erro

    # calculate the PID
    PID = (Kp * P) + (Ki * I) + (Kd * D)

    # update the value of erro
    previous_erro = erro
    
    # return PID, previous_erro
    return PID, previous_erro

# Exemplo de uso da função
erro = 10
previous_erro = 5
Kp = 1
Kd = 2
Ki = 3

# Mede tempo médio em múltiplas execuções
num_execucoes = 100000

start_time = time.perf_counter()
for _ in range(num_execucoes):
    pid_dll.calculate_PID(erro, previous_erro, Kp, Kd, Ki)
end_time = time.perf_counter()
dll_avg_time = (end_time - start_time) / num_execucoes
print(f"Tempo médio por execução (DLL): {dll_avg_time:.8f} segundos")

start_time = time.perf_counter()
for _ in range(num_execucoes):
    calculate_PID(erro, previous_erro, Kp, Kd, Ki)
end_time = time.perf_counter()
py_avg_time = (end_time - start_time) / num_execucoes
print(f"Tempo médio por execução (Python): {py_avg_time:.8f} segundos")
