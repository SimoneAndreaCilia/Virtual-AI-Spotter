from typing import List, Tuple, Callable, Any, Dict
import bisect

class FeedbackSystem:
    """
    Centralized system for managing corrective feedback.
    Allows registering rules and getting the highest priority message.
    """
    def __init__(self):
        # List of tuples: (priority, condition_func, message_key)
        # Higher priority wins (e.g., 10 > 1)
        # Stored in ascending order, iterated in reverse for highest-first
        self.rules: List[Tuple[int, Callable[[Dict[str, Any]], bool], str]] = []

    def add_rule(self, 
                 condition: Callable[[Dict[str, Any]], bool], 
                 message_key: str, 
                 priority: int = 1):
        """
        Adds a feedback rule.
        
        Args:
            condition: Function that accepts a 'context' (dict) and returns True if there's an error.
            message_key: Key of the message to display if the condition is true.
            priority: Importance of the error (10=critical, 1=info).
        """
        # Use bisect.insort for O(n) insertion instead of O(n log n) sort
        # Note: bisect sorts ascending, so we iterate in reverse in check()
        bisect.insort(self.rules, (priority, condition, message_key))

    def check(self, context: Dict[str, Any]) -> Tuple[str, bool]:
        """
        Checks all rules against the provided context.
        
        Returns:
            Tuple[str, bool]: (message_key, is_valid_form)
            is_valid_form is False if at least one rule with priority > 0 is triggered.
        """
        # Iterate in reverse to check highest priority rules first
        for priority, condition, msg_key in reversed(self.rules):
            if condition(context):
                # Condition is true (there's an issue/state to report)
                # Return immediately the highest priority message
                # If priority > 0, consider form invalid (or warning)
                is_valid = False  # Assume if there's feedback, there's something to say
                
                # Exception: "Positive" messages (e.g., Perfect Form) may have low priority
                # But here we assume add_rule is used for ERRORS or WARNINGS.
                # For "Good" status messages, we use a default if loop finishes.
                
                return msg_key, False
        
        # No rules triggered -> Default positive feedback
        return "feedback_perfect", True
        
    def reset(self):
        pass # Stateless for now
