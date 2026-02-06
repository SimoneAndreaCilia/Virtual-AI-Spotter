"""
SpotterApp - Main Application Controller for Virtual AI Spotter.

Implements Dependency Injection pattern:
- Dependencies are injected via __init__
- main.py acts as Composition Root (creates and wires dependencies)
- Enables testing with mocks (CI/CD without hardware)
"""
import cv2
import logging
import time
from typing import Optional, Dict, Any

from config.settings import LOGS_DIR, SHOW_FPS, FRAME_SKIP
from config.translation_strings import i18n
from src.core.interfaces import VideoSource
from src.core.protocols import PoseDetector, DatabaseManagerProtocol as DBManager
from src.core.session_manager import SessionManager
from src.core.factory import ExerciseFactory
from src.infrastructure.keypoint_extractor import YoloKeypointExtractor
from src.ui.visualizer import Visualizer
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
        config: Dict[str, Any]
    ):
        """
        Initialize SpotterApp with injected dependencies.
        
        Args:
            video_source: VideoSource implementation (WebcamSource or MockVideoSource)
            pose_detector: PoseDetector implementation (PoseEstimator or MockPoseEstimator)
            db_manager: DatabaseManager implementation
            config: Configuration dict from CLI (exercise_name, target_reps, etc.)
        """
        self.video_source = video_source
        self.pose_detector = pose_detector
        self.db_manager = db_manager
        self.config = config
        
        # Internal state (initialized in setup())
        self.session_manager: Optional[SessionManager] = None
        self.visualizer: Optional[Visualizer] = None
        self.running = False

    def setup(self):
        """
        Initializes internal components after dependencies are ready.
        
        Call this after __init__ and before run().
        """
        # 1. Logger Setup
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
        
        # 4c. Session Manager (receives injected dependencies)
        self.session_manager = SessionManager(
            db_manager=self.db_manager,
            user_id=user.id,
            exercise=exercise,
            keypoint_extractor=keypoint_extractor,
            target_sets=self.config.get('target_sets', 3),
            target_reps=self.config.get('target_reps', 10)
        )
        
        # 5. Visualizer
        self.visualizer = Visualizer()
        
        logging.info("SpotterApp initialized successfully.")

    def run(self):
        """Main Game Loop."""
        self.running = True
        logging.info("Starting main loop...")
        
        # Performance tracking
        fps_counter = FPSCounter(window_size=30)
        frame_count = 0
        last_pose_data = None
        
        try:
            while self.running:
                # 1. Input
                ret, frame = self.video_source.get_frame()
                if not ret:
                    logging.warning("Frame not received from video source.")
                    break

                # 2. Process (AI Inference) - with optional frame skip
                if FRAME_SKIP == 0 or frame_count % (FRAME_SKIP + 1) == 0:
                    pose_data = self.pose_detector.predict(frame)
                    last_pose_data = pose_data
                else:
                    pose_data = last_pose_data  # Reuse previous inference
                
                # 3. Logic (Update State)
                # Pass current time for smoothing algorithms
                ui_state = self.session_manager.update(pose_data, time.time())
                
                # 4. Render
                display_frame = self.visualizer.draw_dashboard_from_state(frame, ui_state)
                
                # 4b. FPS overlay (optional)
                if SHOW_FPS:
                    fps = fps_counter.tick()
                    cv2.putText(display_frame, f"FPS: {fps:.1f}", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # 5. Output
                cv2.imshow(i18n.get('ui_title'), display_frame)
                
                # 6. Input Handlers (Keyboard)
                self._handle_input()
                
                frame_count += 1
                
                if self.session_manager.is_session_finished():
                    # Optional: wait for user to quit after finish
                    pass

        except Exception as e:
            logging.critical(f"Critical Error in Main Loop: {e}", exc_info=True)
        finally:
            self._cleanup()

    def _handle_input(self):
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            self.running = False
        elif key == ord('c') or key == ord('C'):
            self.session_manager.handle_user_input('CONTINUE')

    def _cleanup(self):
        if self.video_source:
            self.video_source.release()
        cv2.destroyAllWindows()
        if self.session_manager:
            self.session_manager.save_session()
        logging.info("SpotterApp shut down cleanly.")
