"""
Unit Tests for SessionManager - State Transitions.

Tests the SessionManager state machine:
- Initial state verification
- State transitions: EXERCISE -> REST -> FINISHED
- User input handling (CONTINUE action)
- Session persistence

Run with: python -m pytest tests/test_session_manager.py -v
"""
import unittest
import sys
import os
import numpy as np

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session_manager import SessionManager
from src.core.entities.workout_state import WorkoutState
from src.core.interfaces import Exercise, AnalysisResult
from src.core.protocols import KeypointExtractor


# =============================================================================
# Mock Classes
# =============================================================================

class MockExercise(Exercise):
    """Mock Exercise that allows manual rep control for testing."""
    
    def __init__(self, config=None):
        super().__init__(config or {})
        self.display_name_key = "exercise.mock"
        self.exercise_id = "mock_exercise"
        self._mock_reps = 0
        self._reset_called = False
    
    def process_frame(self, landmarks: np.ndarray, timestamp: float = None) -> AnalysisResult:
        """Returns controlled analysis result."""
        return AnalysisResult(
            reps=self._mock_reps,
            stage="test_stage",
            correction="",
            angle=90.0,
            is_valid=True
        )
    
    def reset(self):
        """Track reset calls."""
        self._reset_called = True
        super().reset()
        self._mock_reps = 0
    
    def set_reps(self, reps: int):
        """Helper to simulate rep completion."""
        self._mock_reps = reps
        self.reps = reps


class MockKeypointExtractor(KeypointExtractor):
    """Mock KeypointExtractor for testing."""
    
    def __init__(self, has_people: bool = True):
        self._has_people = has_people
        self._keypoints = np.random.rand(17, 3) * 0.9 + 0.1
    
    def extract(self, pose_data):
        """Returns mock extraction result."""
        return self._has_people, self._keypoints if self._has_people else None


class MockDatabaseManager:
    """Mock database manager for testing session persistence."""
    
    def __init__(self):
        self.saved_sessions = []
    
    def save_session(self, session):
        """Records session saves for verification."""
        self.saved_sessions.append(session)


# =============================================================================
# Test Classes
# =============================================================================

class TestSessionManagerInitialization(unittest.TestCase):
    """Test SessionManager initialization and initial state."""
    
    def setUp(self):
        self.mock_db = MockDatabaseManager()
        self.mock_exercise = MockExercise()
        self.mock_extractor = MockKeypointExtractor()
    
    def test_initial_state_is_exercise(self):
        """Session should start in EXERCISE state."""
        sm = SessionManager(
            db_manager=self.mock_db,
            user_id=1,
            exercise=self.mock_exercise,
            keypoint_extractor=self.mock_extractor,
            target_sets=3,
            target_reps=10
        )
        
        self.assertEqual(sm.workout_state, WorkoutState.EXERCISE)
    
    def test_initial_set_is_one(self):
        """Session should start at set 1."""
        sm = SessionManager(
            db_manager=self.mock_db,
            user_id=1,
            exercise=self.mock_exercise,
            keypoint_extractor=self.mock_extractor,
            target_sets=3,
            target_reps=10
        )
        
        self.assertEqual(sm.current_set, 1)
    
    def test_session_not_finished_initially(self):
        """Session should not be finished at start."""
        sm = SessionManager(
            db_manager=self.mock_db,
            user_id=1,
            exercise=self.mock_exercise,
            keypoint_extractor=self.mock_extractor,
            target_sets=3,
            target_reps=10
        )
        
        self.assertFalse(sm.is_session_finished())


class TestSessionManagerStateTransitions(unittest.TestCase):
    """Test state transitions: EXERCISE -> REST -> EXERCISE -> FINISHED."""
    
    def setUp(self):
        self.mock_db = MockDatabaseManager()
        self.mock_exercise = MockExercise()
        self.mock_extractor = MockKeypointExtractor()
        
        # 3 sets of 5 reps
        self.sm = SessionManager(
            db_manager=self.mock_db,
            user_id=1,
            exercise=self.mock_exercise,
            keypoint_extractor=self.mock_extractor,
            target_sets=3,
            target_reps=5
        )
    
    def test_complete_set_transitions_to_rest(self):
        """Completing a set (not final) should transition to REST."""
        # Simulate reaching target reps
        self.mock_exercise.set_reps(5)
        
        # Process frame triggers set completion
        self.sm.update(pose_data=None, timestamp=0.0)
        
        self.assertEqual(self.sm.workout_state, WorkoutState.REST)
    
    def test_complete_final_set_transitions_to_finished(self):
        """Completing the final set should transition to FINISHED."""
        # Simulate 3 complete sets
        for set_num in range(1, 4):
            self.mock_exercise.set_reps(5)
            self.sm.update(pose_data=None, timestamp=float(set_num))
            
            if set_num < 3:
                # Continue to next set
                self.sm.handle_user_input('CONTINUE')
        
        self.assertEqual(self.sm.workout_state, WorkoutState.FINISHED)
        self.assertTrue(self.sm.is_session_finished())
    
    def test_continue_from_rest_increments_set(self):
        """CONTINUE from REST should increment set and return to EXERCISE."""
        # Complete first set
        self.mock_exercise.set_reps(5)
        self.sm.update(pose_data=None, timestamp=0.0)
        self.assertEqual(self.sm.workout_state, WorkoutState.REST)
        self.assertEqual(self.sm.current_set, 1)
        
        # Continue
        self.sm.handle_user_input('CONTINUE')
        
        self.assertEqual(self.sm.workout_state, WorkoutState.EXERCISE)
        self.assertEqual(self.sm.current_set, 2)
    
    def test_continue_ignored_in_exercise_state(self):
        """CONTINUE should be ignored when in EXERCISE state."""
        initial_set = self.sm.current_set
        initial_state = self.sm.workout_state
        
        # Try to continue while exercising
        self.sm.handle_user_input('CONTINUE')
        
        self.assertEqual(self.sm.current_set, initial_set)
        self.assertEqual(self.sm.workout_state, initial_state)
    
    def test_continue_ignored_in_finished_state(self):
        """CONTINUE should be ignored when in FINISHED state."""
        # Complete all sets
        for _ in range(3):
            self.mock_exercise.set_reps(5)
            self.sm.update(pose_data=None, timestamp=0.0)
            if self.sm.workout_state == WorkoutState.REST:
                self.sm.handle_user_input('CONTINUE')
        
        self.assertEqual(self.sm.workout_state, WorkoutState.FINISHED)
        
        # Try to continue after finished
        self.sm.handle_user_input('CONTINUE')
        
        self.assertEqual(self.sm.workout_state, WorkoutState.FINISHED)


