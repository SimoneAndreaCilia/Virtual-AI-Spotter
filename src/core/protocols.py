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
