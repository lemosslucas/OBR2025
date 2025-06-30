import io
import time
import cv2
from flask import Flask, Response, render_template, request, jsonify
from threading import Thread
from picamera2 import Picamera2
import numpy as np

# Importações dos módulos do seu projeto
from constants import update_constants, threshold_value
from constants import GREEN, RED, GRAY, LEFT, RIGHT, DEAD_END, MIN_AREA_GREEN

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

def identify_colour(img):
    """
    Identifica a cor dominante e retorna a cor, informações de lado (para verde)
    e os contornos da cor detectada.
    """
    if img is None: 
        # Retorna uma tupla de 3 elementos para consistência
        return None, None, None
    
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # IMPORTANTE: Coloque aqui os ranges de HSV que você calibrou!
    color_ranges = {
        GREEN: [(np.array([44-5, 94-5, 140-5]), np.array([47 + 5, 122 +5, 188 + 5]))],
        RED: [
            (np.array([122-5, 203-5, 151-5]), np.array([126+5, 223+5, 227+5])),
            #(np.array([160, 100, 100]), np.array([180, 255, 255]))
        ],
        #GRAY: [(np.array([0, 0, 50]), np.array([130, 60, 220]))]
    }
    
    kernel = np.ones((3, 3), np.uint8)
    detected_areas = {}
    colors_contours = {}

    for color, ranges in color_ranges.items():
        mask = np.bitwise_or.reduce([cv2.inRange(hsv_img, lower, upper) for lower, upper in ranges])
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected_areas[color] = sum(cv2.contourArea(c) for c in contours)
        colors_contours[color] = contours

    if max(detected_areas.values()) > 0:
        dominant_color = max(detected_areas, key=detected_areas.get)
        dominant_contours = colors_contours[dominant_color]

        if dominant_color == GREEN:
            squares = [c for c in dominant_contours if cv2.contourArea(c) > MIN_AREA_GREEN]
            num_squares = len(squares)

            if num_squares >= 2:
                return dominant_color, DEAD_END, squares
            
            elif num_squares == 1:
                mid = img.shape[1] // 2
                moments = cv2.moments(squares[0])
                if moments['m00'] != 0:
                    cX = int(moments["m10"] / moments["m00"])
                    side = LEFT if cX < mid else RIGHT  
                    return dominant_color, side, squares
                return dominant_color, None, squares 
        
        # Para outras cores, retorna a cor e seus contornos
        return dominant_color, None, dominant_contours
        
    return None, None, None

def generate_raw_frames():
    """Gera o feed de vídeo bruto (colorido) da câmera."""
    draw_colors = {
        GREEN: (0, 255, 0),   # Verde
        RED: (0, 0, 255),     # Vermelho
        GRAY: (128, 128, 128) # Cinza
    }

    while True:
        if img is None:
            time.sleep(0.1)
            continue
        
        # Crie uma cópia da imagem para desenhar sobre ela, preservando a original
        display_img = img.copy()

        # Chame a função para identificar cores
        detected_color, side_info, contours = identify_colour(display_img)

        # Se algum contorno de cor foi detectado...
        if contours:
            # Pegue a cor para desenhar o retângulo
            rect_color = draw_colors.get(detected_color, (255, 255, 255)) # Branco como padrão

            # Desenhe um retângulo para cada contorno encontrado
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                cv2.rectangle(display_img, (x, y), (x + w, y + h), rect_color, 2)

        # Codifica o frame como JPEG
        ret, buffer = cv2.imencode('.jpg', display_img)
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