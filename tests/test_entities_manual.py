from datetime import datetime
import sys
import os

# Add project root to python path to allow imports
# Assuming script is in <root>/scripts/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.core.entities.user import User
from src.core.entities.session import Session

def test_entities():
    print("Testing Entities...")

    # 1. Create User
    user = User(username="test_user", height=180.0, weight=75.5)
    print(f"User Created: {user}")
    
    assert user.username == "test_user"
    assert user.height == 180.0
    assert user.id is not None
    
    # 2. Update Preferences
    user.update_preferences({"theme": "dark", "volume": 80})
    print(f"User Preferences: {user.preferences}")
    assert user.preferences["theme"] == "dark"

    # 3. Create Session
    session = Session(user_id=user.id)
    print(f"Session Created: {session}")
    
    assert session.user_id == user.id
    assert session.end_time is None
    
    # 4. Add Exercise
    exercise_data = {
        "name": "Bicep Curl",
        "reps": 10,
        "valid": True
    }
    session.add_exercise(exercise_data)
    print(f"Session Exercises: {session.exercises}")
    assert len(session.exercises) == 1
    assert session.exercises[0]["name"] == "Bicep Curl"

    # 5. End Session
    session.end_session()
    print(f"Session Ended: {session.end_time}")
    assert session.end_time is not None
    
    print("\nSUCCESS: All entities verified correctly!")

if __name__ == "__main__":
    test_entities()
