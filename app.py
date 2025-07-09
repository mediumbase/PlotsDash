import os
import logging
from logging.handlers import RotatingFileHandler
import random
import time
import threading
import base64
import io
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

import cv2
import numpy as np
import matplotlib.pyplot as plt
import mariadb
import av
from flask import Flask, render_template, jsonify, Response, request
from dotenv import load_dotenv
from dbutils.pooled_db import PooledDB
import tflite_runtime.interpreter as tflite
from src.utils.camera import CameraManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("./logs/app.log"),
        logging.StreamHandler(),
        RotatingFileHandler(
            "./logs/app_debug.log",
            maxBytes=1024*1024,
            backupCount=5
        )
    ]
)

# Ensure local directories exist
os.makedirs("./logs", exist_ok=True)
os.makedirs("./media/time_lapse", exist_ok=True)
os.makedirs("./snapshots", exist_ok=True)

app = Flask(__name__)

# Application configuration
class AppConfig:
    def __init__(self):
        load_dotenv()
        self.MYSQL_HOST = os.getenv('MYSQL_HOST', '127.0.0.1')
        self.MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
        self.MYSQL_USER = os.getenv('MYSQL_USER', 'rootdash_user')
        self.MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'adminrdash')
        self.MYSQL_DB = os.getenv('MYSQL_DB', 'rootdash_db')
        self.TIME_LAPSE_FOLDER = os.getenv('TIME_LAPSE_FOLDER', './media/time_lapse')
        self.SNAPSHOT_DIR = os.getenv('SNAPSHOT_DIR', './snapshots')
        self.SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24).hex())
        self.CAMERA_DEVICE = os.getenv('CAMERA_DEVICE', '/dev/video0')
        self.CAMERA_WIDTH = int(os.getenv('CAMERA_WIDTH', 640))
        self.CAMERA_HEIGHT = int(os.getenv('CAMERA_HEIGHT', 480))
        self.CAMERA_FPS = int(os.getenv('CAMERA_FPS', 30))
        self.JPEG_QUALITY = int(os.getenv('JPEG_QUALITY', 95))

        self.validate()

    def validate(self):
        required_vars = ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DB', 'CAMERA_DEVICE']
        missing = [var for var in required_vars if not getattr(self, var)]
        if missing:
            logging.error(f"Missing environment variables: {', '.join(missing)}")
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")
        if self.CAMERA_WIDTH <= 0 or self.CAMERA_HEIGHT <= 0:
            raise ValueError("Camera width and height must be positive")
        if self.CAMERA_FPS <= 0:
            raise ValueError("Camera FPS must be positive")
        if self.JPEG_QUALITY < 0 or self.JPEG_QUALITY > 100:
            raise ValueError("JPEG quality must be between 0 and 100")

config = AppConfig()
app.secret_key = config.SECRET_KEY

