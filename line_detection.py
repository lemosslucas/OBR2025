# Import libraries
import cv2
import numpy as np
import os 

from constants import GRAY, GREEN, RED, LEFT, RIGHT, curve_threshold, MIN_AREA_GREEN, DEAD_END, COLOR_OFFSET
import constants

def calculate_error(target_line, img_width):
    """
    Calculates the positional error between the center of the image and the
    centroid of the target line.

    Args:
        target_line (numpy.ndarray): The contour of the detected line.
        img_width (int): The width of the camera image.

    Returns:
        int: The horizontal error. Positive if the line is to the right of
             the center, negative if to the left. Returns 0 if the contour
             is invalid.
    """
    # Calculate moments of the contour
    moments = cv2.moments(target_line)

    # Calculate the x-coordinate of the centroid
    if moments["m00"] != 0:
        center_x = int(moments["m10"] / moments["m00"])
    else:
        # Cannot calculate centroid, return no error
        return None
    
    # The center of the image
    image_center_x = img_width // 2

    # Calculate the positional error
    error = center_x - image_center_x

    return error

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
    if img is None: 
        return None
    
    # convert image in HSV scale
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # definy colour ranges
    color_ranges = {
        GREEN: [(np.array([44 - COLOR_OFFSET, 94 - COLOR_OFFSET, 140 - COLOR_OFFSET]), 
                 np.array([47 + COLOR_OFFSET, 122 + COLOR_OFFSET, 188 + COLOR_OFFSET]))],
        RED: [(np.array([122 - COLOR_OFFSET, 203 - COLOR_OFFSET, 151 - COLOR_OFFSET]), 
               np.array([126 + COLOR_OFFSET, 223 + COLOR_OFFSET, 227 + COLOR_OFFSET]))]
#        GRAY: [(np.array([0, 0, 50]), np.array([130, 60, 220]))]  # Gray
    }
    
    kernel = np.ones((3, 3), np.uint8)
    # create a dict to storage the colours
    detected_areas = {}
    colors_contours = {}

    # find colours
    for color, ranges in color_ranges.items():
        # create mask colours
        mask = np.bitwise_or.reduce([cv2.inRange(hsv_img, lower, upper) for lower, upper in ranges])
        # reduce the noisy
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected_areas[color] = sum(cv2.contourArea(c) for c in contours)
        colors_contours[color] = contours

    if max(detected_areas.values()) > 0:
        dominant_color = max(detected_areas, key=detected_areas.get) 
        
        if dominant_color == GREEN:
            green_contours = colors_contours[GREEN]
            
            squares = [c for c in green_contours if cv2.contourArea(c) > MIN_AREA_GREEN]
            num_squares = len(squares)

            if num_squares >= 2:
                print('beco sem saida')
                return dominant_color, DEAD_END
            
            elif num_squares == 1:
                # split the image in two sides
                mid = img.shape[1] // 2

                # calculate moments of image
                moments = cv2.moments(squares[0])
                
                if moments['m00'] != 0:
                    # find the center of object
                    cX = int(moments["m10"] / moments["m00"])
                    
                    # find the side
                    side = LEFT if cX < mid else RIGHT  

                    # return the green colour and your side
                    return dominant_color, side
                
                return None, None
        
        # return the colour with most area on the image
        return dominant_color, None
    # return none if not has colour in the image
    return None, None

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
    
    # Aplly a threshold to detect only darken colours
    _, binary = cv2.threshold(img_gray, constants.threshold_value, 255, cv2.THRESH_BINARY_INV)
#    _, binary = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # reduce the noise
    kernel = np.ones((5, 5), np.uint8)
    # fill the gaps
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    # reduce the noise
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    return binary

def find_curve_side(contour, img_width):
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

    X = contour[:, 0, 0]

    points_left, points_right = np.sum(X < mid), np.sum(X >= mid)
  
    if points_left > points_right:
        return LEFT
    if points_left < points_right:
        return RIGHT

def verify_90_curve(contour):
    """
    """
    if len(contour) < 1:
        return False
    
    # get the heighst and lower point on the contour
    highest_y = min(contour[:, 0, 1])
    lowest_y = max(contour[:, 0, 1])

    # get the meddium point
    average_y = highest_y + (lowest_y - highest_y) / 2

    # split the contour point in two parts
    bottom_points = contour[contour[:, 0, 1] > average_y]
    top_points = contour[contour[:, 0, 1] <= average_y]

    # ensure one part not has that points
    if len(bottom_points) == 0 or len(top_points) == 0:
        return False 
    
    # calculate the horizontal center
    center_bottom_x = int(np.mean(bottom_points[:, 0, 0]))
    center_top_x = int(np.mean(top_points[:, 0, 0]))

    # calculate the deviation
    deviation = abs(center_top_x - center_bottom_x)

#   print(f'thershold curva ({deviation})')
    # if deviation is soo big, it's a 90° curve
    if deviation > curve_threshold:
        return True

    return False

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
        contour_target = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(contour_target)

        # send img_widht as img.shape[1]
        has_90_curve = verify_90_curve(contour_target)
        
        # initialize curve_side as false
        curve_side = False

        # find the curve side
        if has_90_curve:
            curve_side = find_curve_side(contour_target, img.shape[1])

        # calculate the error
        error = calculate_error(contour_target, img.shape[1])
        
        return error, curve_side, area
    return None, None, None

def detect_line(img_processed, img_roi):
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
    if img_processed is None:
        return None, None, None

    # process the image
    #processed_img = process_image(img)
    
    # Detect points that form a line
    contours, _ = cv2.findContours(img_processed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # verify if has a symbol on the img
    color_detected = identify_colour(img_roi)

    # analyse the contours on the image
    error, curve_side, area = analyse_contours(img_processed, contours)

    # to avoid false-positive
    if color_detected or curve_side is not False and len(contours) > 0: return 0, curve_side, color_detected, area
    
    # return the erro and curve_side and color_detected
    return error, curve_side, color_detected, area

if __name__ == '__main__':
    #import matplotlib.pyplot as plt 

    def download_image(img, erro, path, image_name, color_detected, curve_side=False):
        #plt.title(f'Erro = {erro}°, Curve = {curve_side}, Color: {color_detected}')
        #plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        #plt.show()
        #plt.savefig(f"{path}/analised/{image_name}-analised.jpg")
        pass 

    path = 'datas/lines/'
    images = [f for f in os.listdir(path) if f.endswith('.jpg')]
    
    # for a specified file
    #images = ["ladrinho_embranco.jpg"]
    
    for image_name in images:
        print(path + image_name)
        img = cv2.imread(path + image_name)
        #img = cv2.imread(image_name)
        img_processed = process_image(img)

        erro, curve_side, color_detected = detect_line(img_processed, img)
        print(f"Erro: {erro}|isCurve: {curve_side}|has_colour: {color_detected}")

        image_name, type_file = image_name.split('.jpg')
        #download_image(img, erro, path, image_name, color_detected, curve_side)
        print('-'*35)
