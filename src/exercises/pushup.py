import numpy as np
from typing import Dict, Any, List, Optional
from src.core.interfaces import Exercise, AnalysisResult, PushUpHistoryEntry
from src.core.registry import register_exercise
from src.utils.geometry import calculate_angle
from src.utils.smoothing import PointSmoother
from src.core.fsm import RepetitionCounter
from src.core.feedback import FeedbackSystem
from config.settings import CONFIDENCE_THRESHOLD, PUSHUP_THRESHOLDS


@register_exercise("pushup")
class PushUp(Exercise):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        self.display_name_key = "pushup_name"
        self.exercise_id = "PushUp"  # Canonical name for database
        
        # Side to analyze: 'left', 'right', or 'auto' (based on confidence/visibility)
        # Defaulting to 'left' as usually one side is presented to camera
        self.side = config.get("side", "left")

        # Configure smoothers for key joints
        self.smoothers = {
            # Left Side
            5: PointSmoother(min_cutoff=0.1, beta=0.05),  # L Shoulder
            7: PointSmoother(min_cutoff=0.1, beta=0.05),  # L Elbow
            9: PointSmoother(min_cutoff=0.1, beta=0.05),  # L Wrist
            11: PointSmoother(min_cutoff=0.1, beta=0.05), # L Hip
            15: PointSmoother(min_cutoff=0.1, beta=0.05), # L Ankle
            
            # Right Side
            6: PointSmoother(min_cutoff=0.1, beta=0.05),  # R Shoulder
            8: PointSmoother(min_cutoff=0.1, beta=0.05),  # R Elbow
            10: PointSmoother(min_cutoff=0.1, beta=0.05), # R Wrist
            12: PointSmoother(min_cutoff=0.1, beta=0.05), # R Hip
            16: PointSmoother(min_cutoff=0.1, beta=0.05)  # R Ankle
        }

        # --- FSM & Feedback (with defaults from settings) ---
        self.fsm = RepetitionCounter(
            up_threshold=config.get("up_angle", PUSHUP_THRESHOLDS["UP_ANGLE"]), 
            down_threshold=config.get("down_angle", PUSHUP_THRESHOLDS["DOWN_ANGLE"]),
            start_stage="up",
            state_prefix="pushup"
        )
        
        self.feedback = FeedbackSystem()
        
        # Rule 1: Back Straightness (Priority 5 - Medium)
        form_min = config.get("form_angle_min", PUSHUP_THRESHOLDS["FORM_ANGLE_MIN"])
        self.feedback.add_rule(
            condition=lambda ctx: ctx.get("body_angle", 180) < form_min,
            message_key="pushup_warn_back",
            priority=5
        )

    def process_frame(self, landmarks: np.ndarray, timestamp: Optional[float] = None) -> AnalysisResult:
        """
        Input: landmarks (Array 17x3 from YOLO: [x, y, conf])
        Output: AnalysisResult
        """
        
        # --- 1. Smoothing & Keypoint Selection ---
        smoothed_landmarks = self.smooth_landmarks(landmarks, timestamp)

        # Indices map
        idx_shoulder_l, idx_elbow_l, idx_wrist_l = 5, 7, 9
        idx_hip_l, idx_ankle_l = 11, 15
        
        idx_shoulder_r, idx_elbow_r, idx_wrist_r = 6, 8, 10
        idx_hip_r, idx_ankle_r = 12, 16
        
        # Determine target sides (using base class helper)
        sides_to_process = self._get_sides_to_process()
            
        # Data holders per side
        data_left = None  # Will hold (angle_reps, angle_form, confidence)
        data_right = None

        # --- Process Left ---
        if "left" in sides_to_process:
             required_indices = [idx_shoulder_l, idx_elbow_l, idx_wrist_l, idx_hip_l, idx_ankle_l]
             # Check if all points are visible
             if all(landmarks[i][2] >= CONFIDENCE_THRESHOLD for i in required_indices):
                # Calculate average confidence for this side
                conf_l = np.mean([landmarks[i][2] for i in required_indices])
                
                angle_l_elbow = calculate_angle(smoothed_landmarks[idx_shoulder_l][:2], 
                                                smoothed_landmarks[idx_elbow_l][:2], 
                                                smoothed_landmarks[idx_wrist_l][:2])
                
                angle_l_body = calculate_angle(smoothed_landmarks[idx_shoulder_l][:2], 
                                               smoothed_landmarks[idx_hip_l][:2], 
                                               smoothed_landmarks[idx_ankle_l][:2])
                
                data_left = (angle_l_elbow, angle_l_body, conf_l)

        # --- Process Right ---
        if "right" in sides_to_process:
             required_indices = [idx_shoulder_r, idx_elbow_r, idx_wrist_r, idx_hip_r, idx_ankle_r]
             if all(landmarks[i][2] >= CONFIDENCE_THRESHOLD for i in required_indices):
                conf_r = np.mean([landmarks[i][2] for i in required_indices])
                
                angle_r_elbow = calculate_angle(smoothed_landmarks[idx_shoulder_r][:2], 
                                                smoothed_landmarks[idx_elbow_r][:2], 
                                                smoothed_landmarks[idx_wrist_r][:2])
                
                angle_r_body = calculate_angle(smoothed_landmarks[idx_shoulder_r][:2], 
                                               smoothed_landmarks[idx_hip_r][:2], 
                                               smoothed_landmarks[idx_ankle_r][:2])
                
                data_right = (angle_r_elbow, angle_r_body, conf_r)

        # --- Selection Logic (Winner Takes All) ---
        current_angle = 0.0
        current_body_angle = 0.0

        if data_left and data_right:
            # Both sides valid: check confidence difference
            conf_l = data_left[2]
            conf_r = data_right[2]
            
            if abs(conf_l - conf_r) > 0.1:
                # Significant difference: pick winner
                if conf_l > conf_r:
                    current_angle = data_left[0]
                    current_body_angle = data_left[1]
                else:
                    current_angle = data_right[0]
                    current_body_angle = data_right[1]
            else:
                # Similar confidence: average them
                current_angle = np.mean([data_left[0], data_right[0]])
                current_body_angle = np.mean([data_left[1], data_right[1]])
                
        elif data_left:
            # Only Left valid
            current_angle = data_left[0]
            current_body_angle = data_left[1]
            
        elif data_right:
            # Only Right valid
            current_angle = data_right[0]
            current_body_angle = data_right[1]
            
        else:
             # No valid sides
             return AnalysisResult(
                reps=self.reps, # Use internal tracked reps
                stage="unknown",
                correction="err_body_not_visible",
                angle=0.0,
                is_valid=False
            )

        # --- 3. Delegate to Subsystems ---
        
        # A. Status & Counting (FSM returns prefixed state directly)
        self.reps, self.stage = self.fsm.process(current_angle)

        # B. Feedback Check
        feedback_ctx = {
            "angle": current_angle,
            "body_angle": current_body_angle,
            "stage": self.stage
        }
        correction_feedback, is_valid = self.feedback.check(feedback_ctx)
        
        # UX: If "perfect", ensure we map to pushup specific absolute key if needed
        if correction_feedback == "feedback_perfect":
            correction_feedback = "pushup_perfect_form"

        # --- History Update (using NamedTuple for memory efficiency) ---
        self.history.append(PushUpHistoryEntry(
            angle=current_angle,
            body_angle=current_body_angle,
            stage=self.stage,
            reps=self.reps,
            is_valid=is_valid
        ))

        return AnalysisResult(
            reps=self.reps,
            stage=self.stage,
            correction=correction_feedback,
            angle=current_angle,
            is_valid=is_valid
        )

    def reset(self):
        super().reset()
        self.fsm.reset()
        self.feedback.reset()
