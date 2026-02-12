"""
Finite State Machine for repetition counting.

Manages the state machine logic with debouncing to avoid false counts.
Thread-safe design for potential async processing.
"""
import threading
from collections import deque
from enum import Enum
from typing import Tuple, Callable, Optional
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


class HoldPhase(Enum):
    """
    Explicit state enum for static hold exercises.
    
    Provides type safety for state transitions.
    """
    WAITING = "waiting"
    COUNTDOWN = "countdown"
    ACTIVE = "active"
    FINISHED = "finished"


class StaticDurationCounter:
    """
    FSM for static hold exercises (Plank, Wall Sit, etc.).
    Sibling to RepetitionCounter — same design patterns, different domain.
    
    States: WAITING → COUNTDOWN → ACTIVE → FINISHED
    - WAITING: No valid form detected yet
    - COUNTDOWN: Valid form held, waiting for stability_duration to confirm
    - ACTIVE: Timer running, form is being held
    - FINISHED: Form broke during active hold (or exercise complete)
    
    Thread-safe: Uses lock for state access to support potential async processing.
    """
    
    def __init__(self, stability_duration: float = 3.0):
        self.stability_duration = stability_duration
        self._phase = HoldPhase.WAITING
        self.elapsed_seconds: int = 0
        
        # Internal timestamps
        self._hold_start: Optional[float] = None
        self._active_start: Optional[float] = None
        self._elapsed_raw: float = 0.0
        self._countdown_remaining: int = 0
        
        # Thread-safe
        self._lock = threading.Lock()

    @property
    def state(self) -> str:
        """Returns the current state string."""
        return self._phase.value

    @property
    def countdown_remaining(self) -> int:
        """Seconds remaining in countdown (for UI feedback)."""
        return self._countdown_remaining

    def process(self, is_valid: bool, timestamp: float) -> Tuple[int, str]:
        """
        Updates FSM based on form validity.
        
        Args:
            is_valid: Whether the pose/form is currently correct
            timestamp: Current frame timestamp
            
        Returns:
            Tuple of (elapsed_seconds, state_string)
        """
        with self._lock:
            if self._phase == HoldPhase.WAITING:
                if is_valid:
                    self._phase = HoldPhase.COUNTDOWN
                    self._hold_start = timestamp
                    
            elif self._phase == HoldPhase.COUNTDOWN:
                if is_valid:
                    hold_time = timestamp - self._hold_start
                    if hold_time >= self.stability_duration:
                        self._phase = HoldPhase.ACTIVE
                        self._active_start = timestamp
                        self._elapsed_raw = 0.0
                    else:
                        self._countdown_remaining = int(self.stability_duration - hold_time) + 1
                else:
                    # Form broke during countdown → reset
                    self._phase = HoldPhase.WAITING
                    self._hold_start = None
                    self._countdown_remaining = 0
                    
            elif self._phase == HoldPhase.ACTIVE:
                if is_valid:
                    self._elapsed_raw = timestamp - self._active_start
                else:
                    # Form broke during active hold → finished
                    self._phase = HoldPhase.FINISHED
                    
            # FINISHED: no-op (stays finished until reset)
            
            self.elapsed_seconds = int(self._elapsed_raw)
            return self.elapsed_seconds, self.state

    def reset(self) -> None:
        """Reset counter state."""
        with self._lock:
            self._phase = HoldPhase.WAITING
            self.elapsed_seconds = 0
            self._hold_start = None
            self._active_start = None
            self._elapsed_raw = 0.0
            self._countdown_remaining = 0
