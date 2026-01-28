import cv2
import numpy as np
from typing import Tuple
from src.core.interfaces import VideoSource
from config.settings import CAMERA_ID, FRAME_WIDTH, FRAME_HEIGHT

class WebcamSource(VideoSource):
    def __init__(self, source_index: int = CAMERA_ID, width: int = FRAME_WIDTH, height: int = FRAME_HEIGHT):
        self.source_index = source_index
        # Inizializza la cattura video
        self.cap = cv2.VideoCapture(self.source_index)
        
        # Imposta risoluzione (HD per default)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        # Check immediato se la camera è accessibile
        if not self.cap.isOpened():
            raise ValueError(f"Impossibile aprire la webcam con indice {source_index}")

    def get_frame(self) -> Tuple[bool, np.ndarray]:
        """
        Legge un frame dalla webcam.
        Returns: (ret, frame)
        """
        if not self.cap.isOpened():
            return False, np.array([])
        
        ret, frame = self.cap.read()
        return ret, frame

    def release(self):
        """Rilascia le risorse hardware."""
        if self.cap.isOpened():
            self.cap.release()