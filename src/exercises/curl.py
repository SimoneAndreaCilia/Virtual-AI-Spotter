import numpy as np
from typing import Dict, Any, List, Tuple
from src.core.interfaces import Exercise, AnalysisResult
from src.utils.geometry import calculate_angle

class BicepCurl(Exercise):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Soglie angolari (configurabili o di default)
        self.up_threshold = config.get("up_angle", 45)     # Braccio piegato
        self.down_threshold = config.get("down_angle", 150) # Braccio disteso
        
        # Lato del corpo da analizzare: 'right' o 'left'
        self.side = config.get("side", "right")

    def process_frame(self, landmarks: np.ndarray) -> AnalysisResult:
        """
        Input: landmarks (Array 17x3 di YOLO: [x, y, conf])
        Output: AnalysisResult
        """
        
        # --- 1. Selezione Keypoint in base al lato ---
        # Mappa keypoint YOLOv8 (COCO format)
        # Left: Spalla=5, Gomito=7, Polso=9
        # Right: Spalla=6, Gomito=8, Polso=10
        if self.side == "left":
            idx_shoulder, idx_elbow, idx_wrist = 5, 7, 9
        else:
            idx_shoulder, idx_elbow, idx_wrist = 6, 8, 10

        # Estraiamo coordinate (x, y) ignorando la confidence per ora
        shoulder = landmarks[idx_shoulder][:2]
        elbow = landmarks[idx_elbow][:2]
        wrist = landmarks[idx_wrist][:2]

        # Check confidenza: se YOLO non è sicuro, non calcoliamo nulla
        conf_shoulder = landmarks[idx_shoulder][2]
        conf_elbow = landmarks[idx_elbow][2]
        conf_wrist = landmarks[idx_wrist][2]
        
        if min(conf_shoulder, conf_elbow, conf_wrist) < 0.5:
             return AnalysisResult(
                reps=self.reps,
                stage="unknown",
                correction="Corpo non visibile",
                angle=0.0,
                is_valid=False
            )

        # --- 2. Calcolo Geometrico ---
        angle = calculate_angle(shoulder, elbow, wrist)

        # --- 3. Macchina a Stati (FSM) ---
        correction_feedback = "Good Form"
        is_valid = True

        # LOGICA DI CONTEGGIO
        if angle > self.down_threshold:
            self.stage = "down"
            
        if angle < self.up_threshold and self.stage == "down":
            self.stage = "up"
            self.reps += 1
            # Qui potremmo aggiungere logica per resettare errori se necessario

        # LOGICA DI CORREZIONE (Esempio semplice)
        # Se nello stato UP l'angolo è ancora troppo aperto (> 90), non sta chiudendo bene
        if self.stage == "up" and angle > 90:
            correction_feedback = "Chiudi di piu il braccio!"
            is_valid = False

        return AnalysisResult(
            reps=self.reps,
            stage=self.stage,
            correction=correction_feedback,
            angle=angle,
            is_valid=is_valid
        )

    def reset(self):
        self.reps = 0
        self.stage = "start"