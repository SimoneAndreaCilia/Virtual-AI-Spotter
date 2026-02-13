"""
UIState dataclass - represents the current state of the UI for rendering.

This is passed from SessionManager to Visualizer each frame.
"""
from dataclasses import dataclass
from typing import Optional
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

