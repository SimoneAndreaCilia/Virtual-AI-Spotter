"""
Custom exception hierarchy for Virtual AI Spotter.

Provides semantic error types instead of generic Python exceptions,
enabling cleaner try/except blocks and more expressive error handling.
"""


class SpotterError(Exception):
    """Base exception for Virtual AI Spotter."""


class VideoSourceError(SpotterError):
    """Camera/video source failed to open or read."""


class ModelLoadError(SpotterError):
    """AI model could not be loaded."""


class ExerciseNotFoundError(SpotterError):
    """Requested exercise is not registered."""
