"""
WorkoutState enum - type-safe workout states.
"""
from enum import Enum


class WorkoutState(Enum):
    """Possible states of a workout session."""
    EXERCISE = "EXERCISE"  # Active exercise phase
    REST = "REST"          # Rest between sets
    FINISHED = "FINISHED"  # Workout complete
