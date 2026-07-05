from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router
import os

def create_app() -> FastAPI:
    app = FastAPI(title="Virtual AI Spotter Web GUI")
    
    # State setup
    app.state.spotter_app = None
    app.state.spotter_thread = None
    
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
