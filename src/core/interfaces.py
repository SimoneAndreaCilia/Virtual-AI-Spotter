from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Tuple, NamedTuple
from collections import deque
import numpy as np
from src.utils.geometry import calculate_angle


# Memory-efficient history entry (replaces per-frame dict allocation)
class HistoryEntry(NamedTuple):
    angle: float
    stage: str
    reps: int
    is_valid: bool

# Extended entry for PushUp (includes body_angle)
class PushUpHistoryEntry(NamedTuple):
    angle: float
    body_angle: float
    stage: str
    reps: int
    is_valid: bool

# Definizione del contratto per i risultati dell'analisi
@dataclass
class AnalysisResult:
    reps: int
    stage: str  # "up", "down", "start"
    correction: str  # Feedback e.g. "Keep back straight!"
    angle: float     # Current angle
    is_valid: bool   # Whether form is correct

class Exercise(ABC):
    """
    Abstract Base Class (Interface).
    Each new exercise (Squat, Curl, PushUp) MUST inherit from this class
    and implement these methods.
    """



    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.reps = 0
        self.stage = "start"
        # Circular buffer for recent history analysis (e.g., last 30 frames ~ 1 sec)
        self.history = deque(maxlen=30)
        # Dictionary of keypoint filters (Idx -> PointSmoother)
        self.smoothers: Dict[int, Any] = {}
        
        # Localization key for exercise display name (OCP)
        self.display_name_key: str = ""
        # Canonical exercise name for database storage
        self.exercise_id: str = ""

    def smooth_landmarks(self, landmarks: np.ndarray, timestamp: float = None) -> np.ndarray:
        """
        Applies smoothing to keypoints registered in self.smoothers.
        Returns a copy of the landmarks with filtered (x,y) coordinates.
        """
        smoothed = landmarks.copy()
        
        for idx, smoother in self.smoothers.items():
            try:
                raw_pt = (landmarks[idx][0], landmarks[idx][1])
                smooth_pt = smoother(raw_pt, t=timestamp)
                smoothed[idx][0] = smooth_pt[0]
                smoothed[idx][1] = smooth_pt[1]
            except IndexError:
                # Smoother index out of range - skip this keypoint
                continue
                
        return smoothed

    def _get_sides_to_process(self) -> list:
        """
        Returns list of sides to analyze based on self.side config.
        
        Returns:
            ["left"], ["right"], or ["left", "right"] for "both"
        """
        side = getattr(self, 'side', 'right')
        if side == "both":
            return ["left", "right"]
        return [side]

    def _calculate_side_angle(
        self,
        landmarks: np.ndarray,
        smoothed: np.ndarray,
        indices: tuple,
        confidence_threshold: float
    ) -> float:
        """
        Calculates angle for a set of 3 keypoints if confidence is sufficient.
        
        Args:
            landmarks: Original landmarks with confidence values
            smoothed: Smoothed landmarks for coordinates
            indices: Tuple of (idx1, idx2, idx3) where idx2 is the vertex
            confidence_threshold: Minimum confidence required
            
        Returns:
            Calculated angle in degrees, or None if confidence too low
        """
        idx1, idx2, idx3 = indices
        
        # Check if all keypoints have sufficient confidence
        if min(landmarks[idx1][2], landmarks[idx2][2], landmarks[idx3][2]) >= confidence_threshold:
            return calculate_angle(
                smoothed[idx1][:2],
                smoothed[idx2][:2],
                smoothed[idx3][:2]
            )
        return None

    def _is_stable_change(self, predicate, consistency_frames: int = 3) -> bool:
        """
        Checks if a condition (predicate) has been true for the last N frames.
        Useful for debouncing (avoiding state changes on spurious frames).
        
        Args:
            predicate: Function that accepts an item from history and returns bool.
            consistency_frames: Number of consecutive frames required.
            
        Returns:
            bool: True if the condition is stable.
        """
        if len(self.history) < consistency_frames:
            return False
            
        # Check the last N elements of history
        # History is a deque, so we iterate the last N
        recent_history = list(self.history)[-consistency_frames:]
        
        return all(predicate(item) for item in recent_history)

    @abstractmethod
    def process_frame(self, landmarks: np.ndarray, timestamp: float = None) -> AnalysisResult:
        """
        Takes keypoints (skeleton) and returns the analysis result.
        Optional: timestamp for handling prerecorded videos or lag.
        """
        pass

    def reset(self):
        """
        Resets the count, state, history, and filters.
        Child classes can override but should call super().reset()
        """
        self.reps = 0
        self.stage = "start"
        self.history.clear()
        for s in self.smoothers.values():
            s.reset()

class VideoSource(ABC):
    """
    Interface for video source.
    Allows swapping Webcam with Video File without breaking code.
    """
    
    @abstractmethod
    def get_frame(self) -> Tuple[bool, np.ndarray]:
        """Returns (ret, frame) like OpenCV."""
        pass

    @abstractmethod
    def release(self):
        pass