class DatabaseManager:
    def __init__(self):
        self.pool = None
        self._create_pool()
        if self.pool:
            self._init_tables()
            self.populate_sample_data()

    def _create_pool(self):
        try:
            self.pool = PooledDB(
                creator=mariadb,
                host=config.MYSQL_HOST,
                port=config.MYSQL_PORT,
                user=config.MYSQL_USER,
                password=config.MYSQL_PASSWORD,
                database=config.MYSQL_DB,
                maxconnections=5
            )
            logging.info("Database connection pool created")
        except mariadb.Error as e:
            logging.error(f"Database connection failed: {e}")
            self.pool = None

    def _init_tables(self, max_retries: int = 3, delay: int = 2):
        tables = [
            """
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME,
                analog_value INT,
                color_red INT,
                color_green INT,
                color_blue INT,
                temperature FLOAT,
                humidity FLOAT,
                light_intensity FLOAT,
                soil_moisture FLOAT
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE IF NOT EXISTS plants (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL
            ) ENGINE=InnoDB
            """,
            """
            CREATE TABLE IF NOT EXISTS growth_rate (
                id INT AUTO_INCREMENT PRIMARY KEY,
                plant_id INT,
                rate FLOAT,
                height FLOAT,
                time_after_planting INT,
                FOREIGN KEY (plant_id) REFERENCES plants(id)
            ) ENGINE=InnoDB
            """
        ]
        for attempt in range(max_retries):
            conn = None
            try:
                conn = self.pool.connection()
                cursor = conn.cursor()
                for table_sql in tables:
                    cursor.execute(table_sql)
                conn.commit()
                logging.info("Database tables initialized")
                return
            except mariadb.Error as e:
                logging.error(f"Table init attempt {attempt + 1} failed: {e}")
                time.sleep(delay)
            finally:
                if conn:
                    conn.close()
        logging.error("Failed to initialize database tables")

    def populate_sample_data(self):
        conn = None
        try:
            conn = self.pool.connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM plants")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO plants (name) VALUES ('Tomato'), ('Basil')")
                conn.commit()
                logging.info("Inserted sample plants")
            cursor.execute("SELECT COUNT(*) FROM growth_rate")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO growth_rate (plant_id, rate, height, time_after_planting)
                    VALUES (1, 0.5, 10.0, 10), (1, 0.6, 12.0, 20), (2, 0.3, 8.0, 15)
                """)
                conn.commit()
                logging.info("Inserted sample growth data")
        except mariadb.Error as e:
            logging.error(f"Failed to populate sample data: {e}")
        finally:
            if conn:
                conn.close()

    def execute_query(self, query: str, params: tuple = None, commit: bool = False) -> Optional[List[Tuple]]:
        if not self.pool:
            return None
        conn = None
        try:
            conn = self.pool.connection()
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            if commit:
                conn.commit()
            if cursor.description:
                return cursor.fetchall()
            return []
        except mariadb.Error as e:
            logging.error(f"Query failed: {e}")
            return None
        finally:
            if conn:
                conn.close()

db_manager = DatabaseManager()
camera_manager = CameraManager(
    index=config.CAMERA_DEVICE,
    width=config.CAMERA_WIDTH,
    height=config.CAMERA_HEIGHT
)

last_detections = deque(maxlen=5)
is_feed_paused = False

# Initialize TFLite interpreter for plant detection
model_path = os.path.join("data_model", "mobilenet_v2_1.0_224_inat_plant_quant.tflite")
label_path = os.path.join("data_model", "inat_plant_labels.txt")

# Load labels
try:
    with open(label_path, "r") as f:
        labels = [line.strip() for line in f if line.strip()]
    logging.info("Plant detection labels loaded successfully")
except Exception as e:
    logging.error(f"Failed to load plant detection labels: {e}")
    labels = []

# Load Edge TPU delegate with fallback to CPU
delegate_paths = [
    "/usr/lib/aarch64-linux-gnu/libedgetpu.so.1.0",
    "/usr/lib/aarch64-linux-gnu/libedgetpu.so.1",
    "/usr/lib/libedgetpu.so.1",
    "/usr/local/lib/libedgetpu.so.1"
]
delegate = None
for path in delegate_paths:
    if os.path.exists(path):
        try:
            delegate = tflite.load_delegate(path)
            logging.info(f"Found Edge TPU delegate at {path}")
            break
        except Exception as e:
            logging.warning(f"Failed to load delegate from {path}: {e}")
if delegate is None:
    logging.warning("No Edge TPU delegate found; using CPU for inference")

# Load interpreter
try:
    interpreter = tflite.Interpreter(
        model_path=model_path,
        experimental_delegates=[delegate] if delegate else []
    )
    interpreter.allocate_tensors()
    logging.info("Plant detection model loaded successfully")
except Exception as e:
    logging.error(f"Failed to load plant detection model: {e}")
    interpreter = None

class TimeLapseController:
    def __init__(self):
        self.is_running = False
        self.thread = None
        self.lock = threading.Lock()

    def capture(self, output_folder: str, interval: float, num_images: int):
        for i in range(num_images):
            with self.lock:
                if not self.is_running:
                    break
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(output_folder, f"timelapse_{timestamp}.jpg")
            camera = camera_manager.get_camera()
            if camera:
                ret, frame = camera.read()
                if ret and frame is not None:
                    cv2.imwrite(filename, frame, [cv2.IMWRITE_JPEG_QUALITY, config.JPEG_QUALITY])
                    logging.info(f"Captured time-lapse image {i + 1}/{num_images}: {filename}")
                else:
                    logging.warning(f"Failed to capture time-lapse image {i + 1}")
            else:
                logging.warning(f"Camera unavailable for time-lapse image {i + 1}")
            time.sleep(interval)
        with self.lock:
            self.is_running = False

    def start(self, folder: str, interval: float, num_images: int) -> Tuple[bool, str]:
        with self.lock:
            if self.is_running:
                return False, "Time-lapse already running"
            if interval <= 0 or num_images <= 0:
                return False, "Invalid interval or number of images"
            self.is_running = True
            self.thread = threading.Thread(
                target=self.capture,
                kwargs={'output_folder': folder, 'interval': interval, 'num_images': num_images},
                daemon=True
            )
            self.thread.start()
            return True, "Time-lapse started"

    def stop(self) -> Tuple[bool, str]:
        with self.lock:
            if self.is_running:
                self.is_running = False
                return True, "Time-lapse stopped"
            return False, "No time-lapse running"

time_lapse_controller = TimeLapseController()

def generate_frames() -> bytes:
    camera = camera_manager.get_camera()
    if not camera:
        logging.error("Camera unavailable for video feed")
        return
    while True:
        if is_feed_paused:
            time.sleep(0.1)
            continue
        ret, frame = camera.read()
        if not ret or frame is None:
            logging.warning("Camera frame read failed")
            camera_manager.release()  # Release and retry
            camera = camera_manager.get_camera()
            if not camera:
                logging.error("Failed to reinitialize camera for video feed")
                time.sleep(0.1)
                continue
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, config.JPEG_QUALITY])
        if not ret:
            logging.error("Failed to encode frame")
            continue
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route("/")
def index() -> str:
    return render_template("index.html")

@app.route("/video_feed")
def video_feed() -> Response:
    if is_feed_paused:
        return jsonify({"error": "Feed is paused"}), 503
    if not camera_manager.get_camera():
        return jsonify({"error": "Camera unavailable"}), 503
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/sensor_data")
def sensor_data() -> Response:
    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "analog_value": random.randint(0, 1023),
        "color_red": random.randint(0, 255),
        "color_green": random.randint(0, 255),
        "color_blue": random.randint(0, 255),
        "temperature": random.uniform(10, 30),
        "humidity": random.uniform(20, 80),
        "light_intensity": random.uniform(100, 1000),
        "soil_moisture": random.uniform(0, 100)
    }
    if db_manager.pool:
        result = db_manager.execute_query(
            """
            INSERT INTO sensor_data 
            (timestamp, analog_value, color_red, color_green, color_blue, 
             temperature, humidity, light_intensity, soil_moisture)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            tuple(data.values()),
            commit=True
        )
        if result is None:
            logging.warning("Failed to store sensor data")
    return jsonify(data)

