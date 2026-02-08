"""
Finite State Machine for repetition counting.

Manages the state machine logic with debouncing to avoid false counts.
Thread-safe design for potential async processing.
"""
import threading
from collections import deque
from enum import Enum
from typing import Tuple, Callable
from config.settings import HYSTERESIS_TOLERANCE, FSM_STABILITY_FRAMES


class RepPhase(Enum):
    """
    Explicit state enum for FSM phases.
    
    Provides type safety for state transitions.
    """
    START = "start"
    UP = "up"
    DOWN = "down"
    UNKNOWN = "unknown"


class RepetitionCounter:
    """
    Manages the logic of the state machine to count repetitions.
    Incorporates debouncing to avoid false counts due to jitter.
    
    Thread-safe: Uses lock for history access to support potential async processing.
    """
    
    def __init__(
        self, 
        up_threshold: float, 
        down_threshold: float, 
        start_stage: str = "start", 
        inverted: bool = False, 
        state_prefix: str = "",
        stability_frames: int = FSM_STABILITY_FRAMES
    ):
        self.up_threshold = up_threshold
        self.down_threshold = down_threshold
        self.state_prefix = state_prefix
        self.inverted = inverted  # If True: Up = SMALL angle, Down = LARGE angle
        self.stability_frames = stability_frames
        
        # Internal state uses enum for type safety
        self._phase = self._parse_phase(start_stage)
        self.reps = 0
        
        # Thread-safe history buffer
        self._lock = threading.Lock()
        self._history: deque = deque(maxlen=5)
    
    def _parse_phase(self, state_str: str) -> RepPhase:
        """Convert string to RepPhase enum."""
        try:
            return RepPhase(state_str)
        except ValueError:
            return RepPhase.UNKNOWN
    
    @property
    def state(self) -> str:
        """Returns prefixed state string for backward compatibility."""
        return self._prefixed(self._phase.value)
    
    def _prefixed(self, state: str) -> str:
        """Returns prefixed state name, e.g., 'squat_up' from 'up'."""
        if self.state_prefix and state not in (RepPhase.START.value, RepPhase.UNKNOWN.value):
            return f"{self.state_prefix}_{state}"
        return state

    def process(self, angle: float) -> Tuple[int, str]:
        """
        Analyzes the new angle and updates the state and reps.
        
        Returns:
            Tuple of (reps_count, state_string)
        """
        with self._lock:
            self._history.append(angle)
        
        if not self.inverted:
            # --- STANDARD LOGIC (Squat, PushUp) ---
            # DOWN: Angle decreases (goes below threshold)
            # UP: Angle increases (goes above threshold)
            
            # DOWN TRANSITION
            if angle < self.down_threshold + HYSTERESIS_TOLERANCE:
                if self._is_stable(lambda a: a < self.down_threshold + HYSTERESIS_TOLERANCE):
                    self._phase = RepPhase.DOWN
                    
            # UP TRANSITION & COUNT
            elif angle > self.up_threshold - HYSTERESIS_TOLERANCE:
                if self._is_stable(lambda a: a > self.up_threshold - HYSTERESIS_TOLERANCE):
                    if self._phase == RepPhase.DOWN:
                        self.reps += 1
                        self._phase = RepPhase.UP
                    elif self._phase == RepPhase.START:
                        self._phase = RepPhase.UP
        
        else:
            # --- INVERTED LOGIC (Bicep Curl) ---
            # DOWN (Extension): Angle INCREASES (extends arm > 160)
            # UP (Flexion/Contraction): Angle DECREASES (< 30)
            
            # DOWN TRANSITION
            if angle > self.down_threshold - HYSTERESIS_TOLERANCE:
                if self._is_stable(lambda a: a > self.down_threshold - HYSTERESIS_TOLERANCE):
                    self._phase = RepPhase.DOWN
            
            # UP TRANSITION & COUNT
            elif angle < self.up_threshold + HYSTERESIS_TOLERANCE:
                if self._is_stable(lambda a: a < self.up_threshold + HYSTERESIS_TOLERANCE):
                    if self._phase == RepPhase.DOWN:
                        self.reps += 1
                        self._phase = RepPhase.UP
                    elif self._phase == RepPhase.START:
                        self._phase = RepPhase.UP
            
        return self.reps, self.state

    def _is_stable(self, predicate: Callable[[float], bool]) -> bool:
        """Checks if a condition is true for 'stability_frames' consecutive frames."""
        with self._lock:
            if len(self._history) < self.stability_frames:
                return False
            return all(predicate(x) for x in list(self._history)[-self.stability_frames:])
    
    def reset(self) -> None:
        """Reset counter state."""
        self.reps = 0
        self._phase = RepPhase.START
        with self._lock:
            self._history.clear()
