"""
SkeletonRenderer - Handles drawing pose skeleton and angle arcs.

Single Responsibility: Render human body skeleton from keypoints.
"""
import cv2
from config.settings import COLORS, THICKNESS


class SkeletonRenderer:
    """Renders the pose skeleton (joints and bones) on video frames."""
    
    # COCO Keypoint connections (body skeleton)
    # 5: L Shoulder, 7: L Elbow, 9: L Wrist
    # 6: R Shoulder, 8: R Elbow, 10: R Wrist
    # 11: L Hip, 13: L Knee, 15: L Ankle
    # 12: R Hip, 14: R Knee, 16: R Ankle
    CONNECTIONS = [
        (5, 7), (7, 9),       # Left Arm
        (6, 8), (8, 10),      # Right Arm
        (11, 13), (13, 15),   # Left Leg
        (12, 14), (14, 16),   # Right Leg
        (5, 6), (11, 12),     # Shoulders and Hips
        (5, 11), (6, 12)      # Torso
    ]
    
    def draw(self, frame, keypoints) -> None:
        """
        Draws skeleton lines and joints on the detected keypoints.
        
        Args:
            frame: OpenCV image (BGR)
            keypoints: numpy array of shape (17, 2) or (17, 3) from YOLO
        """
        if keypoints is None or len(keypoints) == 0:
            return

        # 1. Draw joints (circles)
        for row in keypoints:
            x, y = row[0], row[1]
            if x > 0 and y > 0:
                cv2.circle(frame, (int(x), int(y)), 5, COLORS["YELLOW"], -1)

        # 2. Draw bones (lines)
        for idx_start, idx_end in self.CONNECTIONS:
            if idx_start < len(keypoints) and idx_end < len(keypoints):
                p1 = (int(keypoints[idx_start][0]), int(keypoints[idx_start][1]))
                p2 = (int(keypoints[idx_end][0]), int(keypoints[idx_end][1]))
                
                if p1[0] > 0 and p1[1] > 0 and p2[0] > 0 and p2[1] > 0:
                    cv2.line(frame, p1, p2, COLORS["BLUE"], THICKNESS["SKELETON"])

    def draw_angle_arc(self, frame, center, angle_val) -> None:
        """
        (Optional) Draws the angle value near the joint.
        
        Args:
            frame: OpenCV image
            center: (x, y) tuple of the joint position
            angle_val: Angle value in degrees
        """
        if center[0] == 0:
            return

        cv2.putText(
            frame, 
            f"{int(angle_val)}", 
            (int(center[0]) - 20, int(center[1]) - 20),
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.6, 
            COLORS["WHITE"], 
            2
        )
