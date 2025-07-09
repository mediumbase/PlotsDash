# models/__init__.py
from src.utils.edgedevice import load_models
from .object_detection import generate_frames

__all__ = ["load_models", "generate_frames"]