import sys
import os
import time

# Add project root to python path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.data.db_manager import DatabaseManager
from src.core.entities.user import User
from src.core.entities.session import Session

def test_persistence():
    print("Testing Persistence...")
    
    # Use a test database file
    test_db = "test_gym.db"
    if os.path.exists(test_db):
        os.remove(test_db)
        
    db_manager = DatabaseManager(db_path=test_db)
    
    # 1. Create and Save User
    user = User(username="PersistUser", height=185.0)
    db_manager.save_user(user)
    print(f"User Saved: {user.id}")
    
    # 2. Retrieve User
    loaded_user = db_manager.get_user(user.id)
    assert loaded_user is not None
    assert loaded_user.username == "PersistUser"
    print("User Loaded Successfully")
    
    # 3. Create Session with Exercises
    session = Session(user_id=user.id)
    session.add_exercise({"name": "PushUp", "reps": 20})
    time.sleep(0.1) # Simulate time passing
    session.end_session()
    
    db_manager.save_session(session)
    print(f"Session Saved: {session.id}")
    
    # 4. Verify Raw Data in SQLite
    conn = db_manager._get_connection()
    cursor = conn.cursor()
    
    # Check Session
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session.id,))
    s_row = cursor.fetchone()
    assert s_row is not None
    assert s_row["user_id"] == user.id
    
    # Check Exercises
    cursor.execute("SELECT * FROM exercises WHERE session_id = ?", (session.id,))
    e_rows = cursor.fetchall()
    assert len(e_rows) == 1
    assert e_rows[0]["name"] == "PushUp"
    assert e_rows[0]["reps"] == 20
    
    conn.close()
    
    # Cleanup
    # if os.path.exists(test_db):
    #     os.remove(test_db)
        
    print("\nSUCCESS: Persistence logic verified!")

if __name__ == "__main__":
    test_persistence()
