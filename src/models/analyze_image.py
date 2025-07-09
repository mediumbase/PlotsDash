import cv2
import numpy as np
import os
from datetime import datetime
import csv
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants for reference object sizes (in inches)
REFERENCE_OBJECTS = {
    "U.S. Quarter": {"diameter": 0.955},  # Diameter in inches
    "Credit Card": {"width": 3.37, "height": 2.125},  # Width and height in inches
    "A4 Paper": {"width": 8.27, "height": 11.69},  # Width and height in inches
    "Baseball": {"diameter": 2.86},  # Diameter in inches
    "Soccer Ball": {"diameter": 8.6},  # Diameter in inches
    "Ping Pong Ball": {"diameter": 1.57},  # Diameter in inches
}

# Default pixels per inch (PPI) if no reference object is detected
DEFAULT_PPI = int(os.getenv("PIXELS_PER_INCH", 100))

def detect_reference_object(image):
    """
    Detect a reference object in the image and calculate pixels per inch (PPI).
    :param image: Input image (NumPy array).
    :return: Pixels per inch (PPI) or None if no reference object is found.
    """
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Detect circles (for round objects like quarters, baseballs, etc.)
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=50,
            param1=100,
            param2=30,
            minRadius=10,
            maxRadius=200
        )

        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            for (x, y, r) in circles:
                # Check if the detected circle matches a known reference object
                diameter_pixels = r * 2
                for obj_name, obj_data in REFERENCE_OBJECTS.items():
                    if "diameter" in obj_data:
                        expected_diameter = obj_data["diameter"]
                        ppi = diameter_pixels / expected_diameter
                        logging.info(f"Detected {obj_name}. Pixels per inch (PPI): {ppi}")
                        return ppi

        # Detect rectangles (for credit cards, A4 paper, etc.)
        edges = cv2.Canny(blurred, 100, 200)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            # Approximate the contour to a polygon
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            # Check if the contour has 4 vertices (likely a rectangle)
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = float(w) / h

                # Compare aspect ratio to known reference objects
                for obj_name, obj_data in REFERENCE_OBJECTS.items():
                    if "width" in obj_data and "height" in obj_data:
                        expected_aspect_ratio = obj_data["width"] / obj_data["height"]
                        if abs(aspect_ratio - expected_aspect_ratio) < 0.1:  # Allow some tolerance
                            # Calculate PPI based on width or height
                            ppi_width = w / obj_data["width"]
                            ppi_height = h / obj_data["height"]
                            ppi = (ppi_width + ppi_height) / 2  # Average PPI
                            logging.info(f"Detected {obj_name}. Pixels per inch (PPI): {ppi}")
                            return ppi

        logging.warning("No reference object detected. Using default PPI.")
        return None
    except Exception as e:
        logging.error(f"Error detecting reference object: {e}")
        return None

def analyze_image(image):
    """
    Analyze an image to detect plants and measure their size.
    :param image: Input image (NumPy array).
    :return: List of dictionaries with plant width and height in inches.
    """
    try:
        # Detect reference object and calculate PPI
        ppi = detect_reference_object(image)
        if ppi is None:
            ppi = DEFAULT_PPI  # Fallback to default PPI if no reference object is found

        # Convert to grayscale and detect edges
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)

        # Find contours in the edges
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        plant_data = []
        for contour in contours:
            if cv2.contourArea(contour) > 500:  # Filter out small contours
                x, y, w, h = cv2.boundingRect(contour)
                # Convert pixel dimensions to inches using the calculated PPI
                width_inches = w / ppi
                height_inches = h / ppi
                plant_data.append({"width_inches": width_inches, "height_inches": height_inches})

        return plant_data
    except Exception as e:
        logging.error(f"Error analyzing image: {e}")
        return []

def find_newest_image(directory):
    """
    Find the newest image file in the specified directory.
    :param directory: Path to the directory.
    :return: Path to the newest image file, or None if no images are found.
    """
    try:
        # List all image files in the directory
        image_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not image_files:
            logging.warning(f"No images found in the directory: {directory}")
            return None
        # Return the newest image file
        newest_image = max(image_files, key=os.path.getmtime)
        return newest_image
    except FileNotFoundError:
        logging.error(f"Directory not found: {directory}")
        return None
    except Exception as e:
        logging.error(f"Error finding newest image: {e}")
        return None

def process_image(image_path, output_folder, plant_id, experiment_id):
    """
    Process a single image to detect plants and analyze their sizes.
    :param image_path: Path to the input image.
    :param output_folder: Folder to save the results.
    :param plant_id: ID of the plant (from the `plants` table).
    :param experiment_id: ID of the experiment (from the `experiments` table).
    """
    try:
        # Load the image
        image = cv2.imread(image_path)
        if image is None:
            logging.error(f"Error: Unable to load image at {image_path}")
            return

        # Analyze the image
        plant_data = analyze_image(image)

        # Prepare data for CSV
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = os.path.basename(image_path)

        # Save the results to a CSV file
        os.makedirs(output_folder, exist_ok=True)
        csv_file = os.path.join(output_folder, "time_lapse_data.csv")

        # Write to CSV
        file_exists = os.path.isfile(csv_file)
        with open(csv_file, mode="a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["timestamp", "plant_id", "experiment_id", "image_path", "width", "height"])
            if not file_exists:
                writer.writeheader()  # Write header if file doesn't exist

            # Write a row for each plant
            for data in plant_data:
                writer.writerow({
                    "timestamp": timestamp,
                    "plant_id": plant_id,
                    "experiment_id": experiment_id,
                    "image_path": filename,
                    "width": data["width_inches"],
                    "height": data["height_inches"]
                })

        # Set secure file permissions (read/write by owner only)
        os.chmod(csv_file, 0o600)

        logging.info(f"Analysis results appended to {csv_file}")
    except Exception as e:
        logging.error(f"Error processing image: {e}")

def main():
    try:
        # Get the absolute path to the script's directory
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Construct the relative paths to the time_lapse and convert directories
        time_lapse_dir = os.path.abspath(os.path.join(script_dir, "../../media/time_lapse"))
        output_folder = os.path.abspath(os.path.join(script_dir, "../../media/convert"))

        # Debugging: Print the resolved paths
        logging.info(f"Resolved time_lapse directory: {time_lapse_dir}")
        logging.info(f"Resolved output folder: {output_folder}")

        # Find the newest image in the directory
        newest_image_path = find_newest_image(time_lapse_dir)
        if newest_image_path:
            logging.info(f"Analyzing the newest image: {newest_image_path}")
            
            # Get plant_id and experiment_id from environment variables
            plant_id = int(os.getenv("PLANT_ID", 1))  # Default to 1 if not set
            experiment_id = int(os.getenv("EXPERIMENT_ID", 1))  # Default to 1 if not set

            # Process the image and save results
            process_image(newest_image_path, output_folder, plant_id, experiment_id)
        else:
            logging.warning("No images found in the directory.")
    except Exception as e:
        logging.error(f"Error in main function: {e}")

# Run the script (for standalone usage)
if __name__ == "__main__":
    main()