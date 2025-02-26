import cv2 
from line_detection import *
from ball_detection import *


if __name__ == '__main__':
    path = 'datas/lines/'
    images = [f for f in os.listdir(path) if f.endswith('.jpg')]
    
    # for a specified file
    #images = []"datas/lines/ladrilho_verde.jpg"]
    
    for image_name in images:
        print(path + image_name)
        img = cv2.imread(path + image_name)
        erro, is_curve = detect_line(img)

        image_name, type_file = image_name.split('.jpg')
        download_image(img, erro, path, image_name, is_curve)
        #print('The error in degrees:', erro)
        print(f"Memory used: {psutil.Process(os.getpid()).memory_info().rss / (1024 ** 2)} MB")
        print('-'*35)