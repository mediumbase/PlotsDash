import tflite_runtime.interpreter as tflite
import logging
import os

# Configure logging to match app.py
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

def load_models(models):
    """Load all interpreters and labels for Edge TPU classification."""
    interpreters = {}
    labels = {}

    # Try standard Edge TPU library locations
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
            except ValueError as e:
                logging.warning(f"Failed to load delegate from {path}: {e}")
                continue

    if delegate is None:
        logging.warning("No valid Edge TPU delegate found; using CPU for inference")

    for category, paths in models.items():
        model_path = paths.get("model_path")
        label_path = paths.get("label_path")

        # Validate file existence
        if not model_path or not os.path.exists(model_path):
            logging.error(f"Model file not found for {category}: {model_path}")
            continue
        if not label_path or not os.path.exists(label_path):
            logging.error(f"Label file not found for {category}: {label_path}")
            continue

        try:
            # Initialize interpreter with Edge TPU delegate if applicable
            interpreter = tflite.Interpreter(
                model_path=model_path,
                experimental_delegates=[delegate] if delegate and "_edgetpu" in model_path else []
            )
            interpreter.allocate_tensors()
            interpreters[category] = interpreter

            # Load and clean labels
            with open(label_path, "r") as f:
                labels[category] = [line.strip() for line in f if line.strip()]

            logging.info(f"Model loaded successfully for {category} classification")
        except ValueError as e:
            logging.error(f"Failed to initialize interpreter for {category}: {e}")
        except IOError as e:
            logging.error(f"Failed to read labels for {category}: {e}")
        except Exception as e:
            logging.error(f"Unexpected error loading {category} model or labels: {e}")

    return interpreters, labels

if __name__ == "__main__":
    test_models = {
        "plants": {
            "model_path": "data_model/mobilenet_v2_1.0_224_inat_plant_quant.tflite",
            "label_path": "data_model/inat_plant_labels.txt"
        }
    }
    interpreters, labels = load_models(test_models)
    print(f"Loaded interpreters: {list(interpreters.keys())}")
    print(f"Loaded labels: {list(labels.keys())}")