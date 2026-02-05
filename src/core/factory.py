"""
ExerciseFactory - Creates exercise instances using the Registry Pattern.

The factory uses the registry to look up exercise classes.
Exercises self-register using the @register_exercise decorator.

Adding a new exercise:
1. Create the exercise file (e.g., src/exercises/new_exercise.py)
2. Add @register_exercise("exercise name") decorator to the class
3. Import the exercise in src/exercises/__init__.py
4. Done! No changes needed to this factory.
"""
from typing import Dict, Any
from src.core.interfaces import Exercise
from src.core.registry import get_exercise_class, get_available_exercises

# IMPORTANT: Import exercises package to trigger registration
import src.exercises  # noqa: F401


class ExerciseFactory:
    """
    Factory for creating exercise instances.
    
    Uses the Registry Pattern - exercises register themselves via decorator.
    This class follows the Open/Closed Principle:
    - Open for extension (add new exercises without modifying this file)
    - Closed for modification (no if/elif chains to maintain)
    """
    
    @staticmethod
    def create_exercise(exercise_type: str, config: Dict[str, Any]) -> Exercise:
        """
        Creates an exercise instance by name.
        
        Args:
            exercise_type: Name of the exercise (e.g., "bicep curl", "squat").
            config: Configuration dictionary for the exercise.
            
        Returns:
            An instance of the requested exercise.
            
        Raises:
            ValueError: If the exercise type is not registered.
        """
        exercise_class = get_exercise_class(exercise_type)
        return exercise_class(config)
    
    @staticmethod
    def get_available_exercises():
        """
        Returns a list of all available exercise names.
        
        Returns:
            List of registered exercise names.
        """
        return get_available_exercises()
