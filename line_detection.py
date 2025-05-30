# Import libraries
import cv2
import numpy as np
import os 

from constants import GRAY, GREEN, RED, LEFT, RIGHT

def calculate_error(target_line):
    """
    Calculates the error between the target line position and the car flow line position.

    Args:
        target_line (list): List containing the coordinates of the detected target line.
        start_point_flow (int): X-axis starting position of the car flow line.

    Returns:
        int: error in degrees.
    """
    #print(target_line)
    if isinstance(target_line, tuple):
        target_line = target_line[0]  

    # Convert to numpy array e remove the extra dimensions
    contour = np.squeeze(np.array(target_line))  

    # avoid error if has few points
    if contour.shape[0] < 2:
        return None  
    
    # get the extremes points
    x1, y1 = tuple(contour[np.argmin(contour[:, 1])])  # few value of Y (top)
    x2, y2 = tuple(contour[np.argmax(contour[:, 1])])  # bigger value of Y (base)
    
    # calculate angle em rad
    theta_rad = np.arctan2(y2 - y1, x2 - x1)

    # convert to degree
    theta_deg = np.degrees(theta_rad)
    
    # assure the degres in [0, 180]
    theta_deg = theta_deg + 180 if theta_deg < 0 else theta_deg

    # return the error in degree (for less use of memory)
    return int(theta_deg - 90)

def identify_colour(img):
    """
    Identifies the dominant color in an image based on predefined HSV ranges.

    This function converts the input image to the HSV color space and detects specific colors 
    (red, green, and gray) using predefined hue, saturation, and value ranges. It then applies 
    morphological operations to reduce noise, finds contours, and calculates the area covered 
    by each detected color. The function returns the color with the largest detected area.

    Parameters:
    img (numpy.ndarray): The input image in BGR format.

    Returns:
    int or None: The detected color with the largest area (RED, GREEN, or GRAY), or None 
                 if no significant color region is foun
    """
    # convert image in HSV scale
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # definy colour ranges
    color_ranges = {
        RED: [(np.array([0, 100, 100]), np.array([10, 255, 255])),
                (np.array([160, 100, 100]), np.array([180, 255, 255]))],  # Red (Hue 0-10)
        GREEN: [(np.array([40, 40, 40]), np.array([90, 255, 255]))],  # Green (Hue 40-90)
        GRAY: [(np.array([0, 0, 50]), np.array([130, 60, 220]))]  # Gray
    }
    
    kernel = np.ones((3, 3), np.uint8)
    # create a dict to storage the colours
    detected_areas = {}

    # find colours
    for color, ranges in color_ranges.items():
        # create mask colours
        mask = np.bitwise_or.reduce([cv2.inRange(hsv_img, lower, upper) for lower, upper in ranges])
        # reduce the noisy
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected_areas[color] = sum(cv2.contourArea(c) for c in contours)

        if contours:
            # drawn the contours in black colour
            cv2.drawContours(img, contours, -1, (0,0,0), 2)

    if max(detected_areas.values()) > 0:
        dominant_color = max(detected_areas, key=detected_areas.get) 
        
        if dominant_color == GREEN:
            # split the image in two sides
            mid = img.shape[1] // 2
            
            # create a green mask 
            green_mask = np.bitwise_or.reduce([cv2.inRange(hsv_img, lower, upper) for lower, upper in color_ranges[GREEN]])
            
            # calculate moments of image
            moments = cv2.moments(green_mask)
            
            # find the center of object
            cX = int(moments["m10"] / moments["m00"])
            
            # find the side
            side = LEFT if cX < mid else RIGHT
            
            # return the green colour and your side
            return dominant_color, side
        
        # return the colour with most area on the image
        return dominant_color, None
    # return none if not has colour in the image
    return None

def verify_curve(contours, img_width):
    """
    Checks if there is a curve in the image and identifies its direction.

    The function analyzes the detected contours and verifies the distribution 
    of points relative to the center of the image. If most points are on the 
    left side, the curve is classified as "Left"; if they are on the right side, 
    it is classified as "Right". Otherwise, it returns "No curve".

    Additionally, if the number of points in the contour is too large (>= 8), 
    it is assumed that the shape is not a sharp curve.

    Args:
        contours (list): List of detected contours in the image.
        img_width (int): Width of the image, used to determine the center.

    Returns:
        int: LEFT if the curve is on the left, RIGHT if it is on the right, 
             or False if no significant curve is detected.
    """

    # Split the image in 2
    mid = img_width // 2

    for contour in contours:
        X = contour[:, 0, 0]

        points_left, points_right = np.sum(X < mid), np.sum(X >= mid)

        # if contour > 8 probabily it's not a curve 90
        if len(contour) < 8:  
            if points_left > points_right:
                return LEFT
            if points_left < points_right:
                return RIGHT

    # return no curve
    return False

