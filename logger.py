from threading import Lock
import datetime

log_lock = Lock()
log_buffer = []
LOG_FILE = f"logs/robot_log_{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"

def log(msg):
    timestamped = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    
    with log_lock:
        log_buffer.append(timestamped)

    print(f'{timestamped}: {msg}') 
    # Append em arquivo
    with open(LOG_FILE, 'a') as f:
        f.write(timestamped + '\n')