from ultralytics import YOLO
import logging
from typing import Any

class PoseEstimator:
    def __init__(self, model_path: str, device: str):
        self.model_path = model_path
        self.device = device
        self.model = None
        self._load_model()

    def _load_model(self):
        try:
            logging.info(f"Loading YOLO model from {self.model_path}...")
            self.model = YOLO(self.model_path)
            self.model.to(self.device)
            logging.info(f"Model loaded on {self.device}")
        except Exception as e:
            logging.error(f"Failed to load model: {e}")
            raise

    def predict(self, frame) -> Any:
        """
        Runs inference on the frame.
        Returns the raw results object (to be parsed by logic layer).
        """
        if self.model is None:
            return None
            
        results = self.model(frame, verbose=False)
        return results
