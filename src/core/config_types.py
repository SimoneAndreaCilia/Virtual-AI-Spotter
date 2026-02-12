"""
Typed configuration dictionaries for the Virtual AI Spotter application.

Replaces Dict[str, Any] with TypedDict for compile-time type safety.
"""
from typing import TypedDict


class ExerciseConfig(TypedDict, total=False):
    """
    Config passed to Exercise constructors. All keys are optional (have defaults).
    
    Each exercise uses a subset of these keys:
    - Curl/Squat/PushUp: side, up_angle, down_angle
    - PushUp: form_angle_min
    - Plank: stability_duration
    """
    side: str                    # "left", "right", "both"
    up_angle: float              # Angle threshold for UP state
    down_angle: float            # Angle threshold for DOWN state
    form_angle_min: float        # Min body angle for form check (PushUp)
    stability_duration: float    # Hold duration before active (Plank)


class AppConfig(TypedDict):
    """Top-level config from CLI, passed to SpotterApp."""
    language: str                # "IT" or "EN"
    exercise_name: str           # "Bicep Curl", "Squat", etc.
    exercise_config: ExerciseConfig
    target_sets: int
    target_reps: int
    camera_id: int


class ExerciseRecord(TypedDict):
    """Record of a completed exercise within a session."""
    exercise_name: str
    reps: int
    sets: int
    duration: float
