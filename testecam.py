import cv2
import time
from picamera2 import Picamera2

# 1. Inicializa a câmera com Picamera2
picam2 = Picamera2()
print("Inicializando a câmera...")

# 2. Configura a câmera para uma resolução comum
config = picam2.create_preview_configuration(main={"size": (640, 480)})
picam2.configure(config)

# 3. Inicia a câmera e dá um tempo para ela aquecer
picam2.start()
time.sleep(2)
print("Câmera iniciada com sucesso.")

# 4. Captura a imagem como um array NumPy (formato que o OpenCV usa)
# O array vem no formato RGB por padrão
image = picam2.capture_array()
print("Frame capturado!")

# 5. O OpenCV espera imagens no formato BGR, então convertemos de RGB para BGR
image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

# 6. Salva a imagem usando OpenCV
cv2.imwrite("test_frame_picamera2.jpg", image_bgr)
print("Imagem de teste 'test_frame_picamera2.jpg' foi salva com sucesso.")

# 7. Para a câmera
picam2.stop()
print("Recursos da câmera liberados.")