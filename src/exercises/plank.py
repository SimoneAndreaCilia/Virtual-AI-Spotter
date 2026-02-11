import time
import numpy as np
from typing import Dict, Any, Optional
from src.core.interfaces import Exercise, AnalysisResult, HistoryEntry
from src.core.registry import register_exercise
from src.utils.geometry import calculate_angle
from src.utils.smoothing import PointSmoother
from src.core.feedback import FeedbackSystem
from config.settings import PLANK_THRESHOLDS, CONFIDENCE_THRESHOLD

@register_exercise("plank")
class Plank(Exercise):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.display_name_key = "plank_name"
        self.exercise_id = "Plank"
        self.is_time_based = True  # Flag for UI to show Timer instead of Reps
        
        # State machine for Plank
        # Stages: "waiting" -> "countdown" -> "active" -> "finished"
        self.stage = "waiting"
        
        # Timer variables
        self.start_hold_time: Optional[float] = None
        self.timer_start_time: Optional[float] = None
        self.elapsed_time: float = 0.0
        self.last_valid_frame_time: float = 0.0
        
        # Stability check for countdown
        self.stability_duration = config.get("stability_duration", PLANK_THRESHOLDS["STABILITY_DURATION"])
        
        self.side = "left" # Default to left view for plank usually, but can be configured
        if config.get("side"):
             self.side = config.get("side")

        # Smoothers
        self.smoothers = {
             # Left side
            5: PointSmoother(), # L Shoulder
            7: PointSmoother(), # L Elbow
            9: PointSmoother(), # L Wrist
            11: PointSmoother(),# L Hip
            15: PointSmoother(), # L Ankle
            
            # Right side
            6: PointSmoother(), # R Shoulder
            8: PointSmoother(), # R Elbow
            10: PointSmoother(), # R Wrist
            12: PointSmoother(), # R Hip
            16: PointSmoother()  # R Ankle
        }
        
        self.feedback = FeedbackSystem()
        
        # Rule: Body Straightness (Shoulder-Hip-Ankle)
        self.feedback.add_rule(
            condition=lambda ctx: ctx.get("body_angle", 180) < PLANK_THRESHOLDS["SHOULDER_HIP_ANKLE_MIN"],
            message_key="plank_err_hips", # e.g. "Keep hips in line!"
            priority=10
        )

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
        
        current_feedback = "plank_feedback_get_ready"
        is_form_correct = False
        
        if is_valid_pose:
            # Check thresholds
            body_ok = body_angle >= PLANK_THRESHOLDS["SHOULDER_HIP_ANKLE_MIN"]
            elbow_ok = (PLANK_THRESHOLDS["ELBOW_ANGLE_MIN"] <= elbow_angle <= PLANK_THRESHOLDS["ELBOW_ANGLE_MAX"])
            
            is_form_correct = body_ok and elbow_ok
            
            # Update Feedback System
            ctx = {"body_angle": body_angle, "elbow_angle": elbow_angle}
            correction, _ = self.feedback.check(ctx)
            if correction != "feedback_perfect" and not is_form_correct:
                 curr_feedback = correction
            else:
                 current_feedback = "plank_feedback_hold"
        else:
             current_feedback = "err_body_not_visible"

        # State Machine
        if self.stage == "waiting":
            if is_form_correct:
                self.stage = "countdown"
                self.start_hold_time = timestamp
                current_feedback = "plank_feedback_hold"
            else:
                self.start_hold_time = None
                current_feedback = "plank_feedback_get_ready"
                
        elif self.stage == "countdown":
            if is_form_correct:
                hold_time = timestamp - self.start_hold_time
                if hold_time >= self.stability_duration:
                    self.stage = "active"
                    self.timer_start_time = timestamp
                    self.elapsed_time = 0
                    current_feedback = "plank_feedback_stay_still"
                else:
                    remaining = int(self.stability_duration - hold_time)
                    current_feedback = f"plank_countdown_{remaining+1}"
            else:
                self.stage = "waiting" # Reset if form broke during countdown
                
        elif self.stage == "active":
            if is_form_correct:
                self.elapsed_time = timestamp - self.timer_start_time
                self.last_valid_frame_time = timestamp
                current_feedback = "plank_feedback_stay_still"
            else:
                # Tolerance: How long can we lose form before stopping?
                # For now, immediate stop or maybe 1s grace period?
                # Let's do immediate stop for simplicity as per requirements "quando ti sposti... si blocca"
                self.stage = "finished" 

        elif self.stage == "finished":
            current_feedback = "plank_feedback_done"
            # Timer effectively stopped at last valid time

        # Return result
        # Reps field holds integers: in this case, full seconds
        total_seconds = int(self.elapsed_time)
        
        return AnalysisResult(
            reps=total_seconds,
            stage=self.stage,
            correction=current_feedback,
            angle=body_angle if body_angle else 0.0,
            is_valid=is_form_correct
        )

    def reset(self):
        super().reset()
        self.stage = "waiting"
        self.start_hold_time = None
        self.timer_start_time = None
        self.elapsed_time = 0.0
