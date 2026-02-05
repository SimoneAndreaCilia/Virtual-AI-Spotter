"""
OverlayRenderer - Handles full-screen overlay messages.

Single Responsibility: Render overlay messages (REST, FINISHED states).
"""
import cv2


# Layout Constants
OVERLAY_ALPHA = 0.7


class OverlayRenderer:
    """Renders full-screen overlay messages for workout state transitions."""
    
    def draw_message(self, frame, title: str, subtitle: str) -> None:
        """
        Draws a full-screen overlay with title and subtitle.
        
        Args:
            frame: OpenCV image
            title: Main message (e.g., "REST" or "FINISHED")
            subtitle: Secondary message (e.g., "Press SPACE to continue")
        """
        h, w = frame.shape[:2]
        
        # Semi-transparent dark overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, OVERLAY_ALPHA, frame, 1 - OVERLAY_ALPHA, 0, frame)
        
        font = cv2.FONT_HERSHEY_DUPLEX
        
        # Title (centered, green, large)
        t_size = cv2.getTextSize(title, font, 2.0, 3)[0]
        t_x = (w - t_size[0]) // 2
        t_y = (h // 2) - 20
        cv2.putText(frame, title, (t_x, t_y), font, 2.0, (0, 255, 0), 3, cv2.LINE_AA)
        
        # Subtitle (centered, white, smaller)
        s_size = cv2.getTextSize(subtitle, font, 1.0, 2)[0]
        s_x = (w - s_size[0]) // 2
        s_y = (h // 2) + 40
        cv2.putText(frame, subtitle, (s_x, s_y), font, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
