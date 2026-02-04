import cv2
import logging
import time
from typing import Optional

from config.settings import LOGS_DIR, CAMERA_ID, MODEL_PATH, DEVICE
from config.translation_strings import i18n
from src.core.interfaces import VideoSource
from src.core.session_manager import SessionManager
from src.infrastructure.webcam import WebcamSource
from src.infrastructure.ai_inference import PoseEstimator
from src.ui.visualizer import Visualizer
from src.ui.cli import CLI
from src.data.db_manager import DatabaseManager

class SpotterApp:
    def __init__(self):
        self.config = {}
        self.video_source: Optional[VideoSource] = None
        self.pose_detector: Optional[PoseEstimator] = None
        self.session_manager: Optional[SessionManager] = None
        self.visualizer: Optional[Visualizer] = None
        self.db_manager: Optional[DatabaseManager] = None
        self.running = False

    def setup(self):
        """Initializes all sub-components and loads configuration."""
        # 1. Logger Setup
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"{LOGS_DIR}/app.log"),
                logging.StreamHandler()
            ]
        )
        
        # 2. CLI UI for Initial Config
        self.config = CLI.get_initial_config()
        i18n.set_language(self.config.get('language', 'EN'))
        
        # 3. Database
        self.db_manager = DatabaseManager()
        user = self.db_manager.get_user() or self.db_manager.create_default_user()
        
        # 4. Session Manager
        self.session_manager = SessionManager(
            db_manager=self.db_manager,
            user_id=user.id,
            exercise_name=self.config['exercise_name'],
            exercise_config=self.config['exercise_config'],
            target_sets=self.config['target_sets'],
            target_reps=self.config['target_reps']
        )
        
        # 5. Infrastructure (Webcam & AI)
        self.pose_detector = PoseEstimator(MODEL_PATH, DEVICE)
        self.video_source = WebcamSource(source_index=CAMERA_ID)
        self.visualizer = Visualizer()
        
        logging.info("SpotterApp initialized successfully.")

    def run(self):
        """Main Game Loop."""
        self.running = True
        logging.info("Starting main loop...")
        
        try:
            while self.running:
                # 1. Input
                ret, frame = self.video_source.get_frame()
                if not ret:
                    logging.warning("Frame not received from video source.")
                    break

                # 2. Process (AI Inference)
                pose_data = self.pose_detector.predict(frame)
                
                # 3. Logic (Update State)
                # Pass current time for smoothing algorithms
                ui_state = self.session_manager.update(pose_data, time.time())
                
                # 4. Render
                display_frame = self.visualizer.draw_dashboard_from_state(frame, ui_state)
                
                # 5. Output
                cv2.imshow(i18n.get('ui_title'), display_frame)
                
                # 6. Input Handlers (Keyboard)
                self._handle_input()
                
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
