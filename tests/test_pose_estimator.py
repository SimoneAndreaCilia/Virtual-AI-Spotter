"""
Tests for PoseEstimator and MockPoseEstimator.

Tests cover:
- MockPoseEstimator returns correct sequence behavior
- MockPoseEstimator loop functionality
- Integration with test helpers

Run with: python tests/test_pose_estimator.py -v
"""
import unittest
import sys
import os
import numpy as np
from dataclasses import dataclass
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.mocks.mock_pose import MockPoseEstimator
from tests.helpers import create_dummy_frame


# Mock YOLO-like result structure for testing
@dataclass
class MockKeypoints:
    """Simulates YOLO keypoints structure."""
    xy: np.ndarray
    conf: np.ndarray


@dataclass
class MockResult:
    """Simulates a single YOLO detection result."""
    keypoints: MockKeypoints


def create_mock_yolo_result(num_points: int = 17) -> MockResult:
    """Creates a mock YOLO result with realistic keypoints."""
    xy = np.random.rand(1, num_points, 2) * 400 + 100  # (1, 17, 2)
    conf = np.full((1, num_points), 0.9)  # (1, 17)
    return MockResult(keypoints=MockKeypoints(xy=xy, conf=conf))


class TestMockPoseEstimatorBasic(unittest.TestCase):
    """Tests for basic MockPoseEstimator functionality."""
    
    def setUp(self):
        self.frame = create_dummy_frame()
    
    def test_default_returns_none(self):
        """Test that default MockPoseEstimator returns None."""
        estimator = MockPoseEstimator()
        
        result = estimator.predict(self.frame)
        
        self.assertIsNone(result)
    
    def test_returns_none_when_exhausted(self):
        """Test that estimator returns None after exhausting data."""
        estimator = MockPoseEstimator(pose_data=["result1"])
        
        estimator.predict(self.frame)  # First call consumes data
        result = estimator.predict(self.frame)  # Second call exhausted
        
        self.assertIsNone(result)
    
    def test_reset_restarts_sequence(self):
        """Test that reset() restarts the sequence."""
        estimator = MockPoseEstimator(pose_data=["first", "second"])
        
        estimator.predict(self.frame)  # Gets "first"
        estimator.reset()
        result = estimator.predict(self.frame)
        
        self.assertEqual(result, "first")


class TestMockPoseEstimatorWithData(unittest.TestCase):
    """Tests for MockPoseEstimator with custom pose data."""
    
    def setUp(self):
        self.frame = create_dummy_frame()
        self.mock_result = create_mock_yolo_result()
    
    def test_returns_provided_data(self):
        """Test that estimator returns provided pose data."""
        estimator = MockPoseEstimator(pose_data=[self.mock_result])
        
        result = estimator.predict(self.frame)
        
        self.assertEqual(result, self.mock_result)
    
    def test_returns_sequence_in_order(self):
        """Test that data is returned in sequence order."""
        data = ["first", "second", "third"]
        estimator = MockPoseEstimator(pose_data=data)
        
        results = [estimator.predict(self.frame) for _ in range(3)]
        
        self.assertEqual(results, data)
    
    def test_loop_restarts_sequence(self):
        """Test that loop=True restarts from beginning."""
        data = ["a", "b"]
        estimator = MockPoseEstimator(pose_data=data, loop=True)
        
        results = [estimator.predict(self.frame) for _ in range(5)]
        
        self.assertEqual(results, ["a", "b", "a", "b", "a"])


class TestMockPoseEstimatorKeypoints(unittest.TestCase):
    """Tests for MockPoseEstimator with realistic keypoints."""
    
    def setUp(self):
        self.frame = create_dummy_frame()
        self.mock_result = create_mock_yolo_result()
    
    def test_keypoints_have_xy_attribute(self):
        """Test that mock keypoints have xy coordinates."""
        estimator = MockPoseEstimator(pose_data=[self.mock_result])
        
        result = estimator.predict(self.frame)
        
        self.assertTrue(hasattr(result.keypoints, 'xy'))
    
    def test_keypoints_have_correct_shape(self):
        """Test that keypoints have shape (1, 17, 2)."""
        estimator = MockPoseEstimator(pose_data=[self.mock_result])
        
        result = estimator.predict(self.frame)
        
        self.assertEqual(result.keypoints.xy.shape, (1, 17, 2))
    
    def test_keypoints_have_confidence(self):
        """Test that keypoints have confidence values."""
        estimator = MockPoseEstimator(pose_data=[self.mock_result])
        
        result = estimator.predict(self.frame)
        
        self.assertTrue(hasattr(result.keypoints, 'conf'))
        self.assertEqual(result.keypoints.conf.shape, (1, 17))


if __name__ == "__main__":
    unittest.main()
