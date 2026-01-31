from collections import deque
from typing import Tuple, List, Callable, Dict, Any
from config.settings import HYSTERESIS_TOLERANCE

class RepetitionCounter:
    """
    Gestisce la logica della macchina a stati per contare le ripetizioni.
    Incorpora il debouncing per evitare falsi conteggi dovuti al jitter.
    """
    def __init__(self, up_threshold: float, down_threshold: float, start_stage: str = "start", inverted: bool = False):
        self.up_threshold = up_threshold
        self.down_threshold = down_threshold
        self.state = start_stage
        self.reps = 0
        self.inverted = inverted # Se True: Up è angolo PICCOLO, Down è angolo GRANDE
        
        # Buffer locale per la stabilità del segnale (es. ultimi 5 angoli)
        self.history = deque(maxlen=5) 

    def process(self, angle: float) -> Tuple[int, str]:
        """
        Analizza il nuovo angolo e aggiorna lo stato e le ripetizioni.
        """
        self.history.append(angle)
        
        if not self.inverted:
            # --- STANDARD LOGIC (Squat, PushUp) ---
            # DOWN: Angolo diminuisce (si scende sotto soglia)
            # UP: Angolo aumenta (si sale sopra soglia)
            
            # DOWN TRANSITION
            if angle < self.down_threshold + HYSTERESIS_TOLERANCE:
                if self._is_stable(lambda a: a < self.down_threshold + HYSTERESIS_TOLERANCE):
                    self.state = "down"
                    
            # UP TRANSITION & COUNT
            elif angle > self.up_threshold - HYSTERESIS_TOLERANCE:
                if self._is_stable(lambda a: a > self.up_threshold - HYSTERESIS_TOLERANCE):
                    if self.state == "down":
                        self.reps += 1
                        self.state = "up"
                    elif self.state == "start":
                        self.state = "up"
        
        else:
            # --- INVERTED LOGIC (Bicep Curl) ---
            # DOWN (Estensione): Angolo AUMENTA (si estende braccio > 160)
            # UP (Flessione/Contrazione): Angolo DIMINUISCE (< 30)
            
            # DOWN TRANSITION
            if angle > self.down_threshold - HYSTERESIS_TOLERANCE:
                if self._is_stable(lambda a: a > self.down_threshold - HYSTERESIS_TOLERANCE):
                    self.state = "down"
            
            # UP TRANSITION & COUNT
            elif angle < self.up_threshold + HYSTERESIS_TOLERANCE:
                if self._is_stable(lambda a: a < self.up_threshold + HYSTERESIS_TOLERANCE):
                    if self.state == "down":
                        self.reps += 1
                        self.state = "up"
                    elif self.state == "start":
                        # Se partiamo già piegati? Mmh, di solito si parte distesi (down)
                        self.state = "up"
            
        return self.reps, self.state

    def _is_stable(self, predicate: Callable[[float], bool], frames: int = 2) -> bool:
        """Controlla se la condizione è vera per 'frames' consecutivi."""
        if len(self.history) < frames:
            return False
        return all(predicate(x) for x in list(self.history)[-frames:])
    
    def reset(self):
        self.reps = 0
        self.state = "start"
        self.history.clear()