@app.route("/pause_feed", methods=["POST"])
def pause_feed():
    global is_feed_paused
    is_feed_paused = True
    logging.info("Live feed paused")
    return jsonify({"success": True, "message": "Live feed paused"}), 200

@app.route("/resume_feed", methods=["POST"])
def resume_feed():
    global is_feed_paused
    is_feed_paused = False
    logging.info("Live feed resumed")
    return jsonify({"success": True, "message": "Live feed resumed"}), 200

@app.route("/start_time_lapse", methods=["POST"])
def start_time_lapse():
    data = request.get_json() or {}
    interval = float(data.get('interval', 30))
    num_images = int(data.get('num_images', 10))
    success, message = time_lapse_controller.start(config.TIME_LAPSE_FOLDER, interval, num_images)
    return jsonify({"success": success, "message": message}), 200 if success else 400

@app.route("/stop_time_lapse", methods=["POST"])
def stop_time_lapse():
    success, message = time_lapse_controller.stop()
    return jsonify({"success": success, "message": message}), 200 if success else 400

@app.route("/growth_graph")
def growth_graph():
    try:
        result = db_manager.execute_query("""
            SELECT p.name AS plant_name, gr.height, gr.time_after_planting
            FROM growth_rate gr
            JOIN plants p ON gr.plant_id = p.id
            ORDER BY gr.time_after_planting
        """)
        if not result:
            return jsonify({"error": "No growth data found"}), 404
        data = {}
        for plant_name, height, time in result:
            data.setdefault(plant_name, {"time": [], "height": []})
            data[plant_name]["time"].append(time)
            data[plant_name]["height"].append(float(height))
        plt.figure(figsize=(10, 6))
        for plant_name, values in data.items():
            plt.plot(values["time"], values["height"], label=plant_name, marker='o')
        plt.title("Plant Growth Over Time")
        plt.xlabel("Time (Days)")
        plt.ylabel("Height (cm)")
        plt.legend()
        plt.grid(True)
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode("utf-8")
        plt.close()
        return jsonify({"image": image_base64})
    except Exception as e:
        logging.error(f"Graph generation error: {e}")
        return jsonify({"error": "Failed to generate growth graph"}), 500

