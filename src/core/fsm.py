from collections import deque
from typing import Tuple, List, Callable, Dict, Any
from config.settings import HYSTERESIS_TOLERANCE

class RepetitionCounter:
    """
    Manages the logic of the state machine to count repetitions.
    Incorporates debouncing to avoid false counts due to jitter.
    """
    def __init__(self, up_threshold: float, down_threshold: float, start_stage: str = "start", inverted: bool = False, state_prefix: str = ""):
        self.up_threshold = up_threshold
        self.down_threshold = down_threshold
        self.state_prefix = state_prefix
        self.state = self._prefixed(start_stage)
        self.reps = 0
        self.inverted = inverted  # If True: Up = SMALL angle, Down = LARGE angle
        
        # Local buffer for signal stability (e.g., last 5 angles)
        self.history = deque(maxlen=5)
    
    def _prefixed(self, state: str) -> str:
        """Returns prefixed state name, e.g., 'squat_up' from 'up'."""
        if self.state_prefix and state not in ("start", "unknown"):
            return f"{self.state_prefix}_{state}"
        return state 

    def process(self, angle: float) -> Tuple[int, str]:
        """
        Analyzes the new angle and updates the state and reps.
        """
        self.history.append(angle)
        
        if not self.inverted:
            # --- STANDARD LOGIC (Squat, PushUp) ---
            # DOWN: Angle decreases (goes below threshold)
            # UP: Angle increases (goes above threshold)
            
            # DOWN TRANSITION
            if angle < self.down_threshold + HYSTERESIS_TOLERANCE:
                if self._is_stable(lambda a: a < self.down_threshold + HYSTERESIS_TOLERANCE):
                    self.state = self._prefixed("down")
                    
            # UP TRANSITION & COUNT
            elif angle > self.up_threshold - HYSTERESIS_TOLERANCE:
                if self._is_stable(lambda a: a > self.up_threshold - HYSTERESIS_TOLERANCE):
                    if self.state.endswith("down"):
                        self.reps += 1
                        self.state = self._prefixed("up")
                    elif self.state == "start":
                        self.state = self._prefixed("up")
        
        else:
            # --- INVERTED LOGIC (Bicep Curl) ---
            # DOWN (Extension): Angle INCREASES (extends arm > 160)
            # UP (Flexion/Contraction): Angle DECREASES (< 30)
            
            # DOWN TRANSITION
            if angle > self.down_threshold - HYSTERESIS_TOLERANCE:
                if self._is_stable(lambda a: a > self.down_threshold - HYSTERESIS_TOLERANCE):
                    self.state = self._prefixed("down")
            
            # UP TRANSITION & COUNT
            elif angle < self.up_threshold + HYSTERESIS_TOLERANCE:
                if self._is_stable(lambda a: a < self.up_threshold + HYSTERESIS_TOLERANCE):
                    if self.state.endswith("down"):
                        self.reps += 1
                        self.state = self._prefixed("up")
                    elif self.state == "start":
                        # If we start already bent? Usually we start extended (down)
                        self.state = self._prefixed("up")
            
        return self.reps, self.state

    def _is_stable(self, predicate: Callable[[float], bool], frames: int = 2) -> bool:
        """Checks if a condition is true for 'frames' consecutive frames."""
        if len(self.history) < frames:
            return False
        return all(predicate(x) for x in list(self.history)[-frames:])
    
    def reset(self) -> None:
        self.reps = 0
        self.state = "start"
        self.history.clear()
