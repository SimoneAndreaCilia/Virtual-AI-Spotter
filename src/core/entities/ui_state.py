"""
UIState dataclass - represents the current state of the UI for rendering.

This is passed from SessionManager to Visualizer each frame.
"""
from dataclasses import dataclass
from typing import Any


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
    keypoints: Any = None
