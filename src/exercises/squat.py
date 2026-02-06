import numpy as np
from typing import Dict, Any
from src.core.interfaces import Exercise, AnalysisResult
from src.core.registry import register_exercise
from src.utils.geometry import calculate_angle
from src.utils.smoothing import PointSmoother
from src.core.fsm import RepetitionCounter
from src.core.feedback import FeedbackSystem
from config.settings import SQUAT_THRESHOLDS, CONFIDENCE_THRESHOLD


@register_exercise("squat")
class Squat(Exercise):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        self.display_name_key = "squat_name"
        self.exercise_id = "Squat"  # Canonical name for database
        
        # Body side to analyze: 'right' (default) or 'left'
        self.side = config.get("side", "right")

        # Smoother for critical keypoints (Hips, Knees, Ankles)
        self.smoothers = {
            11: PointSmoother(min_cutoff=0.1, beta=0.05), # L Hip
            13: PointSmoother(min_cutoff=0.1, beta=0.05), # L Knee
            15: PointSmoother(min_cutoff=0.1, beta=0.05), # L Ankle
            12: PointSmoother(min_cutoff=0.1, beta=0.05), # R Hip
            14: PointSmoother(min_cutoff=0.1, beta=0.05), # R Knee
            16: PointSmoother(min_cutoff=0.1, beta=0.05), # R Ankle
        }

        # --- NEW ARCHITECTURE ---
        self.fsm = RepetitionCounter(
            up_threshold=config.get("up_angle", SQUAT_THRESHOLDS["UP_ANGLE"]),
            down_threshold=config.get("down_angle", SQUAT_THRESHOLDS["DOWN_ANGLE"]),
            start_stage="up",
            state_prefix="squat"
        )
        self.feedback = FeedbackSystem()
        
        # Future-proof: Add depth verification or specific squat rules here?
        # self.feedback.add_rule(condition=..., message_key="squat_too_shallow")

    def process_frame(self, landmarks: np.ndarray, timestamp: float = None) -> AnalysisResult:
        """
        Input: landmarks (Array 17x3 di YOLO: [x, y, conf])
        Output: AnalysisResult
        """
        
        # --- 1. Smoothing ---
        smoothed_landmarks = self.smooth_landmarks(landmarks, timestamp)

        # --- 2. Side Processing (using base class helpers) ---
        # Keypoint indices: (Hip, Knee, Ankle) for each side
        side_indices = {
            "left": (11, 13, 15),   # L Hip, L Knee, L Ankle
            "right": (12, 14, 16)   # R Hip, R Knee, R Ankle
        }
        
        sides_to_process = self._get_sides_to_process()
        valid_angles = []

        for side in sides_to_process:
            angle = self._calculate_side_angle(
                landmarks, smoothed_landmarks,
                side_indices[side], CONFIDENCE_THRESHOLD
            )
            if angle is not None:
                valid_angles.append(angle)

        # Se non abbiamo angoli validi
        if len(valid_angles) < len(sides_to_process):
            return AnalysisResult(
                reps=self.reps,
                stage="unknown",
                correction="err_body_not_visible",
                angle=0.0,
                is_valid=False
            )

        # --- 3. Geometric Calculation (Average) ---
        angle = np.mean(valid_angles)

        # --- 3. Delegate to Subsystems ---
        
        # A. FSM Rep Counting (returns prefixed state directly)
        self.reps, self.stage = self.fsm.process(angle)

        # B. Feedback System
        feedback_ctx = {"angle": angle, "stage": self.stage}
        correction_feedback, is_valid = self.feedback.check(feedback_ctx)
        
        if correction_feedback == "feedback_perfect":
            correction_feedback = "squat_perfect_form"
        
        # [NEW] Update History (using NamedTuple for memory efficiency)
        from src.core.interfaces import HistoryEntry
        self.history.append(HistoryEntry(
            angle=angle,
            stage=self.stage,
            reps=self.reps,
            is_valid=is_valid
        ))

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
