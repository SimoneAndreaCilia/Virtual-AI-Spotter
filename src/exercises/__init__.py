"""
Exercises Package - Auto-registers all exercises with the factory.

When this package is imported, all exercise modules are loaded,
triggering their @register_exercise decorators.

To add a new exercise:
1. Create the exercise file (e.g., lunges.py)
2. Add @register_exercise("lunges") decorator to the class
3. Import it here
4. Done! The factory will automatically see it.
"""

# Import all exercises to trigger registration
from src.exercises.curl import BicepCurl
from src.exercises.squat import Squat
from src.exercises.pushup import PushUp

# Export for convenience
__all__ = ["BicepCurl", "Squat", "PushUp"]
