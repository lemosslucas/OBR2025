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

dynamic_color_ranges = {
    GREEN: {'lower': [40, 80, 50], 'upper': [60, 255, 200]},
    RED:   {'lower': [118, 230, 90], 'upper': [123, 255, 220]},
    GRAY:  {'lower': [0, 0, 50], 'upper': [180, 50, 220]}
}

active_calibration_color = 'THRESHOLD'

# --- Lógica da Câmera (sem alterações) ---
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
    if img is None: return None, None, None
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    color_ranges = {
        GREEN: [(np.array(dynamic_color_ranges[GREEN]['lower']), np.array(dynamic_color_ranges[GREEN]['upper']))],
        RED:   [(np.array(dynamic_color_ranges[RED]['lower']), np.array(dynamic_color_ranges[RED]['upper']))],
        GRAY:  [(np.array(dynamic_color_ranges[GRAY]['lower']), np.array(dynamic_color_ranges[GRAY]['upper']))]
    }
    kernel = np.ones((5, 5), np.uint8)
    detected_areas, colors_contours = {}, {}
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
            if len(squares) >= 2: return dominant_color, DEAD_END, squares
            elif len(squares) == 1:
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
    draw_colors = { GREEN: (0, 255, 0), RED: (0, 0, 255), GRAY: (128, 128, 128) }
    color_names = { GREEN: "VERDE", RED: "VERMELHO", GRAY: "CINZA" }
    while True:
        if img is None: time.sleep(0.1); continue
        display_img = img.copy()
        detected_color, side_info, contours = identify_colour(display_img)
        if detected_color and detected_color == active_calibration_color and contours:
            largest_contour = max(contours, key=cv2.contourArea)
            area = int(cv2.contourArea(largest_contour))
            if area > 50:
                rect_color = draw_colors.get(detected_color, (255, 255, 255))
                x, y, w, h = cv2.boundingRect(largest_contour)
                cv2.rectangle(display_img, (x, y), (x + w, y + h), rect_color, 2)
                color_name_str = color_names.get(detected_color, "UNKNOWN")
                text = f"{color_name_str}: {area}" + (f" ({side_info})" if side_info else "")
                cv2.putText(display_img, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, rect_color, 2)
        ret, buffer = cv2.imencode('.jpg', display_img)
        if not ret: continue
        frame = buffer.tobytes()
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# --- GERADORES DE FEED (sem alterações) ---
def generate_color_mask_feed(color_name_str):
    key_map = {'green': GREEN, 'red': RED, 'gray': GRAY}
    color_key = key_map.get(color_name_str)
    if color_key is None: return
    while True:
        if img is None: time.sleep(0.1); continue
        hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower = np.array(dynamic_color_ranges[color_key]['lower'])
        upper = np.array(dynamic_color_ranges[color_key]['upper'])
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
    """Renderiza a página principal, lendo os dados diretamente do dicionário."""
    # Este mapa "traduz" as chaves do backend (que podem ser números) para nomes no frontend
    key_to_name_map = {
        GREEN: {'id': 'green', 'name': 'GREEN'},
        RED:   {'id': 'red',   'name': 'RED'},
        GRAY:  {'id': 'gray',  'name': 'GRAY'}
    }
    
    hsv_controls_data = []

    # A MUDANÇA PRINCIPAL ESTÁ AQUI:
    # Iteramos diretamente sobre os itens do dicionário, que é a fonte da verdade.
    for key, ranges_data in dynamic_color_ranges.items():
        # Verificamos se a chave do dicionário (ex: 1) existe no nosso mapa de tradução
        if key in key_to_name_map:
            # Se existir, adicionamos os dados formatados à lista
            hsv_controls_data.append({
                'id': key_to_name_map[key]['id'],       # ex: "green"
                'name': key_to_name_map[key]['name'],   # ex: "GREEN"
                'ranges': ranges_data
            })
    # Passamos a lista (agora corretamente preenchida) para o template
    return render_template('calibrator.html',
                           current_threshold=threshold_value,
                           hsv_controls=hsv_controls_data)



@app.route('/video_feed')
def video_feed(): return Response(generate_raw_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route('/processed_feed/threshold')
def processed_feed_threshold(): return Response(generate_threshold_feed(), mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route('/processed_feed/<color_name>')
def processed_feed_color(color_name): return Response(generate_color_mask_feed(color_name), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/set_active_color', methods=['POST'])
def set_active_color_view():
    global active_calibration_color
    data = request.get_json()
    color_map = {'green': GREEN, 'red': RED, 'gray': GRAY, 'threshold': 'THRESHOLD'}
    active_calibration_color = color_map.get(data.get('color'), 'THRESHOLD')
    return jsonify({"status": "success", "mode": active_calibration_color})

@app.route('/get_hsv_from_roi', methods=['POST'])
def get_hsv_from_roi():
    if img is None: return jsonify({"error": "No image from camera"}), 500
    data = request.get_json(); x,y,w,h = int(data['x']),int(data['y']),int(data['w']),int(data['h'])
    if w==0 or h==0: return jsonify({"error": "Invalid area"}), 400
    roi = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)[y:y+h, x:x+w]
    return jsonify({'h':int(np.mean(roi[:,:,0])), 's':int(np.mean(roi[:,:,1])), 'v':int(np.mean(roi[:,:,2]))})

@app.route('/update_threshold', methods=['POST'])
def update_threshold_value():
    new_threshold = int(request.get_json()['threshold'])
    #print(new_threshold)
    update_constants(threshold=new_threshold)
    return jsonify({"status": "success", "new_threshold": new_threshold})

# ROTA DE UPDATE HSV MODIFICADA
@app.route('/update_hsv', methods=['POST'])
def update_hsv_ranges():
    """Recebe o NOME da cor do frontend e mapeia para a CHAVE (número) do backend."""
    name_to_key_map = {'GREEN': GREEN, 'RED': RED, 'GRAY': GRAY}
    data = request.get_json()
    color_name = data.get('color') # ex: "GREEN"
    color_key = name_to_key_map.get(color_name) # ex: 1

    if color_key is not None and color_key in dynamic_color_ranges:
        dynamic_color_ranges[color_key]['lower'] = [int(data['h_min']), int(data['s_min']), int(data['v_min'])]
        dynamic_color_ranges[color_key]['upper'] = [int(data['h_max']), int(data['s_max']), int(data['v_max'])]
 #       print(dynamic_color_ranges[color_key]['lower'])
 #       print(dynamic_color_ranges[color_key]['upper'])

        return jsonify({"status": "success"})
    

    return jsonify({"status": "error", "message": "Invalid color name"}), 400

# --- Bloco Principal de Execução ---
if __name__ == '__main__':
    try:
        log("Calibrador: Inicializando a camera...")
        cam = Picamera2(); cam.configure(cam.create_preview_configuration(main={"size": (320, 240)})); cam.start()
        time.sleep(1.0); log("Calibrador: Câmera pronta.")
        camera_thread = Thread(target=update_camera_feed, daemon=True); camera_thread.start()
        log("Servidor de calibração iniciado. Acesse http://<ip_do_raspberry>:5000")
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e: log(f"ERRO FATAL AO INICIAR O CALIBRADOR: {e}")
    finally:
        if cam: cam.stop()
