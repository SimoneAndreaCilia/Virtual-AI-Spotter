import numpy as np
from typing import Dict, Any, Tuple
from src.core.interfaces import Exercise, AnalysisResult
from src.utils.geometry import calculate_angle
from src.utils.smoothing import PointSmoother
from config.settings import CURL_THRESHOLDS, CONFIDENCE_THRESHOLD

class BicepCurl(Exercise):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Soglie angolari (configurabili o di default da settings)
        self.up_threshold = config.get("up_angle", CURL_THRESHOLDS["UP_ANGLE"])
        self.down_threshold = config.get("down_angle", CURL_THRESHOLDS["DOWN_ANGLE"])
        self.display_name_key = "curl_name"
        
        # Lato del corpo da analizzare: 'right' o 'left'
        self.side = config.get("side", "right")

        # [NEW] Smoother per i keypoint critici (Spalla, Gomito, Polso per entrambi i lati)
        # 0.005 beta e 1.0 min_cutoff sono valori empirici per buon smoothing con poco lag
        self.smoothers = {
            5: PointSmoother(min_cutoff=0.1, beta=0.05), # L Shoulder
            7: PointSmoother(min_cutoff=0.1, beta=0.05), # L Elbow
            9: PointSmoother(min_cutoff=0.1, beta=0.05), # L Wrist
            6: PointSmoother(min_cutoff=0.1, beta=0.05), # R Shoulder
            8: PointSmoother(min_cutoff=0.1, beta=0.05), # R Elbow
            10: PointSmoother(min_cutoff=0.1, beta=0.05) # R Wrist
        }

    def process_frame(self, landmarks: np.ndarray, timestamp: float = None) -> AnalysisResult:
        """
        Input: landmarks (Array 17x3 di YOLO: [x, y, conf])
        Output: AnalysisResult
        """
        
        # --- 1. Smoothing & Selezione Keypoint ---
        # Applichiamo lo smoothing (metodo base)
        smoothed_landmarks = self.smooth_landmarks(landmarks, timestamp)

        idx_shoulder_l, idx_elbow_l, idx_wrist_l = 5, 7, 9
        idx_shoulder_r, idx_elbow_r, idx_wrist_r = 6, 8, 10
        
        # Determine target sides
        sides_to_process = []
        if self.side == "left" or self.side == "both":
            sides_to_process.append("left")
        if self.side == "right" or self.side == "both":
            sides_to_process.append("right")

        valid_angles = []

        # --- Process Left ---
        if "left" in sides_to_process:
             # Usiamo la confidence originale per decidere se calcolare
             if min(landmarks[idx_shoulder_l][2], landmarks[idx_elbow_l][2], landmarks[idx_wrist_l][2]) >= CONFIDENCE_THRESHOLD:
                # Usiamo coordinate SMOOTHED per l'angolo
                angle_l = calculate_angle(smoothed_landmarks[idx_shoulder_l][:2], 
                                          smoothed_landmarks[idx_elbow_l][:2], 
                                          smoothed_landmarks[idx_wrist_l][:2])
                valid_angles.append(angle_l)

        # --- Process Right ---
        if "right" in sides_to_process:
             if min(landmarks[idx_shoulder_r][2], landmarks[idx_elbow_r][2], landmarks[idx_wrist_r][2]) >= CONFIDENCE_THRESHOLD:
                angle_r = calculate_angle(smoothed_landmarks[idx_shoulder_r][:2], 
                                          smoothed_landmarks[idx_elbow_r][:2], 
                                          smoothed_landmarks[idx_wrist_r][:2])
                valid_angles.append(angle_r)

        # Se non abbiamo angoli validi
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
        correction_feedback = "curl_perfect_form"
        is_valid = True

        # LOGICA DI CONTEGGIO
        # [MODIFIED] Debouncing: Conferma lo stato solo se stabile per N frame
        
        # DOWN TRANSITION
        if angle > self.down_threshold:
            # Verifica se anche negli ultimi 2 frame eravamo in zona "down" (o quasi)
            # Usiamo una soglia leggermente tollerante per la storia per evitare sfarfallio sui bordi
            if self._is_stable_change(lambda x: x["angle"] > self.down_threshold - 5, consistency_frames=2):
                self.stage = "down"
            
        # UP TRANSITION
        if angle < self.up_threshold and self.stage == "down":
            # Verifica stabilità della chiusura (contrazione)
            if self._is_stable_change(lambda x: x["angle"] < self.up_threshold + 5, consistency_frames=2):
                self.stage = "up"
                self.reps += 1
                # Qui potremmo aggiungere logica per resettare errori se necessario

        # LOGICA DI CORREZIONE (Esempio semplice)
        # Se nello stato UP l'angolo è ancora troppo aperto (> 90), non sta chiudendo bene
        if self.stage == "up" and angle > 90:
            correction_feedback = "curl_err_flexion"
            is_valid = False

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