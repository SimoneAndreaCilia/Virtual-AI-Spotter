import collections
import threading
from typing import Tuple, Optional
import numpy as np

from src.core.interfaces import OutputSink

class DequeOutputSink(OutputSink):
    """
    Thread-safe, non-blocking sink for WebSockets.
    Uses a deque with maxlen to automatically drop the oldest frame when full.
    """
    def __init__(self, maxlen: int = 2):
        # maxlen automatically handles "drop oldest" when appending beyond capacity
        self._deque = collections.deque(maxlen=maxlen)
        self._lock = threading.Lock()
        
    def emit(self, frame: np.ndarray, state_json: str) -> None:
        """
        Thread-safe append. Automatically drops the oldest item if full.
        """
        with self._lock:
            self._deque.append((frame, state_json))
            
    def get_latest(self) -> Optional[Tuple[np.ndarray, str]]:
        """
        Thread-safe popleft. Returns None if empty.
        """
        with self._lock:
            if not self._deque:
                return None
            return self._deque.popleft()
