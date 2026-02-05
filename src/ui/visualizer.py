"""
Visualizer - Facade for rendering workout UI components.

This class composes specialized renderers:
- SkeletonRenderer: Body pose skeleton
- DashboardRenderer: HUD/stats panel
- OverlayRenderer: Full-screen messages

This follows the Facade pattern - clients use Visualizer,
which delegates to the appropriate renderer.
"""
from config.translation_strings import i18n
from src.ui.skeleton_renderer import SkeletonRenderer
from src.ui.dashboard_renderer import DashboardRenderer
from src.ui.overlay_renderer import OverlayRenderer


class Visualizer:
    """
    Facade for all visualization components.
    Composes specialized renderers for skeleton, dashboard, and overlays.
    """
    
    def __init__(self):
        """Initialize all sub-renderers."""
        self.skeleton = SkeletonRenderer()
        self.dashboard = DashboardRenderer()
        self.overlay = OverlayRenderer()

    def draw_skeleton(self, frame, keypoints) -> None:
        """Draws the pose skeleton on the frame."""
        self.skeleton.draw(frame, keypoints)

    def draw_dashboard(self, frame, exercise_name, reps, target_reps,
                       current_set, target_sets, state, feedback_key) -> None:
        """Draws the workout dashboard/HUD panel."""
        self.dashboard.draw(
            frame, exercise_name, reps, target_reps,
            current_set, target_sets, state, feedback_key
        )

    def draw_angle_arc(self, frame, center, angle_val) -> None:
        """Draws the angle value near a joint."""
        self.skeleton.draw_angle_arc(frame, center, angle_val)

    def draw_dashboard_from_state(self, frame, state):
        """
        Adapter method to draw dashboard using the UIState dataclass.
        
        Args:
            frame: OpenCV image
            state: UIState dataclass with all rendering info
            
        Returns:
            The modified frame
        """
        # Draw skeleton if keypoints exist
        if state.keypoints is not None:
            self.skeleton.draw(frame, state.keypoints)

        # Draw dashboard
        self.dashboard.draw(
            frame,
            exercise_name=state.exercise_name,
            reps=state.reps,
            target_reps=state.target_reps,
            current_set=state.current_set,
            target_sets=state.target_sets,
            state=state.state,
            feedback_key=state.feedback_key
        )
        
        # Draw overlays for REST/FINISHED states
        if state.workout_state == "REST":
            self.overlay.draw_message(
                frame,
                i18n.get("ui_rest_title"),
                i18n.get("ui_rest_subtitle")
            )
        elif state.workout_state == "FINISHED":
            self.overlay.draw_message(
                frame,
                i18n.get("ui_finish_title"),
                i18n.get("ui_finish_subtitle")
            )
            
        return frame
