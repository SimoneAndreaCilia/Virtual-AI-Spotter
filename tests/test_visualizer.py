"""
Tests for Visualizer and its sub-renderers.

Tests cover:
- SkeletonRenderer: skeleton drawing and angle arcs
- DashboardRenderer: HUD panel and feedback
- OverlayRenderer: full-screen messages
- Visualizer: facade delegation

Run with: python -m pytest tests/test_visualizer.py -v
"""
import unittest
import sys
import os
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ui.visualizer import Visualizer
from src.ui.skeleton_renderer import SkeletonRenderer
from src.ui.dashboard_renderer import DashboardRenderer
from src.ui.overlay_renderer import OverlayRenderer
from tests.helpers import create_dummy_frame, create_mock_keypoints, create_ui_state


class TestSkeletonRenderer(unittest.TestCase):
    """Tests for SkeletonRenderer class."""
    
    def setUp(self):
        self.renderer = SkeletonRenderer()
        self.frame = create_dummy_frame()
    
    def test_draw_with_valid_keypoints(self):
        """Test that draw() modifies the frame with valid keypoints."""
        keypoints = create_mock_keypoints()
        original_sum = self.frame.sum()
        
        self.renderer.draw(self.frame, keypoints)
        
        # Frame should be modified (pixels drawn)
        self.assertNotEqual(self.frame.sum(), original_sum)
    
    def test_draw_with_empty_keypoints(self):
        """Test that draw() handles empty keypoints gracefully."""
        original_frame = self.frame.copy()
        
        self.renderer.draw(self.frame, None)
        self.renderer.draw(self.frame, [])
        
        # Frame should be unchanged
        np.testing.assert_array_equal(self.frame, original_frame)
    
    def test_draw_with_invalid_keypoints(self):
        """Test that draw() handles keypoints at (0,0) gracefully."""
        keypoints = np.zeros((17, 3))  # All zeros
        original_frame = self.frame.copy()
        
        self.renderer.draw(self.frame, keypoints)
        
        # Should not crash, frame mostly unchanged
        # (only valid points > 0 are drawn)
    
    def test_draw_angle_arc(self):
        """Test that draw_angle_arc() draws text on frame."""
        original_sum = self.frame.sum()
        
        self.renderer.draw_angle_arc(self.frame, (200, 200), 90.5)
        
        # Frame should be modified (text drawn)
        self.assertNotEqual(self.frame.sum(), original_sum)
    
    def test_draw_angle_arc_at_zero(self):
        """Test that draw_angle_arc() skips when center is at origin."""
        original_frame = self.frame.copy()
        
        self.renderer.draw_angle_arc(self.frame, (0, 100), 45.0)
        
        # Frame should be unchanged (skipped due to x=0)
        np.testing.assert_array_equal(self.frame, original_frame)


class TestDashboardRenderer(unittest.TestCase):
    """Tests for DashboardRenderer class."""
    
    def setUp(self):
        self.renderer = DashboardRenderer()
        self.frame = create_dummy_frame()
    
    def test_draw_dashboard_basic(self):
        """Test that draw() renders the dashboard without crashing."""
        original_sum = self.frame.sum()
        
        self.renderer.draw(
            self.frame,
            exercise_name="Bicep Curl",
            reps=5,
            target_reps=8,
            current_set=2,
            target_sets=3,
            state="up",
            feedback_key=""
        )
        
        # Frame should be modified
        self.assertNotEqual(self.frame.sum(), original_sum)
    
    def test_draw_with_feedback_error(self):
        """Test that error feedback renders in red."""
        self.renderer.draw(
            self.frame,
            exercise_name="Squat",
            reps=0,
            target_reps=8,
            current_set=1,
            target_sets=3,
            state="start",
            feedback_key="err_body_not_visible"
        )
        # Should not crash, feedback displayed
    
    def test_draw_with_feedback_success(self):
        """Test that success feedback renders in green."""
        self.renderer.draw(
            self.frame,
            exercise_name="PushUp",
            reps=8,
            target_reps=8,
            current_set=1,
            target_sets=3,
            state="pushup_up",
            feedback_key="good_form"
        )
        # Should not crash, feedback displayed
    
    def test_draw_with_long_state_text(self):
        """Test that long state text is truncated properly."""
        self.renderer.draw(
            self.frame,
            exercise_name="Test",
            reps=0,
            target_reps=10,
            current_set=1,
            target_sets=1,
            state="some_very_long_state_name_that_exceeds_limits",
            feedback_key=""
        )
        # Should not crash, text truncated