@app.route("/growth_rate")
def growth_rate():
    try:
        result = db_manager.execute_query("""
            SELECT gr.rate, gr.height, gr.time_after_planting, p.name AS plant_name
            FROM growth_rate gr
            JOIN plants p ON gr.plant_id = p.id
        """)
        data = [{
            "rate": row[0],
            "height": row[1],
            "time_after_planting": row[2],
            "plant_name": row[3]
        } for row in result]
        return jsonify(data)
    except mariadb.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify([]), 500

@app.route("/seasonal_status")
def seasonal_status():
    try:
        result = db_manager.execute_query("""
            SELECT gr.time_after_planting, p.name AS plant_name
            FROM growth_rate gr
            JOIN plants p ON gr.plant_id = p.id
        """)
        seasonal_status_data = []
        for time_after_planting, plant_name in result:
            start_date = (datetime.now() - timedelta(days=time_after_planting)).strftime("%Y-%m-%d")
            current_stage = ("Early Growth" if time_after_planting < 30 else
                            "Mid Growth" if time_after_planting < 60 else
                            "Late Growth")
            seasonal_status_data.append({
                "plant_name": plant_name,
                "start_date": start_date,
                "current_stage": current_stage
            })
        return jsonify(seasonal_status_data)
    except mariadb.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify([]), 500

@app.route("/harvest_scheduler")
def harvest_scheduler():
    try:
        result = db_manager.execute_query("""
            SELECT gr.time_after_planting, p.name AS plant_name
            FROM growth_rate gr
            JOIN plants p ON gr.plant_id = p.id
        """)
        harvest_scheduler_data = []
        for time_after_planting, plant_name in result:
            planting_date = datetime.now() - timedelta(days=time_after_planting)
            predicted_harvest_date = planting_date + timedelta(days=90)
            harvest_scheduler_data.append({
                "plant_name": plant_name,
                "predicted_harvest_date": predicted_harvest_date.strftime("%Y-%m-%d")
            })
        return jsonify(harvest_scheduler_data)
    except mariadb.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify([]), 500

@app.route("/inference_data")
def inference_data():
    if interpreter is None or not labels:
        return jsonify({"error": "Inference model or labels not loaded"}), 500

    for attempt in range(3):  # Retry up to 3 times
        try:
            camera = camera_manager.get_camera()
            if not camera:
                logging.warning(f"Camera unavailable on attempt {attempt + 1}")
                time.sleep(0.5)
                continue
            ret, frame = camera.read()
            if not ret or frame is None:
                logging.warning(f"Failed to capture camera frame on attempt {attempt + 1}")
                camera_manager.release()
                time.sleep(0.5)
                continue

            # Resize frame to model input size (224x224 for MobileNet)
            img = cv2.resize(frame, (224, 224))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = np.expand_dims(img, axis=0).astype(np.uint8)

            # Run inference
            interpreter.set_tensor(interpreter.get_input_details()[0]['index'], img)
            interpreter.invoke()
            output_details = interpreter.get_output_details()
            probabilities = interpreter.get_tensor(output_details[0]['index'])[0]

            # Format detections
            results = []
            score_threshold = 0.3
            for i, score in enumerate(probabilities):
                if score > score_threshold and i < len(labels):
                    results.append({
                        "category": "plant",
                        "label": labels[i],
                        "confidence": float(score * 100)  # Convert to percentage
                    })

            # Store in last_detections
            last_detections.extend(results)
            return jsonify(list(last_detections)), 200
        except Exception as e:
            logging.error(f"Inference error on attempt {attempt + 1}: {e}")
            camera_manager.release()
            time.sleep(0.5)
    return jsonify({"error": "Failed to perform inference after retries"}), 500

@app.route("/health")
def health_check():
    status = {
        "database": bool(db_manager.pool),
        "camera": bool(camera_manager.get_camera()),
        "inference": interpreter is not None and bool(labels),
        "worker": True,
        "timestamp": datetime.now().isoformat()
    }
    return jsonify(status), 200 if all([status["database"], status["camera"], status["inference"], status["worker"]]) else 503

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000, threaded=True)
    except KeyboardInterrupt:
        logging.info("Shutting down...")
    finally:
        camera_manager.release()
        logging.info("Application stopped")