class TestSessionManagerExerciseReset(unittest.TestCase):
    """Test exercise reset behavior after set completion."""
    
    def setUp(self):
        self.mock_db = MockDatabaseManager()
        self.mock_exercise = MockExercise()
        self.mock_extractor = MockKeypointExtractor()
        
        self.sm = SessionManager(
            db_manager=self.mock_db,
            user_id=1,
            exercise=self.mock_exercise,
            keypoint_extractor=self.mock_extractor,
            target_sets=3,
            target_reps=5
        )
    
    def test_exercise_reset_on_set_completion(self):
        """Exercise logic should reset after completing a set."""
        self.mock_exercise.set_reps(5)
        self.sm.update(pose_data=None, timestamp=0.0)
        
        self.assertTrue(self.mock_exercise._reset_called)


class TestSessionManagerPersistence(unittest.TestCase):
    """Test session data persistence."""
    
    def setUp(self):
        self.mock_db = MockDatabaseManager()
        self.mock_exercise = MockExercise()
        self.mock_extractor = MockKeypointExtractor()
        
        self.sm = SessionManager(
            db_manager=self.mock_db,
            user_id=1,
            exercise=self.mock_exercise,
            keypoint_extractor=self.mock_extractor,
            target_sets=2,
            target_reps=3
        )
    
    def test_session_saved_on_finish(self):
        """Session should be saved to database when workout finishes."""
        # Complete all sets
        for _ in range(2):
            self.mock_exercise.set_reps(3)
            self.sm.update(pose_data=None, timestamp=0.0)
            if self.sm.workout_state == WorkoutState.REST:
                self.sm.handle_user_input('CONTINUE')
        
        self.assertEqual(len(self.mock_db.saved_sessions), 1)
    
    def test_save_session_method(self):
        """save_session() should trigger end_session and database save."""
        self.sm.save_session()
        
        self.assertEqual(len(self.mock_db.saved_sessions), 1)
    
    def test_end_session_only_saves_once(self):
        """Multiple end_session() calls should only save once."""
        self.sm.end_session()
        self.sm.end_session()
        self.sm.end_session()
        
        self.assertEqual(len(self.mock_db.saved_sessions), 1)


class TestSessionManagerUIState(unittest.TestCase):
    """Test UIState output from update()."""
    
    def setUp(self):
        self.mock_db = MockDatabaseManager()
        self.mock_exercise = MockExercise()
        self.mock_extractor = MockKeypointExtractor()
        
        self.sm = SessionManager(
            db_manager=self.mock_db,
            user_id=1,
            exercise=self.mock_exercise,
            keypoint_extractor=self.mock_extractor,
            target_sets=3,
            target_reps=10
        )
    
    def test_update_returns_ui_state(self):
        """update() should return a UIState object."""
        ui_state = self.sm.update(pose_data=None, timestamp=0.0)
        
        self.assertIsNotNone(ui_state)
        self.assertEqual(ui_state.target_reps, 10)
        self.assertEqual(ui_state.target_sets, 3)
        self.assertEqual(ui_state.current_set, 1)
    
    def test_ui_state_reflects_workout_state(self):
        """UIState.workout_state should reflect current state."""
        # Initial state
        ui_state = self.sm.update(pose_data=None, timestamp=0.0)
        self.assertEqual(ui_state.workout_state, "EXERCISE")
        
        # After completing set
        self.mock_exercise.set_reps(10)
        ui_state = self.sm.update(pose_data=None, timestamp=1.0)
        self.assertEqual(ui_state.workout_state, "REST")


if __name__ == '__main__':
    unittest.main()
