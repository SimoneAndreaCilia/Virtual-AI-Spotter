"""
UIState dataclass - represents the current state of the UI for rendering.

This is passed from SessionManager to Visualizer each frame.
"""
from dataclasses import dataclass, field
from typing import Optional, List
import numpy as np
from src.core.interfaces import StateDisplayInfo


@dataclass
class UIState:
    """State object passed to the UI layer for rendering."""
    exercise_name: str
    reps: int
    target_reps: int
    current_set: int
    target_sets: int
    state: str  # "start", "up", "down"
    feedback_key: str
    workout_state: str  # "EXERCISE", "REST", "FINISHED"
    keypoints: Optional[np.ndarray] = None
    is_time_based: bool = False  # New flag for Timer vs Reps
    state_display: Optional[StateDisplayInfo] = None  # OCP: owned by each Exercise
    is_valid: bool = True
    invalid_joints: List[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serializes the UIState to a dictionary suitable for JSON."""
        return {
            "exercise_name": self.exercise_name,
            "reps": self.reps,
            "target_reps": self.target_reps,
            "current_set": self.current_set,
            "target_sets": self.target_sets,
            "state": self.state,
            "feedback_key": self.feedback_key,
            "workout_state": self.workout_state,
            "is_time_based": self.is_time_based,
            "is_valid": self.is_valid,
            "invalid_joints": self.invalid_joints,
            "keypoints": self.keypoints.tolist() if self.keypoints is not None else None,
            "state_display": {
                "label_key": self.state_display.label_key,
                "color": self.state_display.color,
                "category": self.state_display.category
            } if self.state_display else None
        }
