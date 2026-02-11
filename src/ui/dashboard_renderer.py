"""
DashboardRenderer - Handles HUD/Dashboard display and feedback.

Single Responsibility: Render workout information panel and dynamic feedback.
"""
import cv2
import numpy as np
from config.settings import COLORS
from config.translation_strings import i18n


# Layout Constants (extracted magic numbers)
DASHBOARD_MARGIN = 20
DASHBOARD_WIDTH = 300
DASHBOARD_HEIGHT = 250
CORNER_RADIUS = 15
FEEDBACK_Y_POS = 50


class DashboardRenderer:
    """Renders the workout dashboard (HUD) with stats and feedback."""
    
    def draw(self, frame, exercise_name: str, reps: int, target_reps: int,
             current_set: int, target_sets: int, state: str, feedback_key: str,
             is_time_based: bool = False) -> None:
        """
        Draws the information panel (HUD) with set/rep counts and state.
        
        Args:
            frame: OpenCV image
            exercise_name: Name of current exercise
            reps: Current rep count
            target_reps: Target reps per set
            current_set: Current set number
            target_sets: Target total sets
            state: Current exercise state (e.g., "up", "down")
            feedback_key: i18n key for feedback message
        """
        h, w = frame.shape[:2]
        
        # Layout configuration
        x1, y1 = DASHBOARD_MARGIN, DASHBOARD_MARGIN
        x2, y2 = x1 + DASHBOARD_WIDTH, y1 + DASHBOARD_HEIGHT
        
        # Draw rounded background
        self._draw_rounded_rect(
            frame, (x1, y1), (x2, y2), COLORS["OVERLAY_BG"],
            radius=CORNER_RADIUS, alpha=0.7,
            border_color=COLORS["YELLOW"], border_thickness=1
        )

        # Horizontal separators (4 sections)
        row_h = DASHBOARD_HEIGHT // 4
        y_line1 = y1 + row_h
        y_line2 = y1 + (row_h * 2)
        y_line3 = y1 + (row_h * 3)
        
        cv2.line(frame, (x1 + 10, y_line1), (x2 - 10, y_line1), COLORS["WHITE"], 1)
        cv2.line(frame, (x1 + 10, y_line2), (x2 - 10, y_line2), COLORS["WHITE"], 1)
        cv2.line(frame, (x1 + 10, y_line3), (x2 - 10, y_line3), COLORS["WHITE"], 1)

        font_label = cv2.FONT_HERSHEY_SIMPLEX
        font_val = cv2.FONT_HERSHEY_DUPLEX
        
        # --- ROW 1: EXERCISE TITLE (centered) ---
        title_text = exercise_name.upper()
        title_font_scale = 0.9
        title_size = cv2.getTextSize(title_text, font_val, title_font_scale, 2)[0]
        title_x = x1 + (DASHBOARD_WIDTH - title_size[0]) // 2
        cv2.putText(frame, title_text, (title_x, y_line1 - 25), font_val, title_font_scale, COLORS["YELLOW"], 2, cv2.LINE_AA)

        # --- ROW 2: SETS ---
        lbl_set = i18n.get("ui_set").upper()
        cv2.putText(frame, lbl_set, (x1 + 20, y_line2 - 25), font_label, 0.7, COLORS["WHITE"], 1, cv2.LINE_AA)
        
        set_str = f"{current_set} / {target_sets}"
        set_size = cv2.getTextSize(set_str, font_val, 1.2, 2)[0]
        set_x = x2 - 20 - set_size[0]
        
        cv2.putText(frame, set_str, (set_x + 2, y_line2 - 22), font_val, 1.2, COLORS["BLACK"], 4, cv2.LINE_AA)
        cv2.putText(frame, set_str, (set_x, y_line2 - 24), font_val, 1.2, COLORS["YELLOW"], 2, cv2.LINE_AA)

        # --- ROW 3: REPS or TIME ---
        if is_time_based:
             lbl_reps = "TIME" # Should be translated ideally
             # Format seconds to MM:SS
             minutes = reps // 60
             seconds = reps % 60
             reps_str = f"{minutes:02}:{seconds:02}"
             col_reps = COLORS["WHITE"] 
        else:
             lbl_reps = i18n.get("ui_reps")
             reps_str = f"{reps} / {target_reps}"
             col_reps = COLORS["GREEN"] if reps >= target_reps else COLORS["WHITE"]
        cv2.putText(frame, lbl_reps, (x1 + 20, y_line3 - 25), font_label, 0.7, COLORS["WHITE"], 1, cv2.LINE_AA)
        
        # reps_str is already set above
        
        # Calculate position for value
        reps_size = cv2.getTextSize(reps_str, font_val, 1.2, 2)[0]
        reps_x = x2 - 20 - reps_size[0]
        
        cv2.putText(frame, reps_str, (reps_x + 2, y_line3 - 22), font_val, 1.2, COLORS["BLACK"], 4, cv2.LINE_AA)
        cv2.putText(frame, reps_str, (reps_x, y_line3 - 24), font_val, 1.2, col_reps, 2, cv2.LINE_AA)

        # --- ROW 4: STATE ---
        lbl_state = i18n.get("ui_state")
        cv2.putText(frame, lbl_state, (x1 + 20, y2 - 25), font_label, 0.7, COLORS["WHITE"], 1, cv2.LINE_AA)

        # State mapping
        state_key_map = {
            "curl_up": ("curl_state_up", COLORS["GREEN"], "up"),
            "curl_down": ("curl_state_down", (0, 165, 255), "down"),
            "squat_up": ("squat_state_up", COLORS["GREEN"], "up"),
            "squat_down": ("squat_state_down", (0, 165, 255), "down"),
            "pushup_up": ("pushup_state_up", COLORS["GREEN"], "up"),
            "pushup_down": ("pushup_state_down", (0, 165, 255), "down"),
            # Plank States
            "waiting": ("plank_state_waiting", COLORS["YELLOW"], "neutral"),
            "countdown": ("plank_state_countdown", COLORS["YELLOW"], "neutral"),
            "active": ("plank_phase_label", COLORS["GREEN"], "up"), # User requested "Plank Phase" when active
            "finished": ("plank_state_finished", COLORS["GREEN"], "neutral"),
            "start": ("state_start", COLORS["WHITE"], "neutral"),
            "unknown": ("state_unknown", COLORS["GRAY"], "neutral")
        }
        
        tr_key, state_color, _ = state_key_map.get(state, ("state_unknown", COLORS["GRAY"], "neutral"))
        state_text = i18n.get(tr_key)
        if state_text.startswith("MISSING"):
            state_text = state.upper()
        
        # Truncate if too long
        if len(state_text) > 20:
            state_text = state_text[:20] + "..."
        
        # Calculate position to avoid overlap with label
        label_size = cv2.getTextSize(lbl_state, font_label, 0.7, 1)[0]
        label_end_x = x1 + 20 + label_size[0]
        val_end_x = x2 - 20
        max_val_width = val_end_x - (label_end_x + 20)
        
        font_scale_st = 0.9
        state_size = cv2.getTextSize(state_text, font_val, font_scale_st, 2)[0]
        
        while state_size[0] > max_val_width and font_scale_st > 0.5:
            font_scale_st -= 0.1
            state_size = cv2.getTextSize(state_text, font_val, font_scale_st, 2)[0]
            
        st_x = val_end_x - state_size[0]
        
        cv2.putText(frame, state_text, (st_x + 2, y2 - 22), font_val, font_scale_st, COLORS["BLACK"], 4, cv2.LINE_AA)
        cv2.putText(frame, state_text, (st_x, y2 - 24), font_val, font_scale_st, state_color, 2, cv2.LINE_AA)

        # --- Dynamic Feedback ---
        self._draw_dynamic_feedback(frame, feedback_key, w)

    def _draw_rounded_rect(self, img, pt1, pt2, color, radius=15, alpha=0.5,
                           border_color=None, border_thickness=1) -> None:
        """
        Draws a rounded rectangle with semi-transparent fill and optional border.
        Optimized: uses ROI instead of copying entire image.
        """
        x1, y1 = pt1
        x2, y2 = pt2
        
        # Validate and clamp coordinates
        h_img, w_img = img.shape[:2]
        x1 = max(0, min(x1, w_img))
        y1 = max(0, min(y1, h_img))
        x2 = max(0, min(x2, w_img))
        y2 = max(0, min(y2, h_img))
        
        if x1 >= x2 or y1 >= y2:
            return

        roi_w = x2 - x1
        roi_h = y2 - y1
        
        # Extract ROI
        roi = img[y1:y2, x1:x2]
        overlay_roi = roi.copy()
        
        # Draw rounded corners
        cv2.circle(overlay_roi, (radius, radius), radius, color, -1)
        cv2.circle(overlay_roi, (radius, roi_h - radius), radius, color, -1)
        cv2.circle(overlay_roi, (roi_w - radius, radius), radius, color, -1)
        cv2.circle(overlay_roi, (roi_w - radius, roi_h - radius), radius, color, -1)
        
        # Fill center rectangles
        cv2.rectangle(overlay_roi, (radius, 0), (roi_w - radius, roi_h), color, -1)
        cv2.rectangle(overlay_roi, (0, radius), (roi_w, roi_h - radius), color, -1)
        
        # Alpha blend
        cv2.addWeighted(overlay_roi, alpha, roi, 1 - alpha, 0, roi)
        img[y1:y2, x1:x2] = roi
        
        # Draw border
        if border_color and border_thickness > 0:
            cv2.line(img, (x1+radius, y1), (x2-radius, y1), border_color, border_thickness)
            cv2.line(img, (x1+radius, y2), (x2-radius, y2), border_color, border_thickness)
            cv2.line(img, (x1, y1+radius), (x1, y2-radius), border_color, border_thickness)
            cv2.line(img, (x2, y1+radius), (x2, y2-radius), border_color, border_thickness)
            
            cv2.ellipse(img, (x1+radius, y1+radius), (radius, radius), 180, 0, 90, border_color, border_thickness)
            cv2.ellipse(img, (x1+radius, y2-radius), (radius, radius), 90, 0, 90, border_color, border_thickness)
            cv2.ellipse(img, (x2-radius, y1+radius), (radius, radius), 270, 0, 90, border_color, border_thickness)
            cv2.ellipse(img, (x2-radius, y2-radius), (radius, radius), 0, 0, 90, border_color, border_thickness)

    def _draw_dynamic_feedback(self, frame, feedback_key: str, width: int) -> None:
        """
        Draws the corrective feedback message at the top-center of the screen.
        Color logic: "err" -> Red, "good/perfect" -> Green, else -> Yellow
        """
        if not feedback_key:
            return

        text = i18n.get(feedback_key)
        
        # Determine color based on feedback type
        if "err" in feedback_key or "Extension" in text:
            color = COLORS["RED"]
        elif "good" in feedback_key or "perfect" in feedback_key:
            color = COLORS["GREEN"]
        else:
            color = COLORS["YELLOW"]

        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 1.0
        thickness = 2
        
        text_size = cv2.getTextSize(text, font, scale, thickness)[0]
        text_x = (width - text_size[0]) // 2
        text_y = FEEDBACK_Y_POS

        # Shadow for readability
        cv2.putText(frame, text, (text_x + 2, text_y + 2), font, scale, COLORS["BLACK"], thickness + 2)
        cv2.putText(frame, text, (text_x, text_y), font, scale, color, thickness)
