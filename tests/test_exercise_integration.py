"""
Exercise-Level Integration Tests.

Tests full process_frame() cycles with synthetic keypoints, verifying
actual rep counting, low-confidence rejection, and form feedback end-to-end.

Unlike test_exercises.py (which validates "doesn't crash"), these tests
make STRONG assertions: assertEqual(reps, 1), assertFalse(is_valid), etc.

Key design notes:
- Timestamps are passed explicitly so the OneEuroFilter smoother converges
  quickly between states (without timestamps, the smoother uses time.time()
  which can produce tiny deltas in fast test loops).
- 10 frames per state phase ensures both smoother convergence AND FSM
  stability requirements (FSM_STABILITY_FRAMES=2).
"""
import unittest
import numpy as np

from src.exercises.curl import BicepCurl
from src.exercises.squat import Squat
from src.exercises.pushup import PushUp
from src.exercises.plank import Plank

# Frame timing: 30 FPS simulation
_DT = 1.0 / 30
_FRAMES_PER_PHASE = 10  # Enough for smoother + FSM stability


# ---------------------------------------------------------------------------
# Keypoint Helpers
# ---------------------------------------------------------------------------

def _curl_keypoints(elbow_angle: float, confidence: float = 0.9) -> np.ndarray:
    """
    Create right-arm curl keypoints producing a specific elbow angle.
    
    Vertex is at the elbow (index 8). The angle is measured between
    shoulder→elbow and wrist→elbow vectors.
    """
    kp = np.zeros((17, 3))

    shoulder = np.array([300.0, 200.0])
    elbow = np.array([300.0, 300.0])  # Straight down

    # Calculate wrist position to get desired angle at elbow
    rad = np.radians(elbow_angle)
    wrist = elbow + np.array([100 * np.sin(rad), 100 * np.cos(rad)])

    kp[6] = [shoulder[0], shoulder[1], confidence]  # R Shoulder
    kp[8] = [elbow[0], elbow[1], confidence]        # R Elbow
    kp[10] = [wrist[0], wrist[1], confidence]       # R Wrist
    return kp


def _squat_keypoints(knee_angle: float, confidence: float = 0.9) -> np.ndarray:
    """
    Create right-leg squat keypoints producing a specific knee angle.
    
    Vertex is at the knee (index 14). Uses conversion to geometry angle.
    """
    kp = np.zeros((17, 3))

    hip = np.array([300.0, 200.0])
    knee = np.array([300.0, 350.0])

    rad = np.radians(180 - knee_angle)
    ankle = knee + np.array([100 * np.sin(rad), 100 * np.cos(rad)])

    kp[12] = [hip[0], hip[1], confidence]      # R Hip
    kp[14] = [knee[0], knee[1], confidence]     # R Knee
    kp[16] = [ankle[0], ankle[1], confidence]   # R Ankle
    return kp


def _pushup_keypoints(elbow_extended: bool = True,
                      body_straight: bool = True,
                      confidence: float = 0.9) -> np.ndarray:
    """
    Create left-side pushup keypoints using direct coordinate placement.
    
    Uses verified positions that produce correct angles via calculate_angle:
    - Elbow angle: angle at index 7 between indices 5-7-9
    - Body angle:  angle at index 11 between indices 5-11-15
    """
    kp = np.zeros((17, 3))

    # Shoulder (constant)
    kp[5] = [200, 200, confidence]  # L Shoulder

    if elbow_extended:
        # Extended: shoulder→elbow→wrist nearly straight (~170°)
        kp[7] = [200, 300, confidence]  # L Elbow (straight down)
        kp[9] = [200, 400, confidence]  # L Wrist (continues straight)
    else:
        # Bent: ~90° at elbow
        kp[7] = [200, 300, confidence]  # L Elbow (straight down)
        kp[9] = [300, 300, confidence]  # L Wrist (90° to the right)

    # Hip (constant, horizontal from shoulder)
    kp[11] = [400, 200, confidence]  # L Hip

    if body_straight:
        # Body straight: shoulder-hip-ankle collinear (~180°)
        kp[15] = [600, 200, confidence]  # L Ankle (continues horizontal)
    else:
        # Body sagging: ~90° at hip
        kp[15] = [400, 400, confidence]  # L Ankle (straight down from hip)

    return kp


