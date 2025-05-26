import io
from flask import Flask, Response, render_template, request, jsonify, stream_with_context
from threading import Lock
import datetime

#from picamera2 import Picamera2
#from picamera2.picamera2 import Picamera2
#from picamera2 import Preview
import time
import cv2
import psutil
import os
import json
import subprocess
#from main import main

app = Flask(__name__)

Kp = 100; Ki = 200; Kd = 150
threshold_value = 50

log_buffer = []
log_lock = Lock()


def generate_frames():
    #camera = Picamera2() 
    #camera.configure(camera.create_still_configuration())
    #camera.start()

    # Espera a câmera iniciar
    time.sleep(0.1)  

    while True:
#        frame = camera.capture_array()  # Captura o frame
        
        frame = cv2.imread('C:/Users/Samuel/Downloads/test.jpg')

        # converte o frame 
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Codifica o frame como JPEG sem nenhum processamento
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        # Envia o frame como multipart HTTP
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

LOG_FILE = f"logs/robot_log_{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"

def log(msg):
    timestamped = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(timestamped)
    
    with log_lock:
        log_buffer.append(timestamped)
     
    # Append em arquivo
    with open(LOG_FILE, 'a') as f:
        f.write(timestamped + '\n')

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


@app.route('/start', methods=['POST'])
def start_robot():
    log("Robo andando")
    #main.main()
    return jsonify({"status": "started"})

@app.route('/stop', methods=['POST'])
def stop_robot():
    log("Robo parado")
    #motors.stop_motor()
    return jsonify({"status": "stopped"})

@app.route('/status')
def get_status():
    cpu = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory().percent

    # tensao
    voltage_state = 'tmnc'
    #voltage_state = subprocess.run(['vcgencmd', 'get_throttled'], capture_output=True, text=True)
    #voltage_state = voltage_state.stdout.strip()
    
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
                           threshold_value=threshold_value) 

@app.route('/update_params', methods=['POST'])
def update_params():
    global Kp, Ki, Kd, threshold_value
    data = request.get_json()
    
    Kp = int(data.get('kp', Kp))
    Ki = int(data.get('ki', Ki))
    Kd = int(data.get('kd', Kd))
    threshold_value = int(data.get('threshold', threshold_value))
    
    return jsonify({
        "status": "ok",
        "Kp": Kp,
        "Ki": Ki,
        "Kd": Kd,
        "threshold": threshold_value
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)