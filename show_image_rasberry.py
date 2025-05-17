import io
from flask import Flask, Response, render_template, request, jsonify
#from picamera2 import Picamera2
#from picamera2.picamera2 import Picamera2
#from picamera2 import Preview
import time
import cv2
import psutil
import os
import json
import subprocess


app = Flask(__name__)

Kp = 100; Ki = 200; Kd = 150
threshold_value = 50

def generate_frames():
    #camera = Picamera2() 
    #camera.configure(camera.create_still_configuration())
    #camera.start()

    # Espera a câmera iniciar
    time.sleep(0.1)  

    while True:
        #frame = camera.capture_array()  # Captura o frame
        
        frame = cv2.imread('C:/Users/Samuel/Downloads/test.jpg')

        # converte o frame 
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Codifica o frame como JPEG sem nenhum processamento
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        # Envia o frame como multipart HTTP
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/status')
def get_status():
    cpu = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory().percent

    # tensao
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
    app.run(host='0.0.0.0', port=5000)
