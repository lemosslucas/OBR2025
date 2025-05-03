import io
from flask import Flask, Response, render_template
#from picamera2 import Picamera2
#from picamera2.picamera2 import Picamera2
#from picamera2 import Preview
import time
import cv2
import psutil
import os
import json


app = Flask(__name__)

def generate_frames():
    #camera = Picamera2()  # Usando o picamera2
    #camera.configure(camera.create_still_configuration())
    #camera.start()

    time.sleep(0.1)  # Espera a câmera iniciar

    while True:
        #frame = camera.capture_array()  # Captura o frame
        
        frame = cv2.imread('C:/Users/Samuel/Downloads/test.jpg')

        frame = cv2.resize(frame, )
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

    # Lê a temperatura da CPU
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = int(f.read()) / 1000.0
    except:
        temp = None

    return json.dumps({
        "cpu": cpu,
        "memory": memory,
        "temperature": temp
    })
@app.route('/video')
def show_video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
