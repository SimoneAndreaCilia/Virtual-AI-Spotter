import pytest
from fastapi.testclient import TestClient
from src.api.server import app

client = TestClient(app)

def test_setup_workout():
    payload = {
        "exercise_name": "Squat",
        "target_sets": 3,
        "target_reps": 10,
        "side": "both",
        "exercise_config": {"side": "both"},
        "language": "EN"
    }
    
    response = client.post("/api/setup", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "success"}
    
    # Verify SpotterApp state
    assert app.state.spotter_app is not None
    assert app.state.spotter_thread is not None
    assert app.state.spotter_thread.is_alive()
    
    # Cleanup background thread
    app.state.spotter_app.command_queue.put("quit")
    app.state.spotter_thread.join(timeout=2.0)
