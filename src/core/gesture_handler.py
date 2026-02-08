"""
GestureHandler - Collaborator class for hands-free workout control.

Extracts gesture handling responsibility from SessionManager (SRP compliance).
Maps detected gestures to workout actions.
"""
import logging
from typing import Optional, Dict
import numpy as np
from src.core.gesture_detector import GestureDetector


class GestureHandler:
    """
    Handles gesture detection and action mapping for SessionManager.
    
    This class encapsulates the gesture detection logic that was previously
    embedded in SessionManager, improving Single Responsibility compliance.
    
    Responsibilities:
    - Wraps GestureDetector for pose-based gesture recognition
    - Maps gestures to action strings (e.g., "THUMBS_UP" -> "CONTINUE")
    """
    
    # Gesture to action mapping
    GESTURE_ACTIONS: Dict[str, str] = {
        "THUMBS_UP": "CONTINUE",
        # Future gestures can be added here:
        # "OPEN_PALM": "PAUSE",
        # "FIST": "STOP",
    }
    
    def __init__(self, stability_frames: int = 10, confidence_threshold: float = 0.6) -> None:
        """
        Initialize GestureHandler with a GestureDetector.
        
        Args:
            stability_frames: Number of consecutive frames gesture must be detected
            confidence_threshold: Minimum keypoint confidence required
        """
        self.detector = GestureDetector(
            stability_frames=stability_frames,
            confidence_threshold=confidence_threshold
        )
        self._logger = logging.getLogger(__name__)
    
    def process(self, keypoints: Optional[np.ndarray], current_state: str) -> Optional[str]:
        """
        Detect gesture and return corresponding action if applicable.
        
        Args:
            keypoints: Pose keypoints (17x3 array) or None
            current_state: Current workout state (e.g., "REST", "EXERCISE")
            
        Returns:
            Action string (e.g., "CONTINUE") or None if no action triggered
        """
        if keypoints is None:
            return None
        
        gesture = self.detector.detect(keypoints)
        
        if gesture:
            self._logger.info(f"GESTURE DETECTED: {gesture} in state {current_state}")
            
            # Map gesture to action
            action = self.GESTURE_ACTIONS.get(gesture)
            
            # Only return action if valid for current state
            if action == "CONTINUE" and current_state == "REST":
                self._logger.info(f"Triggering {action} via gesture!")
                return action
        
        return None
    
    def reset(self) -> None:
        """Clear gesture history."""
        self.detector.reset()