def _plank_keypoints(body_straight: bool = True,
                     elbow_correct: bool = True,
                     confidence: float = 0.9) -> np.ndarray:
    """
    Create left-side plank keypoints.
    
    body_straight=True  → ~180° body line (shoulder-hip-ankle)
    elbow_correct=True  → ~90°  elbow angle (shoulder-elbow-wrist)
    """
    kp = np.zeros((17, 3))

    kp[5] = [0, 0, confidence]      # L Shoulder
    kp[11] = [1, 0, confidence]     # L Hip

    if body_straight:
        kp[15] = [2, 0, confidence]  # L Ankle → straight line ~180°
    else:
        kp[15] = [1, 1, confidence]  # L Ankle → bent ~90°

    if elbow_correct:
        kp[7] = [0, 1, confidence]   # L Elbow → down
        kp[9] = [1, 1, confidence]   # L Wrist → 90° angle
    else:
        kp[7] = [0, 1, confidence]   # L Elbow
        kp[9] = [0, 2, confidence]   # L Wrist → ~180° (arms extended)

    return kp


def _feed_phase(exercise, keypoints, n: int, start_time: float):
    """
    Feed n frames with proper timestamps (30 FPS).
    Returns (last_result, next_start_time).
    """
    result = None
    t = start_time
    for _ in range(n):
        result = exercise.process_frame(keypoints, timestamp=t)
        t += _DT
    return result, t


# ---------------------------------------------------------------------------
# Curl Integration
# ---------------------------------------------------------------------------

class TestCurlIntegration(unittest.TestCase):
    """End-to-end rep counting for BicepCurl."""

    def setUp(self):
        self.curl = BicepCurl({"side": "right"})

    def test_full_rep_counted(self):
        """Extended→Flexed = 1 rep (inverted: small angle = UP = rep)."""
        extended = _curl_keypoints(elbow_angle=170)
        flexed = _curl_keypoints(elbow_angle=25)

        _, t = _feed_phase(self.curl, extended, _FRAMES_PER_PHASE, 0.0)
        result, _ = _feed_phase(self.curl, flexed, _FRAMES_PER_PHASE, t)

        self.assertEqual(result.reps, 1)

    def test_two_reps_counted(self):
        """Two full down→up cycles = 2 reps."""
        extended = _curl_keypoints(elbow_angle=170)
        flexed = _curl_keypoints(elbow_angle=25)

        t = 0.0
        for _ in range(2):
            _, t = _feed_phase(self.curl, extended, _FRAMES_PER_PHASE, t)
            _, t = _feed_phase(self.curl, flexed, _FRAMES_PER_PHASE, t)

        self.assertEqual(self.curl.reps, 2)

    def test_low_confidence_rejects(self):
        """Keypoints below CONFIDENCE_THRESHOLD → is_valid=False."""
        low_conf = _curl_keypoints(elbow_angle=90, confidence=0.3)
        result, _ = _feed_phase(self.curl, low_conf, 3, 0.0)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.correction, "err_body_not_visible")


# ---------------------------------------------------------------------------
# Squat Integration
# ---------------------------------------------------------------------------

class TestSquatIntegration(unittest.TestCase):
    """End-to-end rep counting for Squat."""

    def setUp(self):
        self.squat = Squat({"side": "right"})

    def test_full_rep_counted(self):
        """Standing→Squat→Standing = 1 rep (standard logic)."""
        standing = _squat_keypoints(knee_angle=170)
        squatting = _squat_keypoints(knee_angle=80)

        t = 0.0
        _, t = _feed_phase(self.squat, standing, _FRAMES_PER_PHASE, t)
        _, t = _feed_phase(self.squat, squatting, _FRAMES_PER_PHASE, t)
        result, _ = _feed_phase(self.squat, standing, _FRAMES_PER_PHASE, t)

        self.assertEqual(result.reps, 1)

    def test_two_reps_counted(self):
        """Two up→down→up cycles = 2 reps."""
        standing = _squat_keypoints(knee_angle=170)
        squatting = _squat_keypoints(knee_angle=80)

        t = 0.0
        for _ in range(2):
            _, t = _feed_phase(self.squat, standing, _FRAMES_PER_PHASE, t)
            _, t = _feed_phase(self.squat, squatting, _FRAMES_PER_PHASE, t)
        _, t = _feed_phase(self.squat, standing, _FRAMES_PER_PHASE, t)

        self.assertEqual(self.squat.reps, 2)

    def test_low_confidence_rejects(self):
        """Keypoints below CONFIDENCE_THRESHOLD → is_valid=False."""
        low_conf = _squat_keypoints(knee_angle=120, confidence=0.3)
        result, _ = _feed_phase(self.squat, low_conf, 3, 0.0)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.correction, "err_body_not_visible")


