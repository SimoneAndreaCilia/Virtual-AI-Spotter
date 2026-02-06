import unittest
import numpy as np
from src.core.gesture_detector import GestureDetector

class TestGestureDetector(unittest.TestCase):
    def setUp(self):
        self.detector = GestureDetector(stability_frames=5, confidence_threshold=0.6)
        
    def test_thumbs_up_detection(self):
        """Test THUMBS_UP detection with correct COCO keypoints."""
        # Create a mock keypoint array (17 keypoints, 3 values each: x, y, conf)
        # 5:L-Shoulder, 6:R-Shoulder, 9:L-Wrist, 10:R-Wrist
        
        # Scenario: Right arm raised high (Wrist Y < Shoulder Y)
        # Image coordinates: Y increases downwards. So Wrist Y < Shoulder Y means Wrist is ABOVE Shoulder.
        keypoints = np.zeros((17, 3))
        
        # Set all confidences to high
        keypoints[:, 2] = 0.9
        
        # Right Shoulder at (300, 300)
        keypoints[6] = [300, 300, 0.9]
        
        # Right Wrist at (300, 200) -> 100 pixels ABOVE shoulder
        keypoints[10] = [300, 200, 0.9]
        
        # Rest of body is normal...
        
        # Feed this stable pose for N frames
        for _ in range(6):
            gesture = self.detector.detect(keypoints)
            
        self.assertEqual(gesture, "THUMBS_UP")
        
    def test_no_gesture(self):
        """Test no gesture when arms are down."""
        keypoints = np.zeros((17, 3))
        keypoints[:, 2] = 0.9
        
        # Right Shoulder at (300, 300)
        keypoints[6] = [300, 300, 0.9]
        
        # Right Wrist at (300, 400) -> 100 pixels BELOW shoulder
        keypoints[10] = [300, 400, 0.9]
        
        for _ in range(6):
            gesture = self.detector.detect(keypoints)
            
        self.assertIsNone(gesture)

    def test_stability(self):
        """Test that gesture is not returned immediately (stability check)."""
        keypoints = np.zeros((17, 3))
        keypoints[:, 2] = 0.9
        keypoints[6] = [300, 300, 0.9]
        keypoints[10] = [300, 200, 0.9] # Raised
        
        # Frame 1: Should be None
        gesture = self.detector.detect(keypoints)
        self.assertIsNone(gesture)
        
        # Frame 5: Should be confirmed (threshold is 50% of 5 = 2.5 frames)
        for _ in range(4):
             gesture = self.detector.detect(keypoints)
             
        self.assertEqual(gesture, "THUMBS_UP")
