import sys
import os
import numpy as np
import time

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.exercises.curl import BicepCurl
from src.core.factory import ExerciseFactory

def test_refactoring():
    print("Testing Refactored Architecture...")
    
    # 1. Instantiate via Factory
    config = {"side": "right"}
    curl = ExerciseFactory.create_exercise("Bicep Curl", config)
    print("Instance created successfully.")
    
    # 2. Check Smoothers Initialization
    if hasattr(curl, 'smoothers') and len(curl.smoothers) > 0:
        print(f"PASS: Smoothers initialized ({len(curl.smoothers)} active).")
    else:
        print("FAIL: Smoothers not initialized.")
        
    # 3. Simulate Process Frame with Timestamp
    # Create fake landmarks (17, 3)
    landmarks = np.zeros((17, 3))
    # Fill critical points to avoid "body not visible" error immediately if possible, 
    # but we just want to see if it CRASHES on timestamp handling.
    
    t0 = time.time()
    try:
        # First call
        res1 = curl.process_frame(landmarks, timestamp=t0)
        print("PASS: process_frame call 1 (t0) successful.")
        
        # Second call
        res2 = curl.process_frame(landmarks, timestamp=t0 + 0.1)
        print("PASS: process_frame call 2 (t0 + 0.1) successful.")
        
    except Exception as e:
        print(f"FAIL: process_frame raised exception: {e}")
        import traceback
        traceback.print_exc()

    # 4. Check Reset
    curl.reps = 10
    curl.stage = "finished"
    curl.history.append("dummy")
    
    curl.reset()
    
    if curl.reps == 0 and curl.stage == "start" and len(curl.history) == 0:
        print("PASS: reset() cleared state.")
    else:
        print(f"FAIL: reset() did not clear state properly. Reps: {curl.reps}, Stage: {curl.stage}, Hist: {len(curl.history)}")

if __name__ == "__main__":
    test_refactoring()
