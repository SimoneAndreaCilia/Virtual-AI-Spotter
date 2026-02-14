import numpy as np
from typing import Optional
from src.core.interfaces import Exercise, AnalysisResult, HistoryEntry, StateDisplayInfo
from src.core.mixins import RepBasedMixin
from src.core.config_types import ExerciseConfig
from src.core.registry import register_exercise
from src.utils.geometry import calculate_angle
from src.utils.smoothing import PointSmoother
from src.core.fsm import RepetitionCounter
from src.core.feedback import FeedbackSystem
from config.settings import CURL_THRESHOLDS, CONFIDENCE_THRESHOLD, SMOOTHING_MIN_CUTOFF, SMOOTHING_BETA


@register_exercise("bicep curl")
class BicepCurl(RepBasedMixin, Exercise):
    def __init__(self, config: ExerciseConfig):
        super().__init__(config)
        self.display_name_key = "curl_name"
        self.exercise_id = "Bicep Curl"  # Canonical name for database
        
        # Body side to analyze: 'right' or 'left'
        self.side = config.get("side", "right")

        # Smoother for critical keypoints (Shoulder, Elbow, Wrist for both sides)
        # Smoother for critical keypoints (Shoulder, Elbow, Wrist for both sides)
        self.smoothers = {
            5: PointSmoother(min_cutoff=SMOOTHING_MIN_CUTOFF, beta=SMOOTHING_BETA), # L Shoulder
            7: PointSmoother(min_cutoff=SMOOTHING_MIN_CUTOFF, beta=SMOOTHING_BETA), # L Elbow
            9: PointSmoother(min_cutoff=SMOOTHING_MIN_CUTOFF, beta=SMOOTHING_BETA), # L Wrist
            6: PointSmoother(min_cutoff=SMOOTHING_MIN_CUTOFF, beta=SMOOTHING_BETA), # R Shoulder
            8: PointSmoother(min_cutoff=SMOOTHING_MIN_CUTOFF, beta=SMOOTHING_BETA), # R Elbow
            10: PointSmoother(min_cutoff=SMOOTHING_MIN_CUTOFF, beta=SMOOTHING_BETA) # R Wrist
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
            inverted=True,
            state_prefix="curl"
        )
        self.feedback = FeedbackSystem()
        
        # Rule: Full Extension Logic handled by FSM state check?
        # Rule: Flexion Error
        self.feedback.add_rule(
            condition=lambda ctx: ctx["stage"] == "up" and ctx["angle"] > 90,
            message_key="curl_err_flexion",
            priority=5
        )

    def get_state_display(self, state: str) -> StateDisplayInfo:
        """Returns display metadata for curl-specific states."""
        _map = {
            "curl_up": StateDisplayInfo("curl_state_up", (0, 255, 0), "up"),
            "curl_down": StateDisplayInfo("curl_state_down", (0, 165, 255), "down"),
        }
        return _map.get(state, super().get_state_display(state))

    def process_frame(self, landmarks: np.ndarray, timestamp: Optional[float] = None) -> AnalysisResult:
        """
        Input: landmarks (Array 17x3 of YOLO: [x, y, conf])
        Output: AnalysisResult
        """
        
        # --- 1. Smoothing ---
        smoothed_landmarks = self.smooth_landmarks(landmarks, timestamp)

        # --- 2. Side Processing (using base class helpers) ---
        # Keypoint indices: (Shoulder, Elbow, Wrist) for each side
        side_indices = {
            "left": (5, 7, 9),   # L Shoulder, L Elbow, L Wrist
            "right": (6, 8, 10)  # R Shoulder, R Elbow, R Wrist
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

        # If we don't have valid angles
        if len(valid_angles) < len(sides_to_process):
            return AnalysisResult(
                reps=self.reps,
                stage="unknown",
                correction="err_body_not_visible",
                angle=0.0,
                is_valid=False
            )

        # --- 3. Calculate Geometry (Average) ---
        angle = np.mean(valid_angles)

        # --- 4. Delegate to Subsystems ---
        
        # A. FSM Rep Counting
        self.reps, stage_raw = self.fsm.process(angle)
        self.stage = stage_raw # "up" or "down" (generic)
        
        # B. Feedback System
        feedback_ctx = {"angle": angle, "stage": self.stage}
        correction_feedback, is_valid = self.feedback.check(feedback_ctx)
        
        if correction_feedback == "feedback_perfect":
             correction_feedback = "curl_perfect_form"

        # [NEW] Update History (using NamedTuple for memory efficiency)
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