class TestOverlayRenderer(unittest.TestCase):
    """Tests for OverlayRenderer class."""
    
    def setUp(self):
        self.renderer = OverlayRenderer()
        self.frame = create_dummy_frame()
    
    def test_draw_message_modifies_frame(self):
        """Test that draw_message() creates a visible overlay."""
        # Fill frame with white first
        self.frame.fill(255)
        original_sum = self.frame.sum()
        
        self.renderer.draw_message(self.frame, "REST", "Press SPACE")
        
        # Frame should be darker (overlay applied)
        self.assertLess(self.frame.sum(), original_sum)
    
    def test_draw_message_with_special_chars(self):
        """Test that draw_message handles unicode characters."""
        self.renderer.draw_message(self.frame, "PAUSA", "Premi SPAZIO per continuare")
        # Should not crash


class TestVisualizerFacade(unittest.TestCase):
    """Tests for Visualizer facade class."""
    
    def setUp(self):
        self.visualizer = Visualizer()
        self.frame = create_dummy_frame()
    
    def test_init_creates_sub_renderers(self):
        """Test that Visualizer creates all sub-renderers."""
        self.assertIsInstance(self.visualizer.skeleton, SkeletonRenderer)
        self.assertIsInstance(self.visualizer.dashboard, DashboardRenderer)
        self.assertIsInstance(self.visualizer.overlay, OverlayRenderer)
    
    def test_draw_skeleton_delegates(self):
        """Test that draw_skeleton() delegates to SkeletonRenderer."""
        keypoints = create_mock_keypoints()
        original_sum = self.frame.sum()
        
        self.visualizer.draw_skeleton(self.frame, keypoints)
        
        self.assertNotEqual(self.frame.sum(), original_sum)
    
    def test_draw_dashboard_delegates(self):
        """Test that draw_dashboard() delegates to DashboardRenderer."""
        original_sum = self.frame.sum()
        
        self.visualizer.draw_dashboard(
            self.frame, "Test", 1, 8, 1, 3, "start", ""
        )
        
        self.assertNotEqual(self.frame.sum(), original_sum)
    
    def test_draw_dashboard_from_state_active(self):
        """Test draw_dashboard_from_state with ACTIVE workout state."""
        state = create_ui_state(workout_state="ACTIVE")
        
        result = self.visualizer.draw_dashboard_from_state(self.frame, state)
        
        self.assertIs(result, self.frame)
    
    def test_draw_dashboard_from_state_rest(self):
        """Test draw_dashboard_from_state shows REST overlay."""
        self.frame.fill(255)  # White frame
        state = create_ui_state(workout_state="REST")
        original_sum = self.frame.sum()
        
        self.visualizer.draw_dashboard_from_state(self.frame, state)
        
        # Overlay should darken the frame
        self.assertLess(self.frame.sum(), original_sum)
    
    def test_draw_dashboard_from_state_finished(self):
        """Test draw_dashboard_from_state shows FINISHED overlay."""
        self.frame.fill(255)
        state = create_ui_state(workout_state="FINISHED")
        original_sum = self.frame.sum()
        
        self.visualizer.draw_dashboard_from_state(self.frame, state)
        
        self.assertLess(self.frame.sum(), original_sum)
    
    def test_draw_dashboard_from_state_with_keypoints(self):
        """Test that keypoints are drawn when present in state."""
        keypoints = create_mock_keypoints()
        state = create_ui_state(keypoints=keypoints)
        original_sum = self.frame.sum()
        
        self.visualizer.draw_dashboard_from_state(self.frame, state)
        
        self.assertNotEqual(self.frame.sum(), original_sum)


