"""
Main Entry Point for Virtual AI Spotter.

This module acts as the COMPOSITION ROOT:
- Creates all dependencies (VideoSource, PoseDetector, DatabaseManager)
- Injects them into SpotterApp
- Allows easy swapping of implementations (real vs mock)

For testing, you can import and use different implementations:
    from src.infrastructure.mock_video import MockVideoSource
    from src.infrastructure.mock_pose import MockPoseEstimator
"""
import sys
import logging

from config.settings import CAMERA_ID, MODEL_PATH, DEVICE
from src.core.app import SpotterApp
from src.core.exceptions import SpotterError
from src.infrastructure.webcam import WebcamSource
from src.infrastructure.ai_inference import PoseEstimator
from src.data.db_manager import DatabaseManager
from src.ui.cli import CLI


def create_production_app() -> SpotterApp:
    """
    Factory function that creates SpotterApp with production dependencies.
    
    Returns:
        SpotterApp configured with real webcam, AI model, and database.
    """
    # 1. Get configuration from CLI
    config = CLI.get_initial_config()
    
    # 2. Create dependencies
    db_manager = DatabaseManager()
    video_source = WebcamSource(source_index=CAMERA_ID)
    pose_detector = PoseEstimator(MODEL_PATH, DEVICE)
    
    # 3. Inject into App
    app = SpotterApp(
        video_source=video_source,
        pose_detector=pose_detector,
        db_manager=db_manager,
        config=config
    )
    
    return app


def main():
    """
    Entry point for Virtual AI Spotter.
    
    Bootstrap the Application Controller with production dependencies.
    """
    try:
        app = create_production_app()
        app.setup()
        app.run()
    except KeyboardInterrupt:
        print("\nAborted by user.")
    except SpotterError as e:
        logging.error(f"Critical Error: {e}", exc_info=True)
        print(f"Critical Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()