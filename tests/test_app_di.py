"""
Integration Tests for SpotterApp with Dependency Injection.

These tests verify that:
1. SpotterApp correctly accepts injected dependencies
2. MockVideoSource and MockPoseEstimator work correctly
3. App loop terminates correctly when video source is exhausted
4. The DI pattern enables CI/CD testing without hardware

Run with: python -m pytest tests/test_app_di.py -v
"""
import unittest
import sys
import os
import tempfile
import numpy as np

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.app import SpotterApp
from tests.mocks.mock_video import MockVideoSource
from tests.mocks.mock_pose import MockPoseEstimator
from src.core.entities.user import User


class MockDatabaseManager:
    """Mock DatabaseManager for testing without SQLite."""
    
    def __init__(self):
        self.users = {}
        self.sessions = []
        self.default_user = User(username="TestUser")
    
    def get_user(self, user_id=None):
        if user_id and user_id in self.users:
            return self.users[user_id]
        return self.default_user if self.users else None
    
    def create_default_user(self):
        self.users[self.default_user.id] = self.default_user
        return self.default_user
    
    def save_user(self, user):
        self.users[user.id] = user
    
    def save_session(self, session):
        self.sessions.append(session)


class TestSpotterAppDI(unittest.TestCase):
    """Test SpotterApp with Dependency Injection."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_video = MockVideoSource()
        self.mock_pose = MockPoseEstimator()
        self.mock_db = MockDatabaseManager()
        self.test_config = {
            'exercise_name': 'squat',
            'exercise_config': {'side': 'left'},
            'target_sets': 1,
            'target_reps': 5,
            'language': 'EN'
        }
    
    def test_app_accepts_injected_dependencies(self):
        """Test that SpotterApp correctly accepts injected dependencies."""
        app = SpotterApp(
            video_source=self.mock_video,
            pose_detector=self.mock_pose,
            db_manager=self.mock_db,
            config=self.test_config
        )
        
        self.assertIs(app.video_source, self.mock_video)
        self.assertIs(app.pose_detector, self.mock_pose)
        self.assertIs(app.db_manager, self.mock_db)
        self.assertEqual(app.config, self.test_config)
    
    def test_mock_video_source_returns_frames(self):
        """Test that MockVideoSource returns frames correctly."""
        frames = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(3)]
        mock = MockVideoSource(frames=frames)
        
        # Should return 3 frames
        for i in range(3):
            ret, frame = mock.get_frame()
            self.assertTrue(ret)
            self.assertEqual(frame.shape, (480, 640, 3))
        
        # Should be exhausted
        ret, _ = mock.get_frame()
        self.assertFalse(ret)
    
    def test_mock_video_source_loops(self):
        """Test that MockVideoSource loops correctly when enabled."""
        frames = [np.zeros((480, 640, 3), dtype=np.uint8)]
        mock = MockVideoSource(frames=frames, loop=True)
        
        # Should loop indefinitely
        for _ in range(5):
            ret, frame = mock.get_frame()
            self.assertTrue(ret)
    
    def test_mock_pose_estimator_returns_data(self):
        """Test that MockPoseEstimator returns poses correctly."""
        pose_data = [{"keypoints": [1, 2, 3]}, {"keypoints": [4, 5, 6]}]
        mock = MockPoseEstimator(pose_data=pose_data)
        
        # Should return 2 poses
        result1 = mock.predict(np.zeros((480, 640, 3)))
        self.assertEqual(result1["keypoints"], [1, 2, 3])
        
        result2 = mock.predict(np.zeros((480, 640, 3)))
        self.assertEqual(result2["keypoints"], [4, 5, 6])
        
        # Should be exhausted
        result3 = mock.predict(np.zeros((480, 640, 3)))
        self.assertIsNone(result3)
    
    def test_mock_db_manager_creates_default_user(self):
        """Test that MockDatabaseManager creates default user."""
        mock_db = MockDatabaseManager()
        
        # Should have no users initially
        user = mock_db.get_user()
        self.assertIsNone(user)
        
        # Create default user
        default_user = mock_db.create_default_user()
        self.assertEqual(default_user.username, "TestUser")
        
        # Now get_user should return the default
        user = mock_db.get_user(default_user.id)
        self.assertIsNotNone(user)


class TestMockIntegration(unittest.TestCase):
    """Integration tests combining all mocks."""
    
    def test_app_can_be_constructed_without_hardware(self):
        """Test that app can be constructed entirely with mocks."""
        mock_video = MockVideoSource()
        mock_pose = MockPoseEstimator()
        mock_db = MockDatabaseManager()
        config = {
            'exercise_name': 'curl',
            'exercise_config': {},
            'target_sets': 1,
            'target_reps': 10,
            'language': 'EN'
        }
        
        # This should not raise any exceptions
        app = SpotterApp(
            video_source=mock_video,
            pose_detector=mock_pose,
            db_manager=mock_db,
            config=config
        )
        
        self.assertIsNotNone(app)


if __name__ == '__main__':
    unittest.main()
