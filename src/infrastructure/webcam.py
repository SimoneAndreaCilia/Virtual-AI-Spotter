import cv2
import numpy as np
from typing import Tuple
from src.core.interfaces import VideoSource
from src.core.exceptions import VideoSourceError
from config.settings import CAMERA_ID, FRAME_WIDTH, FRAME_HEIGHT

class WebcamSource(VideoSource):
    def __init__(self, source_index: int = CAMERA_ID, width: int = FRAME_WIDTH, height: int = FRAME_HEIGHT):
        self.source_index = source_index
        # Initialize video capture
        self.cap = cv2.VideoCapture(self.source_index)
        
        # Set resolution (HD by default)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        # Immediate check if camera is accessible
        if not self.cap.isOpened():
            raise VideoSourceError(f"Unable to open webcam with index {source_index}")

    def get_frame(self) -> Tuple[bool, np.ndarray]:
        """
        Reads a frame from the webcam.
        Returns: (ret, frame)
        """
        if not self.cap.isOpened():
            return False, np.array([])
        
        ret, frame = self.cap.read()
        return ret, frame

    def release(self):
        """Release hardware resources."""
        if self.cap.isOpened():
            self.cap.release()