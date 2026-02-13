"""
Mixins for exercise specializations.

RepBasedMixin: Provides bilateral side-selection and debounce utilities
for rep-based exercises (Curl, Squat, PushUp).

Separated from the Exercise ABC to respect ISP — time-based exercises
like Plank don't need these capabilities.
"""


class RepBasedMixin:
    """
    Mixin for rep-based exercises (Curl, Squat, PushUp).
    
    Provides:
    - _get_sides_to_process(): Bilateral side-selection logic
    - _is_stable_change(): Debounce utility for rep transitions
    """

    def _get_sides_to_process(self) -> list:
        """
        Returns list of sides to analyze based on self.side config.
        
        Returns:
            ["left"], ["right"], or ["left", "right"] for "both"
        """
        side = getattr(self, 'side', 'right')
        if side == "both":
            return ["left", "right"]
        return [side]

    def _is_stable_change(self, predicate, consistency_frames: int = 3) -> bool:
        """
        Checks if a condition (predicate) has been true for the last N frames.
        Useful for debouncing (avoiding state changes on spurious frames).
        
        Args:
            predicate: Function that accepts an item from history and returns bool.
            consistency_frames: Number of consecutive frames required.
            
        Returns:
            bool: True if the condition is stable.
        """
        if len(self.history) < consistency_frames:
            return False
            
        # Check the last N elements of history
        recent_history = list(self.history)[-consistency_frames:]
        
        return all(predicate(item) for item in recent_history)
