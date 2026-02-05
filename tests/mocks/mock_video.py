"""
Mock VideoSource implementation for testing without hardware.

Enables:
- CI/CD testing on GitHub Actions (no webcam required)
- Unit testing of SpotterApp game loop
- Predictable frame sequences for reproducible tests
"""
import numpy as np
from typing import Tuple, List, Optional
from src.core.interfaces import VideoSource


class MockVideoSource(VideoSource):
    """
    VideoSource that returns pre-defined frames for testing.
    
    Usage:
        # Single blank frame
        mock = MockVideoSource()
        
        # Custom frames
        frames = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(10)]
        mock = MockVideoSource(frames=frames, loop=True)
    """
    
    def __init__(self, frames: Optional[List[np.ndarray]] = None, loop: bool = False):
        """
        Args:
            frames: List of BGR frames to return. Defaults to one blank frame.
            loop: If True, restart from beginning when frames are exhausted.
        """
        self.frames = frames if frames is not None else [self._blank_frame()]
        self.loop = loop
        self.index = 0
        
    def _blank_frame(self) -> np.ndarray:
        """Creates a default 640x480 black frame."""
        return np.zeros((480, 640, 3), dtype=np.uint8)
    
    def get_frame(self) -> Tuple[bool, np.ndarray]:
        """
        Returns the next frame in the sequence.
        
        Returns:
            Tuple of (success, frame). Returns (False, empty) when exhausted.
        """
        if self.index >= len(self.frames):
            if self.loop:
                self.index = 0
            else:
                return False, np.array([])
        
        frame = self.frames[self.index]
        self.index += 1
        return True, frame
    
    def release(self) -> None:
        """No-op for mock. Nothing to release."""
        pass
    
    def reset(self) -> None:
        """Resets the frame index to the beginning."""
        self.index = 0
