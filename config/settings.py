import os
from typing import Any


# --- 0. HELPER FUNCTIONS ---
def _get_env(key: str, default: Any, cast_type=str) -> Any:
    """Get environment variable with type casting and fallback."""
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return cast_type(value)
    except (ValueError, TypeError):
        return default


def _detect_device() -> str:
    """Auto-detect best available compute device."""
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
    except ImportError:
        pass
    return "cpu"


# --- 1. PATH CONFIGURATION ---
# Dynamically calculate project root to avoid "File not found" errors
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Absolute paths to resources (with env var overrides)
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
MODELS_DIR = os.path.join(ASSETS_DIR, "models")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
DB_PATH = _get_env("SPOTTER_DB_PATH", os.path.join(BASE_DIR, "src", "data", "gym_data.db"))

# --- 2. AI & MODEL CONFIGURATION ---
MODEL_NAME = "yolov8n-pose.pt"  # Nano model (faster) or 'yolov8s-pose.pt' (more accurate)
MODEL_PATH = os.path.join(MODELS_DIR, MODEL_NAME)
CONFIDENCE_THRESHOLD = 0.5     # Ignore detections with confidence < 50%
DEVICE = _get_env("SPOTTER_DEVICE", _detect_device())  # Auto-detect: cuda/mps/cpu

# --- 3. CAMERA CONFIGURATION ---
CAMERA_ID = 0           # 0 for integrated webcam, 1 for external
FRAME_WIDTH = 1280      # Desired resolution (HD)
FRAME_HEIGHT = 720
FPS = 30

# --- 4. EXERCISE LOGIC (ANGULAR THRESHOLDS) ---
# Modify these values to calibrate exercise difficulty

# Squat Parameters
SQUAT_THRESHOLDS = {
    "UP_ANGLE": 160,       # Leg almost straight (Standing)
    "DOWN_ANGLE": 90,      # Parallel squat (Horizontal)
    "WARN_ANGLE": 110      # Warning threshold "Go lower"
}

# Bicep Curl Parameters
CURL_THRESHOLDS = {
    "UP_ANGLE": 30,        # Maximum contraction (Hands near shoulders)
    "DOWN_ANGLE": 160,     # Arm extended
    "ERROR_ELBOW": 15      # Elbow movement tolerance (too much = error)
}

# Push Up Parameters
PUSHUP_THRESHOLDS = {
    "UP_ANGLE": 160,       # Arms extended
    "DOWN_ANGLE": 90,      # Arms bent at 90 degrees
    "FORM_ANGLE_MIN": 160  # Body line tolerance (approx 180 is straight)
}

# Plank Parameters
PLANK_THRESHOLDS = {
    "SHOULDER_HIP_ANKLE_MIN": 160, # Body straightness
    "ELBOW_ANGLE_MIN": 70,         # Forearms on ground/bent
    "ELBOW_ANGLE_MAX": 110,
    "STABILITY_DURATION": 3        # Seconds to hold before starting timer
}

# Smoothing Parameters (Data Structures)
BUFFER_SIZE = 10           # Number of frames for moving average (reduces jitter)
HYSTERESIS_TOLERANCE = 5   # Tolerance (degrees) for state change debouncing (e.g., +5/-5)
FSM_STABILITY_FRAMES = 2   # Consecutive frames required for state transition

# --- 4b. PERFORMANCE SETTINGS ---
SHOW_FPS = True            # Display FPS counter in HUD
FRAME_SKIP = 0             # Skip N frames between AI inference (0 = process every frame)

# --- 4c. GESTURE RECOGNITION ---
GESTURE_ENABLED = True     # Enable hands-free gesture control
GESTURE_STABILITY = 10     # Frames gesture must be held to trigger action
GESTURE_CONFIDENCE = 0.6   # Minimum keypoint confidence for gesture detection
GESTURE_Y_DIFF_THRESHOLD = 50 # Pixels wrist must be above shoulder for THUMBS_UP

# --- 5. VISUALIZATION (UI) ---
# Colors in BGR format (Blue, Green, Red) for OpenCV
COLORS = {
    "WHITE": (255, 255, 255),
    "BLACK": (0, 0, 0),
    "GREEN": (0, 255, 0),      # Success / Correct Form
    "RED": (0, 0, 255),        # Error / Wrong Form
    "YELLOW": (0, 255, 255),   # Warning / Info / Joints
    "BLUE": (255, 0, 0),       # Skeleton
    "GRAY": (128, 128, 128),   # Standard gray
    "OVERLAY_BG": (40, 40, 40) # Dark semi-transparent background
}

# Line thickness
THICKNESS = {
    "SKELETON": 2,
    "TEXT": 2,
    "BOX": -1  # -1 fills the shape
}