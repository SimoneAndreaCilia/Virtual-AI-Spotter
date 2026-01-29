import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

@dataclass
class Session:
    """
    Rappresenta unallenamento (o sessione di esercizi).
    """
    user_id: str
    start_time: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    end_time: Optional[datetime] = None
    exercises: List[Dict[str, Any]] = field(default_factory=list)
    # [NEW] Obiettivi della sessione
    target_sets: int = 3
    target_reps: int = 8
    
    # [NEW] Stato corrente (da aggiornare durante il workout)
    current_set: int = 1
    total_reps: int = 0

    def end_session(self):
        """Termina la sessione impostando l'orario di fine."""
        self.end_time = datetime.now()

    def add_exercise(self, exercise_data: Dict[str, Any]):
        """Aggiunge i dati di un esercizio svolto alla sessione."""
        self.exercises.append(exercise_data)
