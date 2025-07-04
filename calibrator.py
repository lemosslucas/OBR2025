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

# --- VARIÁVEIS GLOBAIS PARA CALIBRAÇÃO ---
dynamic_color_ranges = {
    GREEN: {'lower': [35, 80, 80], 'upper': [85, 255, 255]},
    RED:   {'lower': [160, 100, 100], 'upper': [180, 255, 255]},
    GRAY:  {'lower': [0, 0, 50], 'upper': [180, 50, 220]}
}

# NOVO: Variável de estado para saber qual calibração está ativa no frontend
active_calibration_color = 'THRESHOLD'

# --- Lógica da Câmera ---

def update_camera_feed():
    global img
    while True:
        try:
            if cam:
                img_cam = cam.capture_array()
                try:
                    from robot_control import get_roi
                    img = get_roi(img_cam)
                except (ImportError, AttributeError):
                    img = img_cam
        except Exception as e:
            log(f"Falha ao capturar frame para o feed: {e}")
            time.sleep(0.5)

def identify_colour(img):
    if img is None: 
        return None, None, None
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    color_ranges = {
        GREEN: [(np.array(dynamic_color_ranges[GREEN]['lower']), np.array(dynamic_color_ranges[GREEN]['upper']))],
        RED:   [(np.array(dynamic_color_ranges[RED]['lower']), np.array(dynamic_color_ranges[RED]['upper']))],
        GRAY:  [(np.array(dynamic_color_ranges[GRAY]['lower']), np.array(dynamic_color_ranges[GRAY]['upper']))]
    }
    kernel = np.ones((5, 5), np.uint8)
    detected_areas = {}
    colors_contours = {}
    for color, ranges in color_ranges.items():
        mask = np.bitwise_or.reduce([cv2.inRange(hsv_img, lower, upper) for lower, upper in ranges])
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            detected_areas[color] = sum(cv2.contourArea(c) for c in contours)
            colors_contours[color] = contours
    min_area_threshold = 50
    valid_detections = {c: a for c, a in detected_areas.items() if a > min_area_threshold}
    if valid_detections:
        dominant_color = max(valid_detections, key=valid_detections.get)
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
        return dominant_color, None, dominant_contours
    return None, None, None

def generate_raw_frames():
    """
    Gera o feed de vídeo bruto.
    AGORA SÓ DESENHA A CAIXA E O TEXTO SE A COR DETECTADA FOR A MESMA
    QUE ESTÁ SELECIONADA PARA CALIBRAÇÃO NO FRONTEND.
    TAMBÉM MOSTRA A ÁREA DO MAIOR CONTORNO.
    """
    draw_colors = { GREEN: (0, 255, 0), RED: (0, 0, 255), GRAY: (128, 128, 128) }
    color_names = { GREEN: "VERDE", RED: "VERMELHO", GRAY: "CINZA" }
    
    while True:
        if img is None:
            time.sleep(0.1)
            continue
        
        display_img = img.copy()
        detected_color, side_info, contours = identify_colour(display_img)

        # A lógica de desenho só é acionada se uma cor for detectada E
        # se a cor detectada for a mesma que está ativa na interface.
        if detected_color and detected_color == active_calibration_color and contours:
            
            # APRIMORADO: Encontra o maior contorno
            largest_contour = max(contours, key=cv2.contourArea)
            area = int(cv2.contourArea(largest_contour))

            if area > 50: # Desenha apenas se a área for significativa
                rect_color = draw_colors.get(detected_color, (255, 255, 255))
                
                # Usa o bounding box do maior contorno
                x, y, w, h = cv2.boundingRect(largest_contour)
                cv2.rectangle(display_img, (x, y), (x + w, y + h), rect_color, 2)
                
                color_name_str = color_names.get(detected_color, "UNKNOWN")
                # APRIMORADO: Mostra a área do maior contorno
                text = f"{color_name_str}: {area}"
                if side_info:
                    text += f" ({side_info})"
                
                cv2.putText(display_img, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, rect_color, 2)

        ret, buffer = cv2.imencode('.jpg', display_img)
        if not ret: continue
        frame = buffer.tobytes()
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# --- GERADORES DE FEED (sem alterações) ---

