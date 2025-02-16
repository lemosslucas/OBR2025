# Import libraries
import cv2
import numpy as np
import matplotlib.pyplot as plt
import psutil
import os

def calculate_error(target_line):
    """
    Calculates the error between the target line position and the car flow line position.

    Args:
        target_line (list): List containing the coordinates of the detected target line.
        start_point_flow (int): X-axis starting position of the car flow line.

    Returns:
        int: erro in degrees.
    """
    #print(target_line)
    if isinstance(target_line, tuple):
        target_line = target_line[0]  

    # Convert to numpy array e remove the extra dimensions
    contour = np.squeeze(np.array(target_line))  

    # avoid erro if has few points
    if contour.shape[0] < 2:
        return None  
    
    # get the extrames points
    x1, y1 = tuple(contour[np.argmin(contour[:, 1])])  # few value of Y (top)
    x2, y2 = tuple(contour[np.argmax(contour[:, 1])])  # bigger value of Y (base)
    
    # calculate angle em rad
    theta_rad = np.arctan2(y2 - y1, x2 - x1)

    # convert to degree
    theta_deg = np.degrees(theta_rad)
    
    # assure the degres in [0, 180]
    theta_deg = theta_deg + 180 if theta_deg < 0 else theta_deg
    
    # return the erro in degree (for less use of memory)
    return int(theta_deg - 90)

def draw_line(img):
    """
    Draws two vertical lines on the image representing the car flow boundaries.

    Args:
        img (numpy.ndarray): The input image on which the lines will be drawn.
    """
    # determine the size of the line
    thickness, line_thickness = 3, 32
    
    # extract the img size
    y, x, _ = img.shape
    
    # determine the position of car flow line in relation of x label
    car_flow_x = int((x - line_thickness) / 2)

    # drawn the line 1
    cv2.line(img, (car_flow_x, 0), (car_flow_x, y), (0, 255, 0), thickness)

    # drawn the line 2
    cv2.line(img, (car_flow_x + line_thickness, 0), (car_flow_x + line_thickness, y), (0, 255, 0), thickness)


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
    str or None: The detected color with the largest area ("red", "green", or "gray"), or None 
                 if no significant color region is foun
    """
    # convert image in HSV scale
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # definy colour ranges
    color_ranges = {
        "red": [(np.array([0, 100, 100]), np.array([10, 255, 255])),
                (np.array([160, 100, 100]), np.array([180, 255, 255]))],  # Red (Hue 0-10)
        "green": [(np.array([40, 40, 40]), np.array([90, 255, 255]))],  # Green (Hue 40-90)
        "gray": [(np.array([0, 0, 50]), np.array([130, 60, 220]))]  # Gray
    }
    
    kernel = np.ones((3, 3), np.uint8)
    # create a dict to storage the colours
    detected_areas = {}

    # find colours
    for color, ranges in color_ranges.items():
        # create mask colours
        mask = sum(cv2.inRange(hsv_img, lower, upper) for lower, upper in ranges)
        # reduce the noisy
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected_areas[color] = sum(cv2.contourArea(c) for c in contours)

        if contours:
            # drawn the contours in black colour
            cv2.drawContours(img, contours, -1, (0,0,0), 2)

    if max(detected_areas.values()) > 0:
        dominant_color = max(detected_areas, key=detected_areas.get) 
        
        if dominant_color == 'green':
            # split the image in two sides
            mid = img.shape[1] // 2
            
            # create a green mask 
            green_mask = sum(cv2.inRange(hsv_img, lower, upper) for lower, upper in color_ranges['green'])
            
            # calculate moments of image
            moments = cv2.moments(green_mask)
            
            # find the center of object
            cX = int(moments["m10"] / moments["m00"])
            
            # find the side
            side = 'on left' if cX < mid else 'on right'
            dominant_color = f'{dominant_color} {side}'
                
        # return the colour with most area on the image
        return dominant_color
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
        str: "Left" if the curve is on the left, "Right" if it is on the right, 
             or "No curve" if no significant curve is detected.
    """

    # Split the image in 2
    mid = img_width // 2

    for contour in contours:
        X = contour[:, 0, 0]

        points_left, points_right = np.sum(X < mid), np.sum(X >= mid)

        # if contour > 8 probabily it's not a curve 90
        if len(contour) < 8:  
            if points_left > points_right:
                return 'Left'
            if points_left < points_right:
                return 'Right'

    # return no curve
    return 'No curve'

def detect_line(img):
    """
    Detects lines in the given image using edge detection and Hough Transform, 
    draws the detected lines, and calculates the error between the detected lines 
    and a reference flow line.

    Args:
        img (numpy.ndarray): Input image, which should be in BGR format.

    Returns:
        float: The calculated error between the detected lines and the flow line.
    """

    # verify if img exists
    if img is not None:
        # Convert the image to grayscale
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Aplly a threshold to detect only darken colours
        _, binary = cv2.threshold(img_gray, 50, 255, cv2.THRESH_BINARY_INV)
    
        # reduce the noise
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
        # Detect points that form a line
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
        # verify if has a symbol on the img
        cor_detected = identify_colour(img)
        if cor_detected:
            print(f'Has the colour {cor_detected} on the image')
        
        if contours is not None:
            # drawn the line target
            cv2.drawContours(img, contours, -1, (255, 0, 0), 2)
            
            #draw the car flow line
            draw_line(img)

            # send img_widht as img.shape[1]
            is_curve = verify_curve(contours, img.shape[1])
            
            # calculate the error
            erro = calculate_error(contours)
                
            # to avoid false-positive
            if (erro > 0 and erro <= 10) or (erro >= -10 and erro < 0): is_curve = 'No curve'
            
            print(is_curve)
            # to avoid false-positive
            if cor_detected or is_curve != 'No curve': return 0
                
            # return the erro
            return erro
            
    return None


if __name__ == '__main__':
    img = cv2.imread('datas/ladrinho3_direita.jpg')
    erro = detect_line(img)
    #plt.imshow(img)
    print('The error in degrees:', erro)

    print(f"Memory used: {psutil.Process(os.getpid()).memory_info().rss / (1024 ** 2)} MB")