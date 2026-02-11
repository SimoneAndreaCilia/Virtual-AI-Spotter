import unittest
from unittest.mock import MagicMock
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.session_manager import SessionManager, WorkoutState
from src.core.entities.ui_state import UIState

class TestSessionManagerRestState(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_exercise = MagicMock()
        self.mock_exercise.display_name_key = "test_exercise"
        self.mock_exercise.stage = "waiting" # Default reset state
        self.mock_extractor = MagicMock()
        self.mock_extractor.extract.return_value = (True, [[0,0,0]])
        
        self.manager = SessionManager(
            db_manager=self.mock_db,
            user_id=1,
            exercise=self.mock_exercise,
            keypoint_extractor=self.mock_extractor,
            target_sets=3,
            target_reps=10
        )

    def test_rest_state_ui_is_finished(self):
        # Set manager to REST mode
        self.manager.workout_state = WorkoutState.REST
        
        # Calling update should return UIState with state="finished"
        # even if exercise logic says "waiting"
        ui_state = self.manager.update(None, 0.0)
        
        self.assertEqual(ui_state.state, "finished")
        self.assertNotEqual(ui_state.state, "waiting")

if __name__ == '__main__':
    unittest.main()
