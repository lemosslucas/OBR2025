import cv2
import numpy as np

def nothing(x):
    pass

img = cv2.imread('C:/Users/Samuel/Downloads/Programacao/projetos-visao-computacional/OBR2025/datas/reliefs/box.jpg')
img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

cv2.namedWindow('Relief Detection')
cv2.createTrackbar('Threshold', 'Relief Detection', 100, 255, nothing)
cv2.createTrackbar('Min Area', 'Relief Detection', 500, 3000, nothing)

while True:
    # catch the actual values of trackbar
    thresh_val = cv2.getTrackbarPos('Threshold', 'Relief Detection')
    min_area = cv2.getTrackbarPos('Min Area', 'Relief Detection')

    # Sobel and magnitude
    sobelx = cv2.Sobel(img_gray, cv2.CV_64F, 1, 0, ksize=5)
    sobely = cv2.Sobel(img_gray, cv2.CV_64F, 0, 1, ksize=5)
    sobel_mag = cv2.magnitude(sobelx, sobely)
    sobel_norm = cv2.normalize(sobel_mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    _, mask = cv2.threshold(sobel_norm, thresh_val, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    result = img.copy()
    for c in contours:
        if cv2.contourArea(c) > min_area:
            cv2.drawContours(result, [c], -1, (0, 0, 255), 2)

    # show the image in this size
    result_resized = cv2.resize(result, (500, 800)) 
    cv2.imshow('Relief Detection', result_resized)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