class TestStateDisplay(unittest.TestCase):
    """
    Tests get_state_display() mapping for each exercise.
    
    Verifies pure data (label_key, color, category) without rendering.
    """

    def _assert_valid_display(self, info, expected_key, expected_category):
        """Shared assertions for any StateDisplayInfo."""
        from src.core.interfaces import StateDisplayInfo
        self.assertIsInstance(info, StateDisplayInfo)
        self.assertEqual(info.label_key, expected_key)
        self.assertEqual(len(info.color), 3)  # Valid BGR tuple
        self.assertIn(info.category, ("up", "down", "neutral"))
        self.assertEqual(info.category, expected_category)

    # --- Base class defaults ---

    def test_base_start(self):
        from src.exercises.curl import BicepCurl
        ex = BicepCurl({"side": "right"})
        info = ex.get_state_display("start")
        self._assert_valid_display(info, "state_start", "neutral")

    def test_base_finished(self):
        from src.exercises.curl import BicepCurl
        ex = BicepCurl({"side": "right"})
        info = ex.get_state_display("finished")
        self._assert_valid_display(info, "state_finished", "neutral")

    def test_base_unknown_fallback(self):
        from src.exercises.curl import BicepCurl
        ex = BicepCurl({"side": "right"})
        info = ex.get_state_display("invalid_state_xyz")
        self._assert_valid_display(info, "state_unknown", "neutral")

    # --- BicepCurl ---

    def test_curl_up(self):
        from src.exercises.curl import BicepCurl
        ex = BicepCurl({"side": "right"})
        info = ex.get_state_display("curl_up")
        self._assert_valid_display(info, "curl_state_up", "up")

    def test_curl_down(self):
        from src.exercises.curl import BicepCurl
        ex = BicepCurl({"side": "right"})
        info = ex.get_state_display("curl_down")
        self._assert_valid_display(info, "curl_state_down", "down")

    # --- Squat ---

    def test_squat_up(self):
        from src.exercises.squat import Squat
        ex = Squat({"side": "right"})
        info = ex.get_state_display("squat_up")
        self._assert_valid_display(info, "squat_state_up", "up")

    def test_squat_down(self):
        from src.exercises.squat import Squat
        ex = Squat({"side": "right"})
        info = ex.get_state_display("squat_down")
        self._assert_valid_display(info, "squat_state_down", "down")

    # --- PushUp ---

    def test_pushup_up(self):
        from src.exercises.pushup import PushUp
        ex = PushUp({"side": "right"})
        info = ex.get_state_display("pushup_up")
        self._assert_valid_display(info, "pushup_state_up", "up")

    def test_pushup_down(self):
        from src.exercises.pushup import PushUp
        ex = PushUp({"side": "right"})
        info = ex.get_state_display("pushup_down")
        self._assert_valid_display(info, "pushup_state_down", "down")

    # --- Plank ---

    def test_plank_waiting(self):
        from src.exercises.plank import Plank
        ex = Plank({"side": "left"})
        info = ex.get_state_display("waiting")
        self._assert_valid_display(info, "plank_state_waiting", "neutral")

    def test_plank_countdown(self):
        from src.exercises.plank import Plank
        ex = Plank({"side": "left"})
        info = ex.get_state_display("countdown")
        self._assert_valid_display(info, "plank_state_countdown", "neutral")

    def test_plank_active(self):
        from src.exercises.plank import Plank
        ex = Plank({"side": "left"})
        info = ex.get_state_display("active")
        self._assert_valid_display(info, "plank_phase_label", "up")

    def test_plank_finished(self):
        from src.exercises.plank import Plank
        ex = Plank({"side": "left"})
        info = ex.get_state_display("finished")
        self._assert_valid_display(info, "plank_state_finished", "neutral")


class TestStateDisplayFlow(unittest.TestCase):
    """Tests UIState → DashboardRenderer integration with state_display."""

    def setUp(self):
        self.visualizer = Visualizer()
        self.frame = create_dummy_frame()

    def test_state_display_injected_into_dashboard(self):
        """state_display flows from UIState to DashboardRenderer without crash."""
        from src.exercises.curl import BicepCurl
        curl = BicepCurl({"side": "right"})
        display = curl.get_state_display("curl_up")

        state = create_ui_state(
            exercise_name="Bicep Curl",
            state="curl_up",
            state_display=display
        )
        original_sum = self.frame.sum()

        result = self.visualizer.draw_dashboard_from_state(self.frame, state)

        self.assertIs(result, self.frame)
        self.assertNotEqual(self.frame.sum(), original_sum)

    def test_state_display_none_fallback(self):
        """state_display=None falls back to 'state_unknown' without crash."""
        state = create_ui_state(
            state="some_unknown_state",
            state_display=None
        )
        original_sum = self.frame.sum()

        result = self.visualizer.draw_dashboard_from_state(self.frame, state)

        self.assertIs(result, self.frame)
        self.assertNotEqual(self.frame.sum(), original_sum)


if __name__ == "__main__":
    unittest.main()
