from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Tuple
import numpy as np

# Definizione del contratto per i risultati dell'analisi
@dataclass
class AnalysisResult:
    reps: int
    stage: str  # "up", "down", "start"
    correction: str  # Feedback es. "Schiena dritta!"
    angle: float     # Angolo corrente
    is_valid: bool   # Se la forma è corretta

class Exercise(ABC):
    """
    Classe Astratta Base (Interface).
    Ogni nuovo esercizio (Squat, Curl, PushUp) DEVE ereditare da questa classe
    e implementare questi metodi.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.reps = 0
        self.stage = "start"

    @abstractmethod
    def process_frame(self, landmarks: np.ndarray) -> AnalysisResult:
        """
        Prende i keypoint (scheletro) e restituisce il risultato dell'analisi.
        """
        pass

    @abstractmethod
    def reset(self):
        """Resetta il conteggio."""
        pass

class VideoSource(ABC):
    """
    Interfaccia per la sorgente video.
    Permette di scambiare Webcam con File Video senza rompere il codice.
    """
    
    @abstractmethod
    def get_frame(self) -> Tuple[bool, np.ndarray]:
        """Restituisce (ret, frame) come OpenCV."""
        pass

    @abstractmethod
    def release(self):
        pass