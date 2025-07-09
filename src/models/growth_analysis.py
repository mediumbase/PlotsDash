# src/models/growth_analysis.py
import cv2

def analyze_image(image_path):
    """
    Analyze an image to detect plants and measure their size.
    :param image_path: Path to the image file.
    :return: List of plant data (width, height).
    """
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    plant_data = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        plant_data.append({"width": w, "height": h})

    return plant_data