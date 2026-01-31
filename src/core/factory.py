from typing import Dict, Any
from src.core.interfaces import Exercise
from src.exercises.curl import BicepCurl
from src.exercises.squat import Squat
from src.exercises.pushup import PushUp

class ExerciseFactory:
    @staticmethod
    def create_exercise(exercise_type: str, config: Dict[str, Any]) -> Exercise:
        exercise_type = exercise_type.lower()
        
        if exercise_type == "bicep curl":
            return BicepCurl(config)
        elif exercise_type == "squat":
            return Squat(config)
        elif exercise_type == "pushup":
             return PushUp(config)
        
        raise ValueError(f"Esercizio '{exercise_type}' non supportato.")
