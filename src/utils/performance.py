"""
Performance utilities for monitoring and optimization.
"""
import time
from collections import deque
from typing import Optional


class FPSCounter:
    """
    Rolling average FPS calculator.
    
    Uses a sliding window of timestamps to calculate smooth FPS
    without sudden spikes or drops.
    """
    
    def __init__(self, window_size: int = 30) -> None:
        """
        Initialize FPS counter.
        
        Args:
            window_size: Number of frames to average over (default 30 = ~1 sec at 30fps)
        """
        self.times: deque = deque(maxlen=window_size)
    
    def tick(self) -> float:
        """
        Record a frame timestamp and calculate current FPS.
        
        Call this once per frame in the main loop.
        
        Returns:
            float: Current FPS (rolling average)
        """
        now = time.perf_counter()
        self.times.append(now)
        
        if len(self.times) < 2:
            return 0.0
        
        # FPS = frames / time_elapsed
        elapsed = self.times[-1] - self.times[0]
        if elapsed <= 0:
            return 0.0
            
        return (len(self.times) - 1) / elapsed
    
    def reset(self) -> None:
        """Clear all recorded timestamps."""
        self.times.clear()
    
    def get_frame_time_ms(self) -> float:
        """
        Get average frame time in milliseconds.
        
        Returns:
            float: Average ms per frame
        """
        fps = self.tick()
        if fps <= 0:
            return 0.0
        return 1000.0 / fps