# ---------------------------------------------------------------------------
# PushUp Integration
# ---------------------------------------------------------------------------

class TestPushUpIntegration(unittest.TestCase):
    """End-to-end rep counting and form feedback for PushUp."""

    def setUp(self):
        self.pushup = PushUp({"side": "left"})

    def test_full_rep_counted(self):
        """Extended→Bent→Extended = 1 rep."""
        up = _pushup_keypoints(elbow_extended=True, body_straight=True)
        down = _pushup_keypoints(elbow_extended=False, body_straight=True)

        t = 0.0
        _, t = _feed_phase(self.pushup, up, _FRAMES_PER_PHASE, t)
        _, t = _feed_phase(self.pushup, down, _FRAMES_PER_PHASE, t)
        result, _ = _feed_phase(self.pushup, up, _FRAMES_PER_PHASE, t)

        self.assertEqual(result.reps, 1)

    def test_bad_body_form_triggers_feedback(self):
        """Body angle < FORM_ANGLE_MIN → pushup_warn_back correction."""
        bad_form = _pushup_keypoints(elbow_extended=True, body_straight=False)
        result, _ = _feed_phase(self.pushup, bad_form, _FRAMES_PER_PHASE, 0.0)

        self.assertEqual(result.correction, "pushup_warn_back")

    def test_low_confidence_rejects(self):
        """Keypoints below CONFIDENCE_THRESHOLD → is_valid=False."""
        low_conf = _pushup_keypoints(confidence=0.3)
        result, _ = _feed_phase(self.pushup, low_conf, 3, 0.0)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.correction, "err_body_not_visible")


# ---------------------------------------------------------------------------
# Plank Integration
# ---------------------------------------------------------------------------

class TestPlankIntegration(unittest.TestCase):
    """Full lifecycle and form feedback for Plank (StaticDurationCounter)."""

    def setUp(self):
        self.plank = Plank({"side": "left"})

    def test_full_lifecycle(self):
        """waiting → countdown → active → finished."""
        good = _plank_keypoints(body_straight=True, elbow_correct=True)

        # 1. First frame: waiting → countdown
        result = self.plank.process_frame(good, timestamp=0.0)
        self.assertEqual(result.stage, "countdown")

        # 2. Hold 2.5s (still countdown, STABILITY_DURATION=3)
        result = self.plank.process_frame(good, timestamp=2.5)
        self.assertEqual(result.stage, "countdown")

        # 3. Hold past 3s → active
        result = self.plank.process_frame(good, timestamp=3.1)
        self.assertEqual(result.stage, "active")
        self.assertEqual(result.reps, 0)

        # 4. Hold 5 more seconds
        result = self.plank.process_frame(good, timestamp=8.1)
        self.assertEqual(result.stage, "active")
        self.assertEqual(result.reps, 5)

        # 5. Break form → finished
        bad = _plank_keypoints(body_straight=False, elbow_correct=True)
        result = self.plank.process_frame(bad, timestamp=9.0)
        self.assertEqual(result.stage, "finished")
        self.assertEqual(result.reps, 5)

    def test_bad_form_triggers_finished(self):
        """Bad body angle during active → transitions to finished."""
        good = _plank_keypoints(body_straight=True, elbow_correct=True)

        # Get to active state
        self.plank.process_frame(good, timestamp=0.0)
        self.plank.process_frame(good, timestamp=3.1)

        # Break form while active → FSM goes to finished
        bad = _plank_keypoints(body_straight=False, elbow_correct=True)
        result = self.plank.process_frame(bad, timestamp=4.0)
        self.assertEqual(result.stage, "finished")

    def test_reset_clears_state(self):
        """After lifecycle, reset() returns to waiting with 0 reps."""
        good = _plank_keypoints(body_straight=True, elbow_correct=True)

        self.plank.process_frame(good, timestamp=0.0)
        self.plank.process_frame(good, timestamp=3.1)
        self.plank.process_frame(good, timestamp=8.0)
        self.assertGreater(self.plank.reps, 0)

        self.plank.reset()
        self.assertEqual(self.plank.stage, "waiting")
        self.assertEqual(self.plank.reps, 0)


if __name__ == "__main__":
    unittest.main()
