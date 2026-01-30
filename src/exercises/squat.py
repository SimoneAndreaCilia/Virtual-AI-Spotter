import numpy as np
from typing import Dict, Any
from src.core.interfaces import Exercise, AnalysisResult
from src.utils.geometry import calculate_angle
from src.utils.smoothing import PointSmoother
from config.settings import SQUAT_THRESHOLDS, CONFIDENCE_THRESHOLD

class Squat(Exercise):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.up_threshold = config.get("up_angle", SQUAT_THRESHOLDS["UP_ANGLE"])
        self.down_threshold = config.get("down_angle", SQUAT_THRESHOLDS["DOWN_ANGLE"])
        
        # Lato del corpo da analizzare: 'right' (default) o 'left'
        # Per lo squat spesso si guarda di lato, quindi ha senso scegliere un lato.
        self.side = config.get("side", "right")

        # [NEW] Smoother per i keypoint critici (Anche, Ginocchia, Caviglie)
        self.smoothers = {
            11: PointSmoother(min_cutoff=0.1, beta=0.05), # L Hip
            13: PointSmoother(min_cutoff=0.1, beta=0.05), # L Knee
            15: PointSmoother(min_cutoff=0.1, beta=0.05), # L Ankle
            12: PointSmoother(min_cutoff=0.1, beta=0.05), # R Hip
            14: PointSmoother(min_cutoff=0.1, beta=0.05), # R Knee
            16: PointSmoother(min_cutoff=0.1, beta=0.05), # R Ankle
        }

    def process_frame(self, landmarks: np.ndarray, timestamp: float = None) -> AnalysisResult:
        """
        Input: landmarks (Array 17x3 di YOLO: [x, y, conf])
        Output: AnalysisResult
        """
        
        # --- 1. Smoothing & Selezione Keypoint ---
        smoothed_landmarks = self.smooth_landmarks(landmarks, timestamp)

        # Mappa keypoint YOLOv8 (COCO format)
        idx_hip_l, idx_knee_l, idx_ankle_l = 11, 13, 15
        idx_hip_r, idx_knee_r, idx_ankle_r = 12, 14, 16
        
        # Determine target sides
        sides_to_process = []
        if self.side == "left" or self.side == "both":
            sides_to_process.append("left")
        if self.side == "right" or self.side == "both":
            sides_to_process.append("right")
            
        valid_angles = []
        
        # --- Process Left ---
        if "left" in sides_to_process:
             # Usiamo confidence originale
             if min(landmarks[idx_hip_l][2], landmarks[idx_knee_l][2], landmarks[idx_ankle_l][2]) >= CONFIDENCE_THRESHOLD:
                # Usiamo smoothed coords
                angle_l = calculate_angle(smoothed_landmarks[idx_hip_l][:2], 
                                          smoothed_landmarks[idx_knee_l][:2], 
                                          smoothed_landmarks[idx_ankle_l][:2])
                valid_angles.append(angle_l)

        # --- Process Right ---
        if "right" in sides_to_process:
             if min(landmarks[idx_hip_r][2], landmarks[idx_knee_r][2], landmarks[idx_ankle_r][2]) >= CONFIDENCE_THRESHOLD:
                angle_r = calculate_angle(smoothed_landmarks[idx_hip_r][:2], 
                                          smoothed_landmarks[idx_knee_r][:2], 
                                          smoothed_landmarks[idx_ankle_r][:2])
                valid_angles.append(angle_r)

        # Se non abbiamo angoli validi (per i lati richiesti)
        if len(valid_angles) < len(sides_to_process):
             return AnalysisResult(
                reps=self.reps,
                stage="unknown",
                correction="err_body_not_visible",
                angle=0.0,
                is_valid=False
            )

        # --- 2. Calcolo Geometrico (Media) ---
        angle = np.mean(valid_angles)

        # --- 3. Macchina a Stati (FSM) ---
        correction_feedback = "squat_perfect_form"
        is_valid = True

        # LOGICA DI CONTEGGIO SQUAT
        # DOWN: Angolo diminuisce (si scende) -> verso 90 gradi
        # UP: Angolo aumenta (si sale) -> verso 160+ gradi
        
        # LOGICA DI CONTEGGIO SQUAT
        # DOWN: Angolo diminuisce (si scende) -> verso 90 gradi
        # UP: Angolo aumenta (si sale) -> verso 160+ gradi
        
        # DOWN TRANSITION
        if angle < self.down_threshold: # Sei sceso sotto i 90
            # Debounce: conferma discesa solo se stabile
            if self._is_stable_change(lambda x: x["angle"] < self.down_threshold + 5, consistency_frames=2):
                self.stage = "squat_down"
            
        # UP TRANSITION
        if angle > self.up_threshold and self.stage == "squat_down":
            # Debounce: conferma risalita
            if self._is_stable_change(lambda x: x["angle"] > self.up_threshold - 5, consistency_frames=2):
                self.stage = "squat_up"
                self.reps += 1
            
        # LOGICA DI CORREZIONE
        
        # [NEW] Aggiornamento Storia
        self.history.append({
            "angle": angle,
            "stage": self.stage,
            "reps": self.reps,
            "is_valid": is_valid
        })

        return AnalysisResult(
            reps=self.reps,
            stage=self.stage,
            correction=correction_feedback,
            angle=angle,
            is_valid=is_valid
        )

    def reset(self):
        super().reset()
