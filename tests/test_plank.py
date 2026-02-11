import unittest
import numpy as np
import time
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.exercises.plank import Plank
from config.settings import PLANK_THRESHOLDS

class TestPlank(unittest.TestCase):
    def setUp(self):
        self.config = {"side": "left"}
        self.plank = Plank(self.config)
        
    def create_mock_landmarks(self, body_angle, elbow_angle):
        # Create a simple stickman with desired angles
        # Indices: 5:Sh, 7:El, 9:Wr, 11:Hip, 15:Ank (Left)
        # We'll just position them to mathematically satisfy the angles
        landmarks = np.zeros((33, 3))
        # Confidence = 1.0
        landmarks[:, 2] = 1.0
        
        # Shoulder at (0, 0)
        landmarks[5] = [0, 0, 1]
        
        # Hip at (1, 0) -> Body line horizontal
        landmarks[11] = [1, 0, 1]
        
        # Ankle geometry for 180 deg body (Sh-Hip-Ank)
        if body_angle == 180:
             landmarks[15] = [2, 0, 1]
        elif body_angle < 160:
             landmarks[15] = [1, 1, 1]
             
        # Elbow Angle: Sh-El-Wr. Vertex is Elbow.
        if elbow_angle == 90:
            landmarks[7] = [0, 1, 1]
            landmarks[9] = [1, 1, 1]
        elif elbow_angle > 110:
            landmarks[7] = [0, 1, 1]
            landmarks[9] = [0, 2, 1]
            
        return landmarks

    def test_ideal_plank_mechanics(self):
        # 1. Start: Good form
        lm = self.create_mock_landmarks(body_angle=180, elbow_angle=90)
        
        # Initial frame (t=0)
        res = self.plank.process_frame(lm, timestamp=0.0)
        self.assertEqual(res.stage, "countdown")
        # Logic update: first frame might be 'hold' if just transitioned, or countdown if updated.
        # Check plank.py: if waiting -> correct -> stage=countdown, feedback=hold. Use next frame for countdown?
        # Actually in plank.py:
        # if stage == "waiting": ... stage="countdown", feedback="plank_feedback_hold"
        self.assertEqual(res.correction, "plank_feedback_hold")
        
        # 2. Hold for 2.9s (Still countdown)
        res = self.plank.process_frame(lm, timestamp=2.9)
        self.assertEqual(res.stage, "countdown")
        self.assertIn("countdown", res.correction)
        
        # 3. Hold for 3.1s (Active) - transition happens here
        res = self.plank.process_frame(lm, timestamp=3.1)
        self.assertEqual(res.stage, "active")
        self.assertEqual(res.reps, 0) # Just started
        self.assertEqual(res.correction, "plank_feedback_stay_still")
        
        # 4. Active for 5 more seconds
        # t = 3.1 + 5.0 = 8.1
        res = self.plank.process_frame(lm, timestamp=8.1)
        self.assertEqual(res.stage, "active")
        self.assertEqual(res.reps, 5) # 5 seconds
        self.assertEqual(res.correction, "plank_feedback_stay_still")
        
        # 5. Break form (Body bent)
        bad_lm = self.create_mock_landmarks(body_angle=90, elbow_angle=90)
        res = self.plank.process_frame(bad_lm, timestamp=9.0)
        self.assertEqual(res.stage, "finished")
        self.assertEqual(res.reps, 5)
        
        # PROOF OF BUG/FIX:
        # The session manager uses self.plank.reps to save data.
        # We must ensure self.plank.reps is updated to match res.reps
        self.assertEqual(self.plank.reps, 5, "self.plank.reps should match the duration in seconds")

    def test_long_duration_update(self):
        # 1. Start & Active
        lm = self.create_mock_landmarks(body_angle=180, elbow_angle=90)
        self.plank.process_frame(lm, timestamp=0.0) # wait
        self.plank.process_frame(lm, timestamp=0.1) # countdown start
        self.plank.process_frame(lm, timestamp=3.2) # active (3.1s hold)
        
        # 2. Simulate 1 minute 5 seconds passing (Total hold = 3.1 + 65 = 68.1)
        # Active start was at 3.1 (approx). elapsed = timestamp - timer_start
        # timer_start set at ~3.1. 
        # Let's say timestamp is now 100.0.
        res = self.plank.process_frame(lm, timestamp=100.0)
        
        expected_duration = int(100.0 - 3.1) # approx 96-97
        self.assertTrue(res.reps > 60, "Should be more than 1 minute")
        self.assertEqual(self.plank.reps, res.reps, "Class attribute .reps must sync with result")

if __name__ == '__main__':
    unittest.main()
