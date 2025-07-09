import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject
import numpy as np
import cv2
import os
import datetime
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def capture_single_photo(output_folder="/home/boss/BASE/dev_tpu/coral/dashboard/media/time_lapse", camera_device="/dev/video0", experiment_id="exp001", max_retries=3):
    """
    Capture a single photo using GStreamer and save it to a folder with a standardized naming convention.
    
    :param output_folder: Folder to save the image (default: "/home/boss/BASE/dev_tpu/coral/dashboard/media/time_lapse").
    :param camera_device: Camera device path (default: "/dev/video0").
    :param experiment_id: Unique identifier for the experiment (default: "exp001").
    :param max_retries: Maximum number of retries if the camera is busy.
    :return: Tuple (success, message) indicating whether the capture was successful.
    """
    # Log output folder details
    logging.info(f"Output folder: {output_folder}")
    logging.info(f"Output folder exists: {os.path.exists(output_folder)}")
    logging.info(f"Output folder is writable: {os.access(output_folder, os.W_OK)}")

    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Check if the output folder is writable
    if not os.access(output_folder, os.W_OK):
        logging.error(f"Output folder is not writable: {output_folder}")
        return False, f"Output folder is not writable: {output_folder}"

    # Initialize GStreamer
    Gst.init(None)

    # Retry mechanism
    for attempt in range(max_retries):
        try:
            # Define the GStreamer pipeline
            pipeline_str = (
                f"v4l2src device={camera_device} ! "
                "video/x-raw,format=YUY2,width=640,height=480 ! "
                "videoconvert ! "
                "video/x-raw,format=BGR ! "
                "appsink name=sink"
            )
            pipeline = Gst.parse_launch(pipeline_str)
            logging.info("Pipeline created successfully.")

            # Start the pipeline
            pipeline.set_state(Gst.State.PLAYING)
            logging.info("Pipeline set to PLAYING state.")

            # Get the appsink element
            appsink = pipeline.get_by_name("sink")

            # Capture a frame
            sample = appsink.emit("pull-sample")
            if sample:
                logging.info("Frame captured successfully.")
                # Convert GStreamer sample to OpenCV frame
                buffer = sample.get_buffer()
                caps = sample.get_caps()
                width = caps.get_structure(0).get_value("width")
                height = caps.get_structure(0).get_value("height")
                success, map_info = buffer.map(Gst.MapFlags.READ)
                if success:
                    frame = map_info.data
                    # Convert raw data to OpenCV format
                    img = np.ndarray((height, width, 3), dtype=np.uint8, buffer=frame)

                    # Get current date and time
                    now = datetime.datetime.now()

                    # Create a subfolder for each day to organize images
                    date_folder = now.strftime("%Y-%m-%d")
                    daily_folder = os.path.join(output_folder, date_folder)
                    os.makedirs(daily_folder, exist_ok=True)

                    # Standardized naming convention: <experiment_id>_<timestamp>.png
                    timestamp = now.strftime("%Y%m%d_%H%M%S")
                    image_name = f"{experiment_id}_{timestamp}.png"
                    image_path = os.path.join(daily_folder, image_name)

                    # Save image with lossless compression (PNG format)
                    if not cv2.imwrite(image_path, img):
                        logging.error(f"Error: Failed to save image to {image_path}")
                        return False, f"Failed to save image to {image_path}"
                    logging.info(f"Saved {image_path}")
                    return True, f"Successfully captured and saved {image_path}"
                buffer.unmap(map_info)
            else:
                logging.error("Failed to capture frame: No sample returned.")

            logging.error(f"Attempt {attempt + 1}: Failed to capture image.")
            time.sleep(1)  # Wait for 1 second before retrying
        except Exception as e:
            logging.error(f"Attempt {attempt + 1}: Error during photo capture: {e}")
            time.sleep(1)  # Wait for 1 second before retrying
        finally:
            # Stop the pipeline
            pipeline.set_state(Gst.State.NULL)
            logging.info("Camera released.")

    logging.error(f"Failed to capture image after {max_retries} attempts.")
    return False, "Failed to capture image after multiple attempts."

# Example usage
if __name__ == "__main__":
    # Capture a single photo
    success, message = capture_single_photo(
        output_folder="/home/boss/BASE/dev_tpu/coral/dashboard/media/time_lapse",  # Correct full path
        camera_device="/dev/video0",  # Camera device path
        experiment_id="exp001"  # Unique identifier for the experiment
    )

    if success:
        print(message)
    else:
        print(f"Error: {message}")