def process_image(img):
    """
    Preprocesses the image to isolate dark regions (potential lines) using grayscale 
    conversion, thresholding, and morphological operations to reduce noise.

    Args:
        img (numpy.ndarray): Input image in BGR format.

    Returns:
        numpy.ndarray: Binary image with detected dark regions (lines) highlighted.
    """

    # Convert the image to grayscale
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    threshold_value = 50

    # Aplly a threshold to detect only darken colours
    _, binary = cv2.threshold(img_gray, threshold_value, 255, cv2.THRESH_BINARY_INV)

    # reduce the noise
    kernel = np.ones((3, 3), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    return binary

def analyse_contours(img, contours):
    """
    Analyzes the provided contours to determine if a curve is present and calculate 
    the angular error between the line and the vertical axis.

    Args:
        img (numpy.ndarray): Original image in BGR format (used for drawing).
        contours (list): List of contours detected from the binary image.

    Returns:
        tuple:
            - erro (int or None): Angular error in degrees relative to vertical.
            - curve_side (int or None): LEFT or RIGHT if a curve is detected, otherwise False.
    """
    # verify if has a line on the image
    if len(contours) > 0:
        # drawn the line target
        cv2.drawContours(img, contours, -1, (0, 0, 255), 2)
        
        # send img_widht as img.shape[1]
        curve_side = verify_curve(contours, img.shape[1])
        
        # calculate the error
        error = calculate_error(contours)

        # to avoid false-positive
        if (error > 0 and error <= 10) or (error >= -10 and error < 0): curve_side = False
       
        return error, curve_side
    return None, None 

def detect_line(img):
    """
    Main function to detect a line in the input image, check for curves, and identify 
    the presence of significant colors (red, green, or gray).

    This function orchestrates the image processing pipeline including preprocessing, 
    contour detection, curve verification, angular error calculation, and color detection.

    Args:
        img (numpy.ndarray): Input image in BGR format.

    Returns:
        tuple:
            - error (int or None): Angular error in degrees (0 if a symbol is detected).
            - curve_side (int or bool or None): LEFT, RIGHT, or False if no curve found.
            - color_detected (tuple or None): Tuple with detected color code and side (if green), 
              or None if no color is detected.
    """

    # verify if img exists
    if img is None:
        return None, None, None

    # process the image
    processed_img = process_image(img)
    
    # Detect points that form a line
    contours, _ = cv2.findContours(processed_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # verify if has a symbol on the img
    color_detected = identify_colour(img)
    
    # analyse the contours on the image
    error, curve_side = analyse_contours(img, contours)

    # to avoid false-positive
    if color_detected or curve_side is not False and len(contours) > 0: return 0, curve_side, color_detected
    
    # return the erro and curve_side and color_detected
    return error, curve_side, color_detected

def download_image(img, erro, path, image_name, color_detected, curve_side=False):
    #plt.title(f'Erro = {erro}°, Curve = {curve_side}, Color: {color_detected}')
    #plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    #plt.savefig(f"{path}/analised/{image_name}-analised.jpg")
    pass 

if __name__ == '__main__':
    path = 'datas/lines/'
    images = [f for f in os.listdir(path) if f.endswith('.jpg')]
    
    # for a specified file
    #images = ["ladrinho_embranco.jpg"]
    
    for image_name in images:
        print(path + image_name)
        img = cv2.imread(path + image_name)
        #img = cv2.imread(image_name)
        
        erro, curve_side, color_detected = detect_line(img)
        print(f"Erro: {erro}|isCurve: {curve_side}|has_colour: {color_detected}")

        image_name, type_file = image_name.split('.jpg')
        #download_image(img, erro, path, image_name, color_detected, curve_side)
        #print('The error in degrees:', erro)
        #print(f"Memory used: {psutil.Process(os.getpid()).memory_info().rss / (1024 ** 2)} MB")
        print('-'*35)