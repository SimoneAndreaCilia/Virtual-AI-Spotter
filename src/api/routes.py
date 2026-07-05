import asyncio
import cv2
import threading
from pydantic import BaseModel
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request

from src.core.app import SpotterApp
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
from config.translation_strings import TRANSLATIONS

router = APIRouter()

class SetupRequest(BaseModel):
    exercise_name: str
    target_sets: int
    target_reps: int
    exercise_config: Dict[str, Any]
    language: str = "EN"

@router.post("/api/setup")
async def setup_workout(request: Request, config: SetupRequest):
    app_state = request.app.state
    
    # Stop existing instance if running
    if app_state.spotter_app is not None:
        app_state.spotter_app.command_queue.put("quit")
        if app_state.spotter_thread is not None:
            app_state.spotter_thread.join(timeout=2.0)
            
    # Retrieve global dependencies
    db_manager = app_state.db_manager
    video_source = app_state.video_source
    pose_detector = app_state.pose_detector
    output_sink = app_state.output_sink
    cloud_uploader = app_state.cloud_uploader
    
    app_config = {
        'language': config.language,
        'exercise_name': config.exercise_name,
        'exercise_config': config.exercise_config,
        'target_sets': config.target_sets,
        'target_reps': config.target_reps,
    }
    
    spotter_app = SpotterApp(
        video_source=video_source,
        pose_detector=pose_detector,
        db_manager=db_manager,
        config=app_config,
        output_sink=output_sink,
        cloud_uploader=cloud_uploader
    )
    
    spotter_app.setup()
    
    # Start thread
    thread = threading.Thread(target=spotter_app.run, daemon=True)
    thread.start()
    
    # Save to state
    app_state.spotter_app = spotter_app
    app_state.spotter_thread = thread
    
    return {"status": "success"}

@router.post("/api/command")
async def send_command(request: Request, command: dict):
    app_state = request.app.state
    if app_state.spotter_app is not None:
        cmd = command.get("command")
        app_state.spotter_app.command_queue.put(cmd)
    return {"status": "ok"}

@router.get("/api/translations")
async def get_translations():
    return TRANSLATIONS

@router.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    await websocket.accept()
    app_state = websocket.app.state
    spotter_app = app_state.spotter_app
    
    if not spotter_app:
        await websocket.close()
        return

    output_sink = spotter_app.output_sink
    
    try:
        while True:
            item = output_sink.get_latest()
            if item is not None:
                frame, state_json = item
                # Encode frame to JPEG
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    # 1. Send binary bytes
                    await websocket.send_bytes(buffer.tobytes())
                    # 2. Send JSON state
                    await websocket.send_text(state_json)
            
            # Non-blocking yield
            await asyncio.sleep(0.002)
    except WebSocketDisconnect:
        print("WebSocket disconnected. Stopping SpotterApp...")
        if spotter_app:
            spotter_app.command_queue.put("quit")
