import sys
import os
import numpy as np
import time

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.exercises.curl import BicepCurl
from src.core.factory import ExerciseFactory

def verify_debouncing():
    print("Verifying Debouncing Logic...")
    
    # Setup
    config = {"side": "right", "down_angle": 160, "up_angle": 50}
    curl = BicepCurl(config) # Direct instantiation for control
    
    # Mock Helper
    def process_angle(angle):
        # Create fake landmarks to produce valid angle
        # We cheat: we don't care about landmarks if we could inject angle, 
        # but process_frame calculates angle from landmarks.
        # So we must mock calculate_angle or inject landmarks that result in 'angle'.
        # Easier: Overwrite the calculated angle in the loop or mock calculate_angle.
        # Let's mock the 'calculate_angle' function in the module if possible, 
        # OR just construct landmarks.
        pass

    # Actually, BicepCurl.process_frame calculates keys.
    # Shoulder(0,0), Elbow(1,0), Wrist(1+cos(a), sin(a))
    def create_landmarks(angle_deg):
        rad = np.radians(angle_deg)
        # Shoulder at 0,0
        # Elbow at 100, 0
        # Wrist at 100 + 100*cos(rad), 100*sin(rad) -> This is angle 180-deg... geometry is tricky.
        # Let's use a simpler approach: Monkey Patch `calculate_angle` for this test context?
        # No, let's create simple geometry.
        # A=Shoulder(0,100), B=Elbow(0,0), C=Wrist(x,y)
        # Vector BA = (0, 100). Vector BC = (x, y).
        # Angle is between BA and BC.
        # Let's keep BA vertical up.
        # If angle is 180, BC is vertical down (0, -100).
        # If angle is 90, BC is horizontal (100, 0).
        
        # Formula: x = 100 * sin(rad), y = -100 * cos(rad) ?
        # Let's use simple logic:
        # P5 (Sh): (0, 100), P7 (El): (0, 0), P9 (Wr): ...
        
        # If angle=180: Wrist=(0, -100)
        # If angle=90: Wrist=(100, 0)
        # If angle=0: Wrist=(0, 100)
        
        rad = np.radians(angle_deg)
        wx = 100 * np.sin(rad)
        wy = -100 * np.cos(rad) # wait, cos(0)=1 -> y=-100... angle 0 should be close to A?
        # calculate_angle uses dot product.
        
        # Let's just create a dummy class that inherits and Overrides process_frame? 
        # No, too complex.
        # Let's just rely on the fact that we can fake "valid_angles" internal logic?
        # No, we must call process_frame.
        
        # Let's patch `calculate_angle` in `src.exercises.curl`?
        pass

    # Let's use `unittest.mock` to patch calculate_angle
    from unittest.mock import patch
    
    with patch('src.exercises.curl.calculate_angle') as mock_calc:
        # Sequence of angles to feed
        # Threshold Down = 160.
        sequence = [
            150, # Initial
            165, # Spike (> 160). Should NOT trigger DOWN yet (N=2 checks history)
            150, # Back to normal.
            165, # Trigger 1
            165, # Trigger 2 (History: 165, 165). Should trigger DOWN.
            165, # Trigger 3 (History: 165, 165). Definitely Down.
        ]
        
        # Fake landmarks (shape correct, values irrelevant as calc is mocked)
        dummy_lm = np.ones((17, 3)) 
        
        print(f"Thresholds: Down={curl.down_threshold}, Up={curl.up_threshold}")
        
        for i, ang in enumerate(sequence):
            mock_calc.return_value = ang
            
            # Timestamp needed? We can pass None as we don't test OneEuro here (or mocked)
            # Actually process_frame calls smooth_landmarks.
            # We should probably initialize smoothers to identity or pass dummy.
            
            res = curl.process_frame(dummy_lm, timestamp=time.time())
            
            print(f"Frame {i+1}: Input Angle={ang}, Result Stage='{res.stage}'")
            
            # Verification Logic
            if i == 1: # Spike
                if res.stage == "down":
                    print("FAIL: Spurious spike triggered change!")
                else:
                    print("PASS: Spike resisted.")
            
            if i == 5: # Stable (Last one)
                if res.stage == "down":
                    print("PASS: Stable signal triggered change.")
                else:
                    print("FAIL: Stable signal did not trigger change.")

if __name__ == "__main__":
    verify_debouncing()
