import time
import numpy as np
from typing import Optional
from src.core.interfaces import Exercise, AnalysisResult, HistoryEntry, StateDisplayInfo
from src.core.config_types import ExerciseConfig
from src.core.registry import register_exercise
from src.core.fsm import StaticDurationCounter
from src.utils.geometry import calculate_angle
from src.utils.smoothing import PointSmoother
from src.core.feedback import FeedbackSystem
from config.settings import PLANK_THRESHOLDS, CONFIDENCE_THRESHOLD, SMOOTHING_MIN_CUTOFF, SMOOTHING_BETA

@register_exercise("plank")
class Plank(Exercise):
    def __init__(self, config: ExerciseConfig):
        super().__init__(config)
        self.display_name_key = "plank_name"
        self.exercise_id = "Plank"
        self.is_time_based = True  # Flag for UI to show Timer instead of Reps
        
        # Delegate FSM to StaticDurationCounter (same pattern as Curl/Squat → RepetitionCounter)
        self.fsm = StaticDurationCounter(
            stability_duration=config.get("stability_duration", PLANK_THRESHOLDS["STABILITY_DURATION"])
        )
        self.stage = "waiting"
        
        self.side = "left" # Default to left view for plank usually, but can be configured
        if config.get("side"):
             self.side = config.get("side")

        # Smoothers
        self.smoothers = {
             # Left side
            5: PointSmoother(min_cutoff=SMOOTHING_MIN_CUTOFF, beta=SMOOTHING_BETA), # L Shoulder
            7: PointSmoother(min_cutoff=SMOOTHING_MIN_CUTOFF, beta=SMOOTHING_BETA), # L Elbow
            9: PointSmoother(min_cutoff=SMOOTHING_MIN_CUTOFF, beta=SMOOTHING_BETA), # L Wrist
            11: PointSmoother(min_cutoff=SMOOTHING_MIN_CUTOFF, beta=SMOOTHING_BETA),# L Hip
            15: PointSmoother(min_cutoff=SMOOTHING_MIN_CUTOFF, beta=SMOOTHING_BETA), # L Ankle
            
            # Right side
            6: PointSmoother(min_cutoff=SMOOTHING_MIN_CUTOFF, beta=SMOOTHING_BETA), # R Shoulder
            8: PointSmoother(min_cutoff=SMOOTHING_MIN_CUTOFF, beta=SMOOTHING_BETA), # R Elbow
            10: PointSmoother(min_cutoff=SMOOTHING_MIN_CUTOFF, beta=SMOOTHING_BETA), # R Wrist
            12: PointSmoother(min_cutoff=SMOOTHING_MIN_CUTOFF, beta=SMOOTHING_BETA), # R Hip
            16: PointSmoother(min_cutoff=SMOOTHING_MIN_CUTOFF, beta=SMOOTHING_BETA)  # R Ankle
        }
        
        self.feedback = FeedbackSystem()
        
        # Rule: Body Straightness (Shoulder-Hip-Ankle)
        self.feedback.add_rule(
            condition=lambda ctx: ctx.get("body_angle", 180) < PLANK_THRESHOLDS["SHOULDER_HIP_ANKLE_MIN"],
            message_key="plank_err_hips", # e.g. "Keep hips in line!"
            priority=10
        )

    def get_state_display(self, state: str) -> StateDisplayInfo:
        """Returns display metadata for plank-specific states."""
        _map = {
            "waiting": StateDisplayInfo("plank_state_waiting", (0, 255, 255), "neutral"),
            "countdown": StateDisplayInfo("plank_state_countdown", (0, 255, 255), "neutral"),
            "active": StateDisplayInfo("plank_phase_label", (0, 255, 0), "up"),
            "finished": StateDisplayInfo("plank_state_finished", (0, 255, 0), "neutral"),
        }
        return _map.get(state, super().get_state_display(state))

    def process_frame(self, landmarks: np.ndarray, timestamp: Optional[float] = None) -> AnalysisResult:
        if timestamp is None:
            timestamp = time.time()
            
        smoothed_landmarks = self.smooth_landmarks(landmarks, timestamp)
        
        # Keypoints
        side_indices = {
            "left": {
                "shoulder": 5, "elbow": 7, "wrist": 9, "hip": 11, "ankle": 15
            },
            "right": {
                "shoulder": 6, "elbow": 8, "wrist": 10, "hip": 12, "ankle": 16
            }
        }
        
        indices = side_indices.get(self.side, side_indices["left"])
        
        # Calculate Angles
        # 1. Body Angle (Shoulder - Hip - Ankle) -> Should be ~180
        body_angle = self._calculate_side_angle(
            landmarks, smoothed_landmarks, 
            (indices["shoulder"], indices["hip"], indices["ankle"]), 
            CONFIDENCE_THRESHOLD
        )
        
        # 2. Elbow Angle (Shoulder - Elbow - Wrist) -> Should be ~90
        elbow_angle = self._calculate_side_angle(
             landmarks, smoothed_landmarks,
             (indices["shoulder"], indices["elbow"], indices["wrist"]),
             CONFIDENCE_THRESHOLD
        )
        
        is_valid_pose = (body_angle is not None and elbow_angle is not None)
        
        is_form_correct = False
        
        if is_valid_pose:
            # Check thresholds
            body_ok = body_angle >= PLANK_THRESHOLDS["SHOULDER_HIP_ANKLE_MIN"]
            elbow_ok = (PLANK_THRESHOLDS["ELBOW_ANGLE_MIN"] <= elbow_angle <= PLANK_THRESHOLDS["ELBOW_ANGLE_MAX"])
            is_form_correct = body_ok and elbow_ok

        # Delegate state machine to StaticDurationCounter
        total_seconds, self.stage = self.fsm.process(is_form_correct, timestamp)
        self.reps = total_seconds

        # Feedback (exercise-specific, not FSM-level)
        current_feedback = self._resolve_feedback(
            is_valid_pose, is_form_correct, body_angle, elbow_angle
        )
        
        return AnalysisResult(
            reps=total_seconds,
            stage=self.stage,
            correction=current_feedback,
            angle=body_angle if body_angle else 0.0,
            is_valid=is_form_correct
        )

    def _resolve_feedback(self, is_valid_pose: bool, is_form_correct: bool,
                          body_angle: Optional[float], elbow_angle: Optional[float]) -> str:
        """Determines the appropriate feedback key based on current state and form."""
        if self.stage == "finished":
            return "plank_feedback_done"
        
        if not is_valid_pose:
            return "err_body_not_visible"
            
        if self.stage == "waiting":
            return "plank_feedback_get_ready"
            
        if self.stage == "countdown":
            remaining = self.fsm.countdown_remaining
            if remaining > 0:
                return f"plank_countdown_{remaining}"
            return "plank_feedback_hold"
            
        if self.stage == "active":
            # Check form quality via FeedbackSystem
            ctx = {"body_angle": body_angle, "elbow_angle": elbow_angle}
            correction, _ = self.feedback.check(ctx)
            if correction != "feedback_perfect" and not is_form_correct:
                return correction
            return "plank_feedback_stay_still"
        
        return "plank_feedback_get_ready"

    def reset(self):
        super().reset()
        self.stage = "waiting"
        self.fsm.reset()
