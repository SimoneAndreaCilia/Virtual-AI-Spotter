"""
Main Entry Point for Virtual AI Spotter.

This module acts as the COMPOSITION ROOT:
- Creates all dependencies (VideoSource, PoseDetector, DatabaseManager)
- Optionally creates CloudSessionUploader for AWS integration
- Injects them into SpotterApp
- Allows easy swapping of implementations (real vs mock)

For testing, you can import and use different implementations:
    from tests.mocks.mock_video import MockVideoSource
    from tests.mocks.mock_pose import MockPoseEstimator
"""
import sys
import logging
import uvicorn
from dotenv import load_dotenv

def main():
    """
    Entry point for Virtual AI Spotter.
    
    Starts the FastAPI Web Server using Uvicorn.
    """
    # Load environment variables
    load_dotenv()
    
    try:
        logging.info("Starting Virtual AI Spotter Web Server...")
        print("Starting Server at http://localhost:8000")
        uvicorn.run("src.api.server:app", host="127.0.0.1", port=8000, reload=False)
    except KeyboardInterrupt:
        print("\nAborted by user.")
    except Exception as e:
        logging.error(f"Critical Error: {e}", exc_info=True)
        print(f"Critical Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()