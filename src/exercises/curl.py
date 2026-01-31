import numpy as np
from typing import Dict, Any, Tuple
from src.core.interfaces import Exercise, AnalysisResult
from src.utils.geometry import calculate_angle
from src.utils.smoothing import PointSmoother
from src.core.fsm import RepetitionCounter
from src.core.feedback import FeedbackSystem
from config.settings import CURL_THRESHOLDS, CONFIDENCE_THRESHOLD, HYSTERESIS_TOLERANCE

class BicepCurl(Exercise):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.display_name_key = "curl_name"
        
        # Lato del corpo da analizzare: 'right' o 'left'
        self.side = config.get("side", "right")

        # [NEW] Smoother per i keypoint critici (Spalla, Gomito, Polso per entrambi i lati)
        self.smoothers = {
            5: PointSmoother(min_cutoff=0.1, beta=0.05), # L Shoulder
            7: PointSmoother(min_cutoff=0.1, beta=0.05), # L Elbow
            9: PointSmoother(min_cutoff=0.1, beta=0.05), # L Wrist
            6: PointSmoother(min_cutoff=0.1, beta=0.05), # R Shoulder
            8: PointSmoother(min_cutoff=0.1, beta=0.05), # R Elbow
            10: PointSmoother(min_cutoff=0.1, beta=0.05) # R Wrist
        }
        
        # --- NEW ARCHITECTURE ---
        # Curl Logic is INVERTED compared to Squat:
        # "UP" (Concentrica) is SMALL angle (<30)
        # "DOWN" (Eccentrica) is LARGE angle (>160)
        # We use the 'inverted' flag in FSM
        self.fsm = RepetitionCounter(
            up_threshold=config.get("up_angle", CURL_THRESHOLDS["UP_ANGLE"]),
            down_threshold=config.get("down_angle", CURL_THRESHOLDS["DOWN_ANGLE"]),
            start_stage="down", # Start extended
            inverted=True 
        )
        self.feedback = FeedbackSystem()
        
        # Rule: Full Extension Logic handled by FSM state check?
        # Rule: Flexion Error
        self.feedback.add_rule(
            condition=lambda ctx: ctx["stage"] == "up" and ctx["angle"] > 90,
            message_key="curl_err_flexion",
            priority=5
        )

    def process_frame(self, landmarks: np.ndarray, timestamp: float = None) -> AnalysisResult:
        """
        Input: landmarks (Array 17x3 di YOLO: [x, y, conf])
        Output: AnalysisResult
        """
        
        # --- 1. Smoothing & Selezione Keypoint ---
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
             if min(landmarks[idx_shoulder_l][2], landmarks[idx_elbow_l][2], landmarks[idx_wrist_l][2]) >= CONFIDENCE_THRESHOLD:
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

        # --- 3. Delegate to Subsystems ---
        
        # A. FSM Rep Counting
        self.reps, stage_raw = self.fsm.process(angle)
        self.stage = stage_raw # "up" or "down" (generic)
        
        # B. Feedback System
        feedback_ctx = {"angle": angle, "stage": self.stage}
        correction_feedback, is_valid = self.feedback.check(feedback_ctx)
        
        if correction_feedback == "feedback_perfect":
             correction_feedback = "curl_perfect_form"

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
        self.fsm.reset()
        self.feedback.reset()