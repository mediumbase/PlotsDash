GardenHub
GardenHub is a sophisticated Flask-based web application designed for real-time plant monitoring. It leverages a USB camera for live video feeds, TensorFlow Lite for plant classification, and a MariaDB database for storing sensor and growth data. With optional Edge TPU acceleration, it provides a robust platform for tracking plant health, growth, and species identification through a user-friendly web interface.
Features

Live Video Streaming: Real-time feed from a USB camera (/dev/video0) at 640x480@30fps, accessible via /video_feed.
Sensor Monitoring: Simulated data for temperature, humidity, light intensity, and soil moisture, stored in MariaDB and served at /sensor_data.
Plant Classification: Identifies plant species using mobilenet_v2_1.0_224_inat_plant_quant.tflite at /inference_data, integrated with Wikipedia for species insights.
Growth Analytics: Visualizes plant height over time at /growth_graph, with detailed data from /growth_rate, /seasonal_status, and /harvest_scheduler.
Time-Lapse Photography: Captures images at configurable intervals, saved in ./media/time_lapse.
Edge TPU Support: Accelerates inference with Coral USB Accelerator, with seamless fallback to CPU.

Requirements

Hardware: Raspberry Pi or similar with a USB camera, optional Coral USB Accelerator.
Software:
Debian-based OS (e.g., Raspberry Pi OS Bookworm).
Python 3.8.
MariaDB server.
OpenCV (opencv-contrib-python==4.8.1.78).
TensorFlow Lite Runtime (tflite-runtime==2.14.0).
Coral USB Accelerator drivers (if using Edge TPU).



Setup Instructions

Clone the Repository:
git clone <repository_url>
cd /HUB/enterprise/apps/python/app_gardenhub


Set Up Virtual Environment:
python3.8 -m venv ienv
source ienv/bin/activate


Install System Dependencies:
sudo apt update
sudo apt install -y libedgetpu1-std libusb-1.0-0-dev python3-opencv mariadb-server libmariadb-dev ffmpeg


Set Up Coral USB Accelerator (if using):
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/coral-edgetpu-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/coral-edgetpu-archive-keyring.gpg] https://packages.cloud.google.com/apt coral-edgetpu-stable main" | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list
sudo apt update
sudo apt install -y libedgetpu1-std
sudo ln -sf /usr/lib/aarch64-linux-gnu/libedgetpu.so.1.0 /usr/lib/libedgetpu.so.1
sudo ln -sf /usr/lib/aarch64-linux-gnu/libedgetpu.so.1.0 /usr/local/lib/libedgetpu.so.1
sudo chmod 644 /usr/lib/aarch64-linux-gnu/libedgetpu.so*
sudo ldconfig
echo 'SUBSYSTEMS=="usb", ATTRS{idVendor}=="1a6e", ATTRS{idProduct}=="089a", MODE="0664", GROUP="plugdev", TAG+="uaccess"' | sudo tee /etc/udev/rules.d/99-coral-edgetpu.rules
echo 'SUBSYSTEMS=="usb", ATTRS{idVendor}=="18d1", ATTRS{idProduct}=="9302", MODE="0664", GROUP="plugdev", TAG+="uaccess"' | sudo tee -a /etc/udev/rules.d/99-coral-edgetpu.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
sudo usermod -a -G plugdev $USER
echo 'export LD_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc


Install Python Dependencies:
pip install --upgrade pip
pip install -r requirements.txt
pip install opencv-contrib-python==4.8.1.78 tflite-runtime==2.14.0


Configure MariaDB:
sudo systemctl start mariadb
sudo mysql -u root -p

In the MariaDB prompt:
CREATE DATABASE rootdash_db;
CREATE USER 'rootdash_user'@'localhost' IDENTIFIED BY 'adminrdash';
GRANT ALL PRIVILEGES ON rootdash_db.* TO 'rootdash_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;


Configure Environment Variables:Create or edit .env in the project root:
MYSQL_HOST=127.0.0.1
MYSQL_USER=rootdash_user
MYSQL_PASSWORD=adminrdash
MYSQL_DB=rootdash_db
TIME_LAPSE_FOLDER=./media/time_lapse
SNAPSHOT_DIR=./snapshots
CAMERA_DEVICE=/dev/video0
CAMERA_WIDTH=640
CAMERA_HEIGHT=480
JPEG_QUALITY=95
FPS=30
SECRET_KEY=your_secure_key


Run the Application:
source ienv/bin/activate
python3.8 app.py

Access the web interface at http://localhost:5000 or http://172.20.20.20:5000.


Troubleshooting

Camera Issues:

Verify device:ls -l /dev/video*
ffmpeg -i /dev/video0 -f null -


Check for conflicting processes:sudo fuser /dev/video*
sudo kill -9 <pid>


Ensure permissions:sudo chmod 666 /dev/video*
sudo usermod -a -G video $USER


Run diagnostics:python3 -c "from src.utils.camera import CameraManager; print(CameraManager.diagnose_camera_issues())"




Edge TPU Issues:

Verify Coral USB Accelerator:lsusb | grep -E "1a6e:089a|18d1:9302"


Check library dependencies:ldd /usr/lib/aarch64-linux-gnu/libedgetpu.so.1


Test delegate:python3 -c "import tflite_runtime.interpreter as tflite; delegate = tflite.load_delegate('/usr/lib/aarch64-linux-gnu/libedgetpu.so.1.0'); print('Success')"




Inference Errors:

Validate model outputs:python3 -c "import tflite_runtime.interpreter as tflite; interpreter = tflite.Interpreter(model_path='data_model/mobilenet_v2_1.0_224_inat_plant_quant.tflite'); interpreter.allocate_tensors(); print(interpreter.get_output_details())"


Ensure data_model/inat_plant_labels.txt matches model classes.


OpenCV Issues:

Verify version:python3 -c "import cv2; print(cv2.__version__)"


Reinstall if needed:pip uninstall opencv-python opencv-contrib-python -y
pip install opencv-contrib-python==4.8.1.78




Logs:

Check ./logs/app.log for server-side errors.
Use browser console (F12) for client-side issues with static/js/dataDetection.js.



Directory Structure

app.py: Main Flask application.
.env: Environment variables.
data_model/: TensorFlow Lite models and labels (mobilenet_v2_1.0_224_inat_plant_quant.tflite, inat_plant_labels.txt, etc.).
static/: JavaScript and CSS files (dataDetection.js, styles.css, etc.).
templates/: HTML templates for the web interface.
src/utils/: Utility scripts (camera.py, edgedevice.py, etc.).
logs/: Application logs.
media/time_lapse/: Time-lapse images.
snapshots/: Snapshot images.

Notes

The application uses tflite-runtime for inference, with Edge TPU acceleration optional.
MariaDB reliably stores sensor and growth data.
Ensure the Coral USB Accelerator is connected if using Edge TPU.
The edgedevice.py script is not currently used but supports model loading for future extensions.
