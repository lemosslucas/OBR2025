import ctypes
import os

# Carrega a DLL
pid_dll = ctypes.CDLL(("./c_files/PID.dll"))

# Define os tipos dos argumentos e o tipo de retorno da função
pid_dll.calculate_PID.argtypes = (ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int)
pid_dll.calculate_PID.restype = ctypes.c_int

# Exemplo de uso da função
erro = 10
previous_erro = 5
Kp = 1
Kd = 2
Ki = 3

# Chama a função calculate_PID da DLL
output = pid_dll.calculate_PID(erro, previous_erro, Kp, Kd, Ki)
print(f"PID Output: {output}")