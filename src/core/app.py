"""
SpotterApp - Main Application Controller for Virtual AI Spotter.

Implements Dependency Injection pattern:
- Dependencies are injected via __init__
- main.py acts as Composition Root (creates and wires dependencies)
- Enables testing with mocks (CI/CD without hardware)
"""
import cv2
import logging
import os
import time
import json
import queue
from typing import Optional

from src.core.config_types import AppConfig

from config.settings import LOGS_DIR, SHOW_FPS, FRAME_SKIP, GESTURE_ENABLED, GESTURE_STABILITY, GESTURE_CONFIDENCE
from config.translation_strings import i18n
from src.core.interfaces import VideoSource, OutputSink
from src.core.exceptions import SpotterError
from src.core.protocols import PoseDetector, DatabaseManagerProtocol as DBManager, CloudUploaderProtocol
from src.core.session_manager import SessionManager
from src.core.factory import ExerciseFactory
from src.core.gesture_handler import GestureHandler
from src.infrastructure.keypoint_extractor import YoloKeypointExtractor
from src.utils.performance import FPSCounter


class SpotterApp:
    """
    Main application controller.
    
    Follows Single Responsibility Principle:
    - Does NOT construct dependencies (injected via __init__)
    - Only handles game loop execution
    
    Usage:
        # Production (in main.py)
        app = SpotterApp(
            video_source=WebcamSource(...),
            pose_detector=PoseEstimator(...),
            db_manager=DatabaseManager(),
            config={"exercise_name": "squat", ...}
        )
        app.setup()
        app.run()
        
        # Testing
        app = SpotterApp(
            video_source=MockVideoSource(),
            pose_detector=MockPoseEstimator(),
            db_manager=mock_db,
            config=test_config
        )
    """
    
    def __init__(
        self,
        video_source: VideoSource,
        pose_detector: PoseDetector,
        db_manager: DBManager,
        config: AppConfig,
        output_sink: OutputSink,
        cloud_uploader: Optional[CloudUploaderProtocol] = None
    ):
        """
        Initialize SpotterApp with injected dependencies.
        
        Args:
            video_source: VideoSource implementation (WebcamSource or MockVideoSource)
            pose_detector: PoseDetector implementation (PoseEstimator or MockPoseEstimator)
            db_manager: DatabaseManager implementation
            config: Configuration dict from CLI (exercise_name, target_reps, etc.)
            output_sink: Interface to emit frames and state (e.g. WebSocket)
            cloud_uploader: Optional CloudSessionUploader for AWS integration
        """
        self.video_source = video_source
        self.pose_detector = pose_detector
        self.db_manager = db_manager
        self.config = config
        self.output_sink = output_sink
        self.cloud_uploader = cloud_uploader
        
        # Internal state (initialized in setup())
        self.session_manager: Optional[SessionManager] = None
        self.running = False
        self.command_queue = queue.Queue()

    def setup(self):
        """
        Initializes internal components after dependencies are ready.
        
        Call this after __init__ and before run().
        """
        # 1. Logger Setup
        if not os.path.exists(LOGS_DIR):
            os.makedirs(LOGS_DIR, exist_ok=True)
            
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"{LOGS_DIR}/app.log"),
                logging.StreamHandler()
            ]
        )
        
        # 2. Language Setup
        i18n.set_language(self.config.get('language', 'EN'))
        
        # 3. User Setup
        user = self.db_manager.get_user() or self.db_manager.create_default_user()
        
        # 4a. Create Exercise (Composition Root responsibility)
        exercise = ExerciseFactory.create_exercise(
            self.config['exercise_name'],
            self.config.get('exercise_config', {})
        )
        
        # 4b. Create Keypoint Extractor (YOLO-specific)
        keypoint_extractor = YoloKeypointExtractor()
        
        # 4c. Create Gesture Handler (if enabled)
        gesture_handler = GestureHandler(
            stability_frames=GESTURE_STABILITY,
            confidence_threshold=GESTURE_CONFIDENCE
        ) if GESTURE_ENABLED else None
        
        # 4d. Session Manager (receives injected dependencies)
        self.session_manager = SessionManager(
            db_manager=self.db_manager,
            user_id=user.id,
            exercise=exercise,
            keypoint_extractor=keypoint_extractor,
            target_sets=self.config.get('target_sets', 3),
            target_reps=self.config.get('target_reps', 10),
            gesture_handler=gesture_handler,
            cloud_uploader=self.cloud_uploader
        )
        
        logging.info("SpotterApp initialized successfully.")

    def run(self):
        """Main Game Loop."""
        self.running = True
        logging.info("Starting main loop...")
        
        # Performance tracking
        fps_counter = FPSCounter(window_size=30)
        frame_count = 0
        last_pose_data = None
        frame_fail_count = 0  # Rate-limit logging for frame failures
        
        try:
            while self.running:
                # 1. Input
                ret, frame = self.video_source.get_frame()
                if not ret:
                    frame_fail_count += 1
                    # Rate-limited logging: log first failure and every 30th
                    if frame_fail_count == 1 or frame_fail_count % 30 == 0:
                        logging.warning(f"Frame read failed ({frame_fail_count} consecutive)")
                    continue  # Allow recovery instead of immediate break
                
                frame_fail_count = 0  # Reset on success

                # 2. Process (AI Inference) - with optional frame skip
                if FRAME_SKIP == 0 or frame_count % (FRAME_SKIP + 1) == 0:
                    pose_data = self.pose_detector.predict(frame)
                    last_pose_data = pose_data
                else:
                    pose_data = last_pose_data  # Reuse previous inference
                
                # 3. Logic (Update State)
                # Pass current time for smoothing algorithms
                ui_state = self.session_manager.update(pose_data, time.time())
                
                # 4. Render & Output (Delegate to Sink)
                state_json = json.dumps(ui_state.to_dict())
                self.output_sink.emit(frame, state_json)
                
                # 5. Input Handlers
                self._handle_input()
                
                frame_count += 1
                
                if self.session_manager.is_session_finished():
                    # Optional: wait for user to quit after finish
                    pass

        except (SpotterError, cv2.error) as e:
            logging.critical(f"Critical Error in Main Loop: {e}", exc_info=True)
        finally:
            self._cleanup()

    def _handle_input(self):
        try:
            cmd = self.command_queue.get_nowait()
            if cmd == 'quit':
                self.running = False
            elif cmd in ('continue', 'CONTINUE'):
                self.session_manager.handle_user_input('CONTINUE')
        except queue.Empty:
            pass

    def _cleanup(self):
        if self.video_source:
            self.video_source.release()
        if self.session_manager:
            self.session_manager.save_session()
        logging.info("SpotterApp shut down cleanly.")
