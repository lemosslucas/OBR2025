import io
from flask import Flask, Response, render_template, request, jsonify, stream_with_context
from threading import Thread
import datetime

import time
import cv2
import psutil
import os
import json
import subprocess

from main import run_robot_control, robot_running
from constants import update_constants, Kp, Ki, Kd, threshold_value, Ka

from logger import log, log_buffer, log_lock
import main 

app = Flask(__name__)

def generate_frames():
    while True:
        frame = main.get_current_img()
        
        if frame is None:
            time.sleep(0.1)
            continue

        # Codifica o frame como JPEG sem nenhum processamento
        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 40])
        frame = buffer.tobytes()

        # Envia o frame como multipart HTTP
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/logs')
def stream_logs():
    log("SSE connection opened")
    
    def event_stream():
        previous = ""
        while True:
            time.sleep(0.5)
            with log_lock:
                if log_buffer:
                    latest = log_buffer[-1]
                    if latest != previous:
                        previous = latest
                        yield f"data: {latest}\n\n"

    
    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")

control_thread = None
@app.route('/start', methods=['POST'])
def start_robot():
    global control_thread
#    if main.robot_running:
#        log("Tentativa de iniciar robô que já está em execução.")
#        return jsonify({"status": "already_running"})

    log("Robo andando")
    main.robot_running = True
    control_thread = Thread(target=run_robot_control)
    control_thread.daemon = True
    control_thread.start()

    return jsonify({"status": "started"})

@app.route('/stop', methods=['POST'])
def stop_robot():
    log("Robo parado")
    # APENAS ALTERA A FLAG. A THREAD VAI PARAR SOZINHA.
    main.robot_running = False
    main.motors.stop_motor()
    return jsonify({"status": "stopped"})

@app.route('/status')
def get_status():
    cpu = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory().percent

    # voltage
    voltage_state = subprocess.run(['vcgencmd', 'get_throttled'], capture_output=True, text=True)
    voltage_state = voltage_state.stdout.strip()
    
    # Lê a temperatura da CPU
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = int(f.read()) / 1000.0
    except:
        temp = None
        
    return json.dumps({
        "cpu": cpu,
        "memory": memory,
        "temperature": temp,
        "voltage_state": voltage_state,
    })

@app.route('/video')
def show_video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return render_template('index.html', 
                           Kp=Kp, 
                           Ki=Ki, 
                           Kd=Kd, 
                           Ka=Ka,
                           threshold_value=threshold_value) 

@app.route('/update_params', methods=['POST'])
def update_params():
    data = request.get_json()

    update_constants(
        kp=float(data.get('kp', Kp)),
        ki=float(data.get('ki', Ki)),
        kd=float(data.get('kd', Kd)),
        ka=float(data.get('ka', Ka)),
        threshold=int(data.get('threshold', threshold_value))
    )

    return jsonify({
        "status": "ok",
        "Kp": Kp,
        "Ki": Ki,
        "Kd": Kd,
        "Ka": Ka,
        "threshold": threshold_value
    })

if __name__ == '__main__':
    log("Iniciando a thread do feed da camera...")
    camera_thread = Thread(target=main.update_camera_feed)
    camera_thread.daemon = True
    camera_thread.start()

    # Inicia o servidor web
    app.run(host='0.0.0.0', port=5000, debug=False)
