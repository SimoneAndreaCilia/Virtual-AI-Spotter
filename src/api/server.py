from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router
import os
from contextlib import asynccontextmanager
from src.infrastructure.webcam import WebcamSource
from src.infrastructure.ai_inference import PoseEstimator
from src.data.db_manager import DatabaseManager
from src.infrastructure.sinks import DequeOutputSink
from src.data.api_client import CloudSessionUploader
from config.settings import (
    CAMERA_ID, MODEL_PATH, DEVICE,
    AWS_API_URL, AWS_API_KEY, CLOUD_UPLOAD_ENABLED,
    CLOUD_UPLOAD_TIMEOUT, CLOUD_UPLOAD_MAX_RETRIES
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup global dependencies
    app.state.db_manager = DatabaseManager()
    app.state.video_source = WebcamSource(source_index=CAMERA_ID)
    app.state.pose_detector = PoseEstimator(MODEL_PATH, DEVICE)
    app.state.output_sink = DequeOutputSink(maxlen=2)
    
    app.state.cloud_uploader = None
    if CLOUD_UPLOAD_ENABLED and AWS_API_URL:
        app.state.cloud_uploader = CloudSessionUploader(
            api_url=AWS_API_URL,
            api_key=AWS_API_KEY,
            timeout=CLOUD_UPLOAD_TIMEOUT,
            max_retries=CLOUD_UPLOAD_MAX_RETRIES
        )
        
    app.state.spotter_app = None
    app.state.spotter_thread = None
    
    yield
    
    # Cleanup global dependencies
    if app.state.video_source:
        app.state.video_source.release()

def create_app() -> FastAPI:
    app = FastAPI(title="Virtual AI Spotter Web GUI", lifespan=lifespan)
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Routes
    app.include_router(router)
    
    # Static files
    web_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'web')
    if not os.path.exists(web_dir):
        os.makedirs(web_dir)
        
    app.mount("/", StaticFiles(directory=web_dir, html=True), name="web")
    
    return app

app = create_app()
