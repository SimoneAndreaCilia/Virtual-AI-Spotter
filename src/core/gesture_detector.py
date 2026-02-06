"""
Gesture detection from pose keypoints.

Detects simple gestures for hands-free control:
- THUMBS_UP: Continue/skip rest (move the arm up the shoulder)
- OPEN_PALM: Pause (to add in the future)
- FIST: Stop (to add in the future)
"""
import numpy as np
from typing import Optional, Dict, Any
from collections import deque


class GestureDetector:
    """
    Detects gestures from YOLO pose keypoints.
    
    Uses wrist and elbow positions to detect arm-based gestures.
    Requires temporal stability to avoid false positives.
    """
    
    # Keypoint indices (YOLO/COCO format)
    # 0:Nose, 1:L-Eye, 2:R-Eye, 3:L-Ear, 4:R-Ear
    # 5:L-Shoulder, 6:R-Shoulder, 7:L-Elbow, 8:R-Elbow
    # 9:L-Wrist, 10:R-Wrist, 11:L-Hip, 12:R-Hip, ...
    LEFT_SHOULDER = 5
    RIGHT_SHOULDER = 6
    LEFT_ELBOW = 7
    RIGHT_ELBOW = 8
    LEFT_WRIST = 9
    RIGHT_WRIST = 10
    
    def __init__(self, stability_frames: int = 10, confidence_threshold: float = 0.6) -> None:
        """
        Initialize gesture detector.
        
        Args:
            stability_frames: Number of consecutive frames gesture must be detected
            confidence_threshold: Minimum keypoint confidence required
        """
        self.stability_frames = stability_frames
        self.confidence_threshold = confidence_threshold
        
        # Gesture history for temporal stability
        self.gesture_history: deque = deque(maxlen=stability_frames)
    
    def detect(self, keypoints: np.ndarray) -> Optional[str]:
        """
        Detect gesture from pose keypoints.
        
        Args:
            keypoints: Array of shape (N, 3) with [x, y, confidence] per keypoint
            
        Returns:
            Gesture name ("THUMBS_UP", "WAVE") or None if no gesture detected
        """
        if keypoints is None or len(keypoints) < 17:
            self.gesture_history.append(None)
            return None
        
        # Check for raised arm gesture (thumbs up approximation)
        gesture = self._detect_raised_arm(keypoints)
        
        self.gesture_history.append(gesture)
        
        # Return gesture only if stable for N frames
        return self._get_stable_gesture()
    
    def _detect_raised_arm(self, keypoints: np.ndarray) -> Optional[str]:
        """
        Detect raised arm gesture (approximation of thumbs up).
        
        Criteria: Wrist is significantly above shoulder on either side.
        Note: Y coordinate increases downward in image space.
        """
        try:
            # Check right side
            right_wrist = keypoints[self.RIGHT_WRIST]
            right_shoulder = keypoints[self.RIGHT_SHOULDER]
            
            if (right_wrist[2] > self.confidence_threshold and 
                right_shoulder[2] > self.confidence_threshold):
                # Wrist Y is smaller (higher on screen) than shoulder by at least 50 pixels
                y_diff = right_shoulder[1] - right_wrist[1]
                if y_diff > 50:  # Wrist is 50+ pixels above shoulder
                    return "THUMBS_UP"
            
            # Check left side
            left_wrist = keypoints[self.LEFT_WRIST]
            left_shoulder = keypoints[self.LEFT_SHOULDER]
            
            if (left_wrist[2] > self.confidence_threshold and 
                left_shoulder[2] > self.confidence_threshold):
                y_diff = left_shoulder[1] - left_wrist[1]
                if y_diff > 50:
                    return "THUMBS_UP"
                    
        except (IndexError, TypeError):
            pass
        
        return None
    
    def _get_stable_gesture(self) -> Optional[str]:
        """
        Returns gesture only if detected consistently.
        
        Requires same gesture for majority of recent frames.
        """
        if len(self.gesture_history) < self.stability_frames:
            return None
        
        # Count occurrences
        gestures = [g for g in self.gesture_history if g is not None]
        
        if len(gestures) < self.stability_frames * 0.5:  # 50% threshold (was 70%)
            return None
        
        # Return most common gesture
        from collections import Counter
        counts = Counter(gestures)
        most_common = counts.most_common(1)
        
        if most_common and most_common[0][1] >= self.stability_frames * 0.5:
            return most_common[0][0]
        
        return None
    
    def reset(self) -> None:
        """Clear gesture history."""
        self.gesture_history.clear()
