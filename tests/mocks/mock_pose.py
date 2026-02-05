"""
Mock PoseEstimator implementation for testing without AI model.

Enables:
- CI/CD testing without YOLO model weights
- Unit testing without GPU requirements
- Predictable pose data for reproducible tests
"""
import numpy as np
from typing import Any, List, Optional


class MockPoseEstimator:
    """
    PoseEstimator that returns pre-defined pose data for testing.
    
    Implements the PoseDetector protocol without loading a real model.
    
    Usage:
        # Returns None for all predictions
        mock = MockPoseEstimator()
        
        # Custom pose sequence
        poses = [mock_pose_result_1, mock_pose_result_2]
        mock = MockPoseEstimator(pose_data=poses, loop=True)
    """
    
    def __init__(self, pose_data: Optional[List[Any]] = None, loop: bool = False):
        """
        Args:
            pose_data: List of pose results to return. Defaults to [None].
            loop: If True, restart from beginning when data is exhausted.
        """
        self.pose_data = pose_data if pose_data is not None else [None]
        self.loop = loop
        self.index = 0
    
    def predict(self, frame: np.ndarray) -> Any:
        """
        Returns the next pose data in the sequence.
        
        Args:
            frame: Ignored in mock. Accepts any numpy array.
            
        Returns:
            Pre-defined pose result, or None when exhausted.
        """
        if self.index >= len(self.pose_data):
            if self.loop:
                self.index = 0
            else:
                return None
        
        result = self.pose_data[self.index]
        self.index += 1
        return result
    
    def reset(self) -> None:
        """Resets the pose data index to the beginning."""
        self.index = 0
