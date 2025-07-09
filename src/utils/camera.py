# src/utils/camera.py
import cv2
import logging
import os
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class CameraManager:
    def __init__(self, index=0, width=640, height=480, retries=3, delay=3):
        self.camera = None
        self.index = index
        self.width = width
        self.height = height
        self.retries = retries
        self.delay = delay

    def get_camera(self):
        if self.camera and self.camera.isOpened():
            return self.camera

        for attempt in range(self.retries):
            try:
                logging.info(f"Attempting to open camera at index {self.index}, attempt {attempt + 1}")
                self.camera = cv2.VideoCapture(self.index, cv2.CAP_V4L2)
                if not self.camera.isOpened():
                    logging.error(f"Failed to open camera at index {self.index}")
                    self.camera = None
                    time.sleep(self.delay)
                    continue

                # Set properties
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self.camera.set(cv2.CAP_PROP_FPS, 30)
                self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
                self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 1)

                # Verify settings
                actual_width = self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)
                actual_height = self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
                fps = self.camera.get(cv2.CAP_PROP_FPS)
                logging.info(f"Camera initialized: {actual_width}x{actual_height} @ {fps} FPS")

                # Test frame read
                success, frame = self.camera.read()
                if not success or frame is None or not frame.any():
                    logging.error(f"Initial frame read failed or returned empty frame: success={success}, frame={frame}")
                    self.release()
                    time.sleep(self.delay)
                    continue
                logging.info(f"Initial frame shape: {frame.shape}")
                return self.camera
            except Exception as e:
                logging.error(f"Error initializing camera on attempt {attempt + 1}: {e}")
                self.release()
                time.sleep(self.delay)
        logging.error(f"Failed to initialize camera after {self.retries} attempts")
        self.diagnose_camera_issues()
        return None

    def release(self):
        if self.camera:
            self.camera.release()
            self.camera = None
            logging.info("Camera released")

    def __del__(self):
        self.release()

    @staticmethod
    def diagnose_camera_issues(max_devices=10):
        diagnostics = {"available_devices": [], "permissions": {}, "tips": []}
        for i in range(max_devices):
            device = f"/dev/video{i}"
            if os.path.exists(device):
                diagnostics["available_devices"].append(device)
                perms = os.stat(device)
                diagnostics["permissions"][device] = {
                    "readable": os.access(device, os.R_OK),
                    "writable": os.access(device, os.W_OK),
                }
        if not diagnostics["available_devices"]:
            diagnostics["tips"].append("No video devices found. Check USB connections.")
        else:
            diagnostics["tips"].append("Check camera permissions: sudo chmod 666 /dev/video*")
            diagnostics["tips"].append("Check for conflicting processes: sudo fuser /dev/video*")
            diagnostics["tips"].append("Test camera: ffmpeg -i /dev/video0 -f null -")
        logging.info(f"Camera diagnostics: {diagnostics}")
        return diagnostics