import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from src.core.config_types import ExerciseRecord

@dataclass
class Session:
    """
    Represents a workout (or exercise session).
    """
    user_id: str
    start_time: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    end_time: Optional[datetime] = None
    exercises: List[ExerciseRecord] = field(default_factory=list)
    # [NEW] Session goals
    target_sets: int = 3
    target_reps: int = 8
    
    # [NEW] Current state (to update during workout)
    current_set: int = 1
    total_reps: int = 0

    def end_session(self):
        """Ends the session by setting the end time."""
        self.end_time = datetime.now()

    def add_exercise(self, exercise_data: ExerciseRecord):
        """Adds exercise data to the session."""
        self.exercises.append(exercise_data)