def generate_color_mask_feed(color_name):
    while True:
        if img is None: time.sleep(0.1); continue
        hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower = np.array(dynamic_color_ranges[color_name]['lower'])
        upper = np.array(dynamic_color_ranges[color_name]['upper'])
        mask = cv2.inRange(hsv_img, lower, upper)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        ret, buffer = cv2.imencode('.jpg', mask)
        if not ret: continue
        frame = buffer.tobytes()
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def generate_threshold_feed():
    while True:
        if img is None: time.sleep(0.1); continue
        processed_img = process_image(img)
        ret, buffer = cv2.imencode('.jpg', processed_img)
        if not ret: continue
        frame = buffer.tobytes()
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# --- Rotas do Flask ---

@app.route('/')
def index():
    return render_template('calibrator.html', current_threshold=threshold_value, hsv_ranges=dynamic_color_ranges)

@app.route('/video_feed')
def video_feed():
    return Response(generate_raw_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/processed_feed/threshold')
def processed_feed_threshold():
    return Response(generate_threshold_feed(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/processed_feed/green')
def processed_feed_green():
    return Response(generate_color_mask_feed(GREEN), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/processed_feed/red')
def processed_feed_red():
    return Response(generate_color_mask_feed(RED), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/processed_feed/gray')
def processed_feed_gray():
    return Response(generate_color_mask_feed(GRAY), mimetype='multipart/x-mixed-replace; boundary=frame')

# --- NOVA ROTA PARA ATUALIZAR O ESTADO DE VISUALIZAÇÃO ---
@app.route('/set_active_color', methods=['POST'])
def set_active_color_view():
    """Recebe do frontend qual cor está sendo calibrada e atualiza a variável de estado."""
    global active_calibration_color
    data = request.get_json()
    color_map = {'green': GREEN, 'red': RED, 'gray': GRAY, 'threshold': 'THRESHOLD'}
    color_key = data.get('color')
    
    if color_key in color_map:
        active_calibration_color = color_map[color_key]
        # log(f"Modo de calibração alterado para: {active_calibration_color}")
        return jsonify({"status": "success", "mode": active_calibration_color})
    
    return jsonify({"status": "error", "message": "Invalid color key"}), 400


# --- ROTAS DE CONTROLE (sem alterações) ---

@app.route('/get_hsv_from_roi', methods=['POST'])
def get_hsv_from_roi():
    if img is None: return jsonify({"error": "No image from camera"}), 500
    data = request.get_json()
    x, y, w, h = int(data['x']), int(data['y']), int(data['w']), int(data['h'])
    if w == 0 or h == 0: return jsonify({"error": "Invalid area"}), 400
    hsv_image = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    roi = hsv_image[y:y+h, x:x+w]
    h_val = int(np.mean(roi[:, :, 0]))
    s_val = int(np.mean(roi[:, :, 1]))
    v_val = int(np.mean(roi[:, :, 2]))
    return jsonify({'h': h_val, 's': s_val, 'v': v_val})

@app.route('/update_threshold', methods=['POST'])
def update_threshold_value():
    data = request.get_json()
    new_threshold = int(data['threshold'])
    update_constants(threshold=new_threshold)
    log(f"Threshold atualizado para: {new_threshold}")
    return jsonify({"status": "success", "new_threshold": new_threshold})

@app.route('/update_hsv', methods=['POST'])
def update_hsv_ranges():
    global dynamic_color_ranges
    data = request.get_json()
    color = data['color']
    if color in dynamic_color_ranges:
        dynamic_color_ranges[color]['lower'][0] = int(data['h_min'])
        dynamic_color_ranges[color]['upper'][0] = int(data['h_max'])
        dynamic_color_ranges[color]['lower'][1] = int(data['s_min'])
        dynamic_color_ranges[color]['upper'][1] = int(data['s_max'])
        dynamic_color_ranges[color]['lower'][2] = int(data['v_min'])
        dynamic_color_ranges[color]['upper'][2] = int(data['v_max'])
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Invalid color"}), 400

# --- Bloco Principal de Execução ---
if __name__ == '__main__':
    try:
        log("Calibrador: Inicializando a camera...")
        cam = Picamera2()
        config = cam.create_preview_configuration(main={"size": (320, 240)})
        cam.configure(config)
        cam.start()
        time.sleep(1.0)
        log("Calibrador: Câmera pronta.")

        log("Calibrador: Iniciando a thread de captura de imagem...")
        camera_thread = Thread(target=update_camera_feed)
        camera_thread.daemon = True
        camera_thread.start()
        
        log("Servidor de calibração iniciado. Acesse http://<ip_do_raspberry>:5000")
        app.run(host='0.0.0.0', port=5000, debug=False)

    except Exception as e:
        log(f"ERRO FATAL AO INICIAR O CALIBRADOR: {e}")
    finally:
        if cam:
            cam.stop()