import sys
import os
import numpy as np

# Add project root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.core.entities.session import Session
from src.core.factory import ExerciseFactory
from src.exercises.squat import Squat
from src.core.interfaces import AnalysisResult

def verify_session_targets():
    print("\n[1] Testing Session Targets...")
    session = Session(user_id="testval", target_sets=4, target_reps=12)
    assert session.target_sets == 4
    assert session.target_reps == 12
    print("PASS: Session targets set correctly.")

def verify_factory():
    print("\n[2] Testing Exercise Factory...")
    config = {"side": "left"}
    
    # Test Squat
    squat = ExerciseFactory.create_exercise("Squat", config)
    assert isinstance(squat, Squat)
    assert squat.side == "left"
    print("PASS: Factory created Squat correctly.")
    
    # Test Error
    try:
        ExerciseFactory.create_exercise("Unknown", config)
        print("FAIL: Factory should have raised ValueError")
    except ValueError:
        print("PASS: Factory rejected unknown exercise.")

def verify_squat_logic():
    print("\n[3] Testing Squat Logic...")
    squat = Squat(config={"side": "right"})
    
    # Mock Keypoints
    # Hip=12, Knee=14, Ankle=16 (Right)
    # Create an array of 17 keypoints (all zeros initially)
    # Format: [x, y, conf]
    
    def get_kp(hip_y, knee_y, ankle_y, hip_x=100, knee_x=100, ankle_x=100):
        kp = np.zeros((17, 3))
        # Set confidence high
        kp[:, 2] = 0.9
        
        # Right Side Indices
        kp[12] = [hip_x, hip_y, 0.9]
        kp[14] = [knee_x, knee_y, 0.9]
        kp[16] = [ankle_x, ankle_y, 0.9]
        return kp

    # 1. Start (Standing) - Angle ~180 (Straight)
    # Hip roughly above Knee roughly above Ankle
    kp_start = get_kp(hip_y=100, knee_y=200, ankle_y=300) 
    # Check angle logic manually? No, trust process_frame.
    
    res = squat.process_frame(kp_start)
    print(f"Start Angle: {res.angle:.2f}, Stage: {res.stage}")
    assert res.stage == "start"
    
    # 2. Go Down (Squat) - Angle ~90
    # Knee moves forward? Or Hip moves back.
    # Let's just simulate coordinates that give 90 degrees.
    # Hip(0, 100), Knee(0, 0), Ankle(100, 0) -> 90 deg at Knee?
    # Wait, Knee is pivot.
    # Hip(0, 10), Knee(0, 0), Ankle(10, 0)
    # Angle at Knee.
    
    # Coordinates for ~90 deg
    kp_down = get_kp(hip_y=100, knee_y=200, ankle_y=200, hip_x=100, knee_x=200, ankle_x=200)
    # Wait geometry is subtle.
    # Let's use simple vertical/horizontal lines.
    # Hip(100, 100), Knee(100, 200), Ankle(100, 300) -> 180 deg.
    
    # Bend Knee:
    # Hip(50, 100), Knee(100, 200), Ankle(100, 300)
    # Vector Knee->Hip (-50, -100), Knee->Ankle (0, 100).
    # ...
    
    # Let's force an angle < down_threshold (90)
    # Hip and Ankle close to each other relative to knee?
    
    # Hip (100, 100)
    # Knee (200, 100)
    # Ankle (100, 100) -> 0 degrees (folded)
    
    kp_down = get_kp(hip_y=100, knee_y=100, ankle_y=100, hip_x=100, knee_x=200, ankle_x=100)
    res = squat.process_frame(kp_down)
    print(f"Down Angle: {res.angle:.2f}, Stage: {res.stage}")
    assert res.stage == "down"
    
    # 3. Go Up (Standing)
    res = squat.process_frame(kp_start)
    print(f"Up Angle: {res.angle:.2f}, Stage: {res.stage}, Reps: {res.reps}")
    assert res.stage == "up"
    assert res.reps == 1
    
    print("PASS: Squat counted 1 rep correctly.")

if __name__ == "__main__":
    verify_session_targets()
    verify_factory()
    verify_squat_logic()
