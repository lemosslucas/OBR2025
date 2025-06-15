import io
import time
import cv2
from flask import Flask, Response, render_template, request, jsonify
from threading import Thread
from picamera2 import Picamera2

# Importações dos módulos do seu projeto
from constants import update_constants, threshold_value
from line_detection import process_image
from logger import log

# --- Configuração do Aplicativo Flask e Variáveis Globais ---
app = Flask(__name__)
cam = None
img = None

# --- Lógica da Câmera ---

def update_camera_feed():
    """
    Uma função que roda em uma thread separada
    para manter a variável global 'img' sempre atualizada.
    """
    global img
    while True:
        try:
            if cam:
                img_cam = cam.capture_array()
                from robot_control import get_roi
                img = get_roi(img_cam)
        except Exception as e:
            log(f"Falha ao capturar frame para o feed: {e}")
            time.sleep(0.5)

# --- Geradores de Frame para Streaming ---

def generate_raw_frames():
    """Gera o feed de vídeo bruto (colorido) da câmera."""
    while True:
        if img is None:
            time.sleep(0.1)
            continue
        
        # Codifica o frame como JPEG
        ret, buffer = cv2.imencode('.jpg', img)
        if not ret:
            continue
        frame = buffer.tobytes()

        # Envia o frame como multipart HTTP
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def generate_processed_frames():
    """Gera o feed de vídeo processado (após o threshold)."""
    while True:
        if img is None:
            time.sleep(0.1)
            continue

        # Usa a função de processamento do line_detection para binarizar a imagem
        processed_img = process_image(img)
        
        ret, buffer = cv2.imencode('.jpg', processed_img)
        if not ret:
            continue
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# --- Rotas do Flask (Endpoints da API) ---

@app.route('/')
def index():
    """Renderiza a página principal do calibrador."""
    return render_template('calibrator.html', current_threshold=threshold_value)

@app.route('/video_feed')
def video_feed():
    """Rota para o feed de vídeo bruto."""
    return Response(generate_raw_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/processed_feed')
def processed_feed():
    """Rota para o feed de vídeo processado."""
    return Response(generate_processed_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_hsv', methods=['POST'])
def get_hsv_value():
    """Recebe coordenadas (x, y) e retorna o valor HSV daquele pixel."""
    if img is None:
        return jsonify({"error": "No image from camera"}), 500

    data = request.get_json()
    x, y = int(data['x']), int(data['y'])

    # Converte a imagem BGR (padrão do OpenCV) para HSV
    hsv_image = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Pega o valor do pixel. h, s, v são inteiros de 8 bits (0-255)
    pixel_hsv = hsv_image[y, x]
    h, s, v = int(pixel_hsv[0]), int(pixel_hsv[1]), int(pixel_hsv[2])

    return jsonify({'h': h, 's': s, 'v': v})

@app.route('/update_threshold', methods=['POST'])
def update_threshold_value():
    """Atualiza o valor do threshold em tempo real."""
    data = request.get_json()
    new_threshold = int(data['threshold'])
    
    # Usa a função do seu arquivo de constantes para atualizar o valor
    update_constants(threshold=new_threshold)
    log(f"Threshold atualizado para: {new_threshold}")
    
    return jsonify({"status": "success", "new_threshold": new_threshold})

# --- Bloco Principal de Execução ---

if __name__ == '__main__':
    try:
        log("Calibrador: Inicializando a camera...")
        cam = Picamera2()
        config = cam.create_preview_configuration(main={"size": (320, 240)})
        cam.configure(config)
        cam.start()
        time.sleep(1.0)  # Tempo para estabilização da câmera
        log("Calibrador: Câmera pronta.")

        log("Calibrador: Iniciando a thread de captura de imagem...")
        camera_thread = Thread(target=update_camera_feed)
        camera_thread.daemon = True
        camera_thread.start()
        log("Calibrador: Thread da câmera rodando.")
        
        log("Servidor de calibração iniciado. Acesse http://<ip_do_raspberry>:5000")
        app.run(host='0.0.0.0', port=5000, debug=False)

    except Exception as e:
        log(f"ERRO FATAL AO INICIAR O CALIBRADOR: {e}")
    finally:
        if cam:
            cam.stop()