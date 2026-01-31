import numpy as np
from typing import Dict, Any, List, Optional
from src.core.interfaces import Exercise, AnalysisResult
from src.utils.geometry import calculate_angle
from src.utils.smoothing import PointSmoother
from config.settings import CONFIDENCE_THRESHOLD, HYSTERESIS_TOLERANCE

class PushUp(Exercise):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # [DRY] Validation: Ensure all thresholds are passed from central settings
        required_keys = ["up_angle", "down_angle", "form_angle_min"]
        if not all(k in config for k in required_keys):
            raise ValueError(f"PushUp configuration error: Missing keys {required_keys}. Received: {list(config.keys())}")

        self.up_threshold = config["up_angle"]
        self.down_threshold = config["down_angle"]
        self.form_threshold_min = config["form_angle_min"]
        self.display_name_key = "pushup_name"
        
        # Side to analyze: 'left', 'right', or 'auto' (based on confidence/visibility)
        # Defaulting to 'left' as usually one side is presented to camera
        self.side = config.get("side", "left")

        # Configure smoothers for key joints
        # Reps: Shoulder, Elbow, Wrist
        # Form: Shoulder, Hip, Ankle
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

    def process_frame(self, landmarks: np.ndarray, timestamp: float = None) -> AnalysisResult:
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
        
        # Determine target sides
        sides_to_process = []
        if self.side == "left" or self.side == "both":
            sides_to_process.append("left")
        if self.side == "right" or self.side == "both":
            sides_to_process.append("right")
            
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
                reps=self.reps,
                stage="unknown",
                correction="err_body_not_visible",
                angle=0.0,
                is_valid=False
            )

        # --- 3. FSM (Finite State Machine) ---
        correction_feedback = "pushup_perfect_form"
        is_valid = True

        # FORM CHECK Logic
        # Body must be straight (~180 degrees)
        # We check if it deviates significantly below threshold (e.g. < 160)
        # Note: calculate_angle returns [0, 180]. So 180 is max.
        if current_body_angle < self.form_threshold_min:
            correction_feedback = "pushup_warn_back" # "Occhio alla schiena"
            is_valid = True # [UX] Permissive: Count the rep but show warning

        # COUNTING LOGIC
        # DOWN: Elbow angle decreases -> < 90
        # UP: Elbow angle increases -> > 160
        
        # DOWN TRANSITION
        if current_angle < self.down_threshold:
            # Debounce: Confirm descent
            if self._is_stable_change(lambda x: x["angle"] < self.down_threshold + HYSTERESIS_TOLERANCE, consistency_frames=2):
                self.stage = "pushup_down"
            
        # UP TRANSITION
        if current_angle > self.up_threshold and self.stage == "pushup_down":
            # Debounce: Confirm ascent (extension)
            if self._is_stable_change(lambda x: x["angle"] > self.up_threshold - HYSTERESIS_TOLERANCE, consistency_frames=2):
                self.stage = "pushup_up"
                self.reps += 1
                # Optional: Reset error state logic if needed based on the rep cycle

        # --- History Update ---
        self.history.append({
            "angle": current_angle,
            "body_angle": current_body_angle,
            "stage": self.stage,
            "reps": self.reps,
            "is_valid": is_valid
        })

        return AnalysisResult(
            reps=self.reps,
            stage=self.stage,
            correction=correction_feedback,
            angle=current_angle,
            is_valid=is_valid
        )

    def reset(self):
        super().reset()
