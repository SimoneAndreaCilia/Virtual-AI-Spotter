"""
Test Helpers - Shared fixtures and utilities for tests.

Provides factory functions for creating dummy frames, keypoints, and UI states.
"""
import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class UIState:
    """Minimal UIState for testing Visualizer."""
    exercise_name: str = "Test Exercise"
    reps: int = 0
    target_reps: int = 8
    current_set: int = 1
    target_sets: int = 3
    state: str = "start"
    feedback_key: str = ""
    workout_state: str = "ACTIVE"  # ACTIVE, REST, FINISHED
    keypoints: Optional[np.ndarray] = None


def create_dummy_frame(width: int = 640, height: int = 480) -> np.ndarray:
    """
    Creates a dummy BGR frame (3-channel numpy array) for testing.
    
    Args:
        width: Frame width in pixels
        height: Frame height in pixels
        
    Returns:
        np.ndarray of shape (height, width, 3) with dtype uint8
    """
    return np.zeros((height, width, 3), dtype=np.uint8)


def create_mock_keypoints(num_points: int = 17, with_confidence: bool = True) -> np.ndarray:
    """
    Creates mock keypoints for testing skeleton rendering.
    
    Args:
        num_points: Number of keypoints (default 17 for COCO format)
        with_confidence: If True, returns (x, y, conf), else (x, y)
        
    Returns:
        np.ndarray of shape (num_points, 3) or (num_points, 2)
    """
    if with_confidence:
        # Create random keypoints with x, y in [100, 500] range and confidence ~0.9
        keypoints = np.random.rand(num_points, 3)
        keypoints[:, 0] = keypoints[:, 0] * 400 + 100  # x: 100-500
        keypoints[:, 1] = keypoints[:, 1] * 300 + 100  # y: 100-400
        keypoints[:, 2] = 0.9  # High confidence
    else:
        keypoints = np.random.rand(num_points, 2)
        keypoints[:, 0] = keypoints[:, 0] * 400 + 100
        keypoints[:, 1] = keypoints[:, 1] * 300 + 100
    
    return keypoints


def create_ui_state(**kwargs) -> UIState:
    """
    Creates a UIState with optional overrides.
    
    Args:
        **kwargs: Override default UIState fields
        
    Returns:
        UIState instance
    """
    return UIState(**kwargs)
