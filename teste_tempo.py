import time 

start_time = time.time()
timeout = 3.0
line_lost_count = 0

while (time.time() - start_time) < timeout:
    print('to no loop')
print('sai do loop')