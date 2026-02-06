from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Tuple, NamedTuple
from collections import deque
import numpy as np
from src.utils.geometry import calculate_angle


# Memory-efficient history entry (replaces per-frame dict allocation)
class HistoryEntry(NamedTuple):
    angle: float
    stage: str
    reps: int
    is_valid: bool

# Extended entry for PushUp (includes body_angle)
class PushUpHistoryEntry(NamedTuple):
    angle: float
    body_angle: float
    stage: str
    reps: int
    is_valid: bool

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
        # [NEW] Buffer circolare per analizzare la storia recente (es. ultimi 30 frame ~ 1 sec)
        self.history = deque(maxlen=30)
        # [NEW] Dizionario dei filtri per i keypoint (Idx -> PointSmoother)
        self.smoothers: Dict[int, Any] = {}
        
        # [NEW] Chiave per localizzazione nome esercizio (OCP)
        self.display_name_key: str = ""

    def smooth_landmarks(self, landmarks: np.ndarray, timestamp: float = None) -> np.ndarray:
        """
        Applica lo smoothing ai keypoint registrati in self.smoothers.
        Restituisce una copia dei landmarks con le coordinate (x,y) filtrate.
        """
        smoothed = landmarks.copy()
        
        for idx, smoother in self.smoothers.items():
            try:
                raw_pt = (landmarks[idx][0], landmarks[idx][1])
                smooth_pt = smoother(raw_pt, t=timestamp)
                smoothed[idx][0] = smooth_pt[0]
                smoothed[idx][1] = smooth_pt[1]
            except IndexError:
                # Smoother index out of range - skip this keypoint
                continue
                
        return smoothed

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

    def _calculate_side_angle(
        self,
        landmarks: np.ndarray,
        smoothed: np.ndarray,
        indices: tuple,
        confidence_threshold: float
    ) -> float:
        """
        Calculates angle for a set of 3 keypoints if confidence is sufficient.
        
        Args:
            landmarks: Original landmarks with confidence values
            smoothed: Smoothed landmarks for coordinates
            indices: Tuple of (idx1, idx2, idx3) where idx2 is the vertex
            confidence_threshold: Minimum confidence required
            
        Returns:
            Calculated angle in degrees, or None if confidence too low
        """
        idx1, idx2, idx3 = indices
        
        # Check if all keypoints have sufficient confidence
        if min(landmarks[idx1][2], landmarks[idx2][2], landmarks[idx3][2]) >= confidence_threshold:
            return calculate_angle(
                smoothed[idx1][:2],
                smoothed[idx2][:2],
                smoothed[idx3][:2]
            )
        return None

    def _is_stable_change(self, predicate, consistency_frames: int = 3) -> bool:
        """
        Verifica se una condizione (predicate) è stata vera per gli ultimi N frame.
        Utile per debouncing (evitare cambi di stato su singoli frame spuri).
        
        Args:
            predicate: Funzione che accetta un item della history e restituisce bool.
            consistency_frames: Numero di frame consecutivi richiesti.
            
        Returns:
            bool: True se la condizione è stabile.
        """
        if len(self.history) < consistency_frames:
            return False
            
        # Controlliamo gli ultimi N elementi della storia
        # History è una deque, quindi iteriamo gli ultimi N
        recent_history = list(self.history)[-consistency_frames:]
        
        return all(predicate(item) for item in recent_history)

    @abstractmethod
    def process_frame(self, landmarks: np.ndarray, timestamp: float = None) -> AnalysisResult:
        """
        Prende i keypoint (scheletro) e restituisce il risultato dell'analisi.
        Opzionale: timestamp per gestire video preregistrati o lag.
        """
        pass

    def reset(self):
        """
        Resetta il conteggio, lo stato, la storia e i filtri.
        Le classi figlie possono fare override ma dovrebbero chiamare super().reset()
        """
        self.reps = 0
        self.stage = "start"
        self.history.clear()
        for s in self.smoothers.values():
            s.reset()

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