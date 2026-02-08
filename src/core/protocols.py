"""
Protocol/Interface definitions for Dependency Injection.

Separates abstractions from implementations, enabling:
- Easy testing with mocks (CI/CD without hardware)
- Swappable AI models
- Following Dependency Inversion Principle (SOLID)
"""
from typing import Protocol, Any, Tuple, Optional, runtime_checkable
import numpy as np


@runtime_checkable
class PoseDetector(Protocol):
    """
    Interface for AI pose detection.
    
    Implementations:
    - PoseEstimator (real YOLO model)
    - MockPoseEstimator (for testing)
    """
    
    def predict(self, frame: np.ndarray) -> Any:
        """
        Runs inference on a frame.
        
        Args:
            frame: BGR image as numpy array (H, W, 3)
            
        Returns:
            Pose detection results (format depends on implementation)
        """
        ...


@runtime_checkable
class DatabaseManagerProtocol(Protocol):
    """
    Interface for database operations.
    
    Implementations:
    - DatabaseManager (SQLite)
    - MockDatabaseManager (for testing)
    """
    
    def get_user(self, user_id: Optional[str] = None) -> Any:
        """Retrieves a user by ID, or the most recent if ID is None."""
        ...
    
    def create_default_user(self) -> Any:
        """Creates and saves a default user."""
        ...
    
    def save_session(self, session: Any) -> None:
        """Saves a training session to the database."""
        ...


@runtime_checkable
class KeypointExtractor(Protocol):
    """
    Protocol for extracting standardized keypoints from pose detection results.
    
    Implementations:
    - YoloKeypointExtractor (for YOLO models)
    - Future: MediaPipeKeypointExtractor, etc.
    """
    
    def extract(self, pose_data: Any) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Extracts keypoints from raw pose detection results.
        
        Args:
            pose_data: Raw output from pose detector
            
        Returns:
            Tuple of (has_person, keypoints):
            - has_person: True if a person was detected
            - keypoints: 17x3 numpy array (x, y, confidence) or None
        """
        ...


@runtime_checkable
class GestureHandlerProtocol(Protocol):
    """
    Protocol for gesture handling.
    
    Implementations:
    - GestureHandler (real implementation)
    - Mock for testing
    """
    
    def process(self, keypoints: Optional[np.ndarray], current_state: str) -> Optional[str]:
        """
        Detect gesture and return corresponding action if applicable.
        
        Args:
            keypoints: Pose keypoints or None
            current_state: Current workout state
            
        Returns:
            Action string or None
        """
        ...
    
    def reset(self) -> None:
        """Clear gesture history."""
        ...
