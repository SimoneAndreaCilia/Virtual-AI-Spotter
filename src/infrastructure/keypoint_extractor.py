"""
Keypoint Extractor implementations for different pose detection backends.

Follows the KeypointExtractor protocol defined in protocols.py.
"""
from typing import Any, Tuple, Optional
import numpy as np


class YoloKeypointExtractor:
    """
    Extracts keypoints from YOLO pose detection results.
    
    YOLO returns results with format:
    - results[0].keypoints.data: Tensor of shape (N, 17, 3) where N is num persons
    - Each keypoint has (x, y, confidence)
    """
    
    def extract(self, pose_data: Any) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Extracts keypoints from YOLO pose detection results.
        
        Args:
            pose_data: Raw YOLO detection results
            
        Returns:
            Tuple of (has_person, keypoints):
            - has_person: True if at least one person was detected
            - keypoints: 17x3 numpy array for first detected person, or None
        """
        # Guard: No data
        if not pose_data:
            return False, None
            
        # Guard: No keypoints attribute
        if not hasattr(pose_data[0], 'keypoints'):
            return False, None
            
        # Guard: Keypoints is None
        if pose_data[0].keypoints is None:
            return False, None
            
        # Guard: No detected persons
        if pose_data[0].keypoints.data.shape[0] == 0:
            return False, None
        
        # Extract keypoints for first person (17x3 array)
        keypoints = pose_data[0].keypoints.data[0].cpu().numpy()
        return True, keypoints
