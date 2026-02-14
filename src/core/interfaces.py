from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple, NamedTuple, Optional, Dict, Any
from collections import deque
import numpy as np
from src.utils.geometry import calculate_angle
from src.core.config_types import ExerciseConfig


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

# Definition of the contract for the analysis results
@dataclass
class AnalysisResult:
    reps: int
    stage: str  # "up", "down", "start"
    correction: str  # Feedback e.g. "Keep back straight!"
    angle: float     # Current angle
    is_valid: bool   # Whether form is correct


# Display metadata for exercise states (OCP: owned by each Exercise)
class StateDisplayInfo(NamedTuple):
    """UI display properties for an exercise state."""
    label_key: str   # i18n translation key (e.g. "curl_state_up")
    color: tuple     # BGR color tuple (e.g. (0, 255, 0))
    category: str    # "up", "down", or "neutral"

class Exercise(ABC):
    """
    Abstract Base Class (Interface).
    Each new exercise (Squat, Curl, PushUp) MUST inherit from this class
    and implement these methods.
    """



    def __init__(self, config: ExerciseConfig):
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

    def smooth_landmarks(self, landmarks: np.ndarray, timestamp: Optional[float] = None) -> np.ndarray:
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

    def get_state_display(self, state: str) -> StateDisplayInfo:
        """
        Returns display metadata for a given exercise state.
        
        Override in subclasses to provide exercise-specific state displays.
        Falls back to generic defaults for common states (start, finished, unknown).
        """
        _defaults = {
            "start": StateDisplayInfo("state_start", (255, 255, 255), "neutral"),
            "finished": StateDisplayInfo("state_finished", (0, 255, 0), "neutral"),
            "unknown": StateDisplayInfo("state_unknown", (128, 128, 128), "neutral"),
        }
        return _defaults.get(state, StateDisplayInfo("state_unknown", (128, 128, 128), "neutral"))

    @abstractmethod
    def process_frame(self, landmarks: np.ndarray, timestamp: Optional[float] = None) -> AnalysisResult:
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