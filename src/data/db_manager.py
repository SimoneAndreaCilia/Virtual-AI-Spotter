import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from src.core.entities.user import User
from src.core.entities.session import Session

class DatabaseManager:
    def __init__(self, db_path: str = "src/data/gym.db", schema_path: str = "src/data/schema.sql"):
        # Ensure 'src/data' folder exists or path is absolute
        # If script is run from root, 'src/data/gym.db' works.
        self.db_path = db_path
        self.schema_path = schema_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize database by creating tables if they don't exist."""
        if not os.path.exists(self.schema_path):
             # Fallback if schema not found at expected location (e.g., tests)
             self.schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        
        with open(self.schema_path, "r") as f:
            schema = f.read()
        
        conn = self._get_connection()
        conn.executescript(schema)
        conn.close()

    # --- USER OPERATIONS ---
    
    def save_user(self, user: User) -> None:
        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT INTO users (id, username, created_at, height, weight, preferences)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    username=excluded.username,
                    height=excluded.height,
                    weight=excluded.weight,
                    preferences=excluded.preferences
                """,
                (
                    user.id,
                    user.username,
                    user.created_at.isoformat(),
                    user.height,
                    user.weight,
                    json.dumps(user.preferences)
                )
            )
            conn.commit()
        finally:
            conn.close()

    def get_user(self, user_id: Optional[str] = None) -> Optional[User]:
        """Retrieve a user by ID, or the last created if ID is None."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        else:
            cursor.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT 1")
            
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(
                id=row["id"],
                username=row["username"],
                created_at=datetime.fromisoformat(row["created_at"]),
                height=row["height"],
                weight=row["weight"],
                preferences=json.loads(row["preferences"]) if row["preferences"] else {}
            )
        return None

    def create_default_user(self) -> User:
        """
        Creates a default user if none exists.
        
        Returns:
            User: The newly created default user.
        """
        user = User(username="Athlete")
        self.save_user(user)
        return user

    # --- SESSION OPERATIONS ---

    def save_session(self, session: Session) -> None:
        """Save the session and all its exercises."""
        conn = self._get_connection()
        try:
            # 1. Save Session
            conn.execute(
                """
                INSERT INTO sessions (id, user_id, start_time, end_time)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    end_time=excluded.end_time
                """,
                (
                    session.id,
                    session.user_id,
                    session.start_time.isoformat(),
                    session.end_time.isoformat() if session.end_time else None
                )
            )
            
            # 2. Save Exercises (Simplified: add all, ideally only new ones)
            # To avoid duplicates in this simple implementation, delete and rewrite exercises for this session
            # In production: better to use append logic or unique IDs for exercises
            conn.execute("DELETE FROM exercises WHERE session_id = ?", (session.id,))
            
            for ex in session.exercises:
                conn.execute(
                    """
                    INSERT INTO exercises (session_id, name, reps, details)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        session.id,
                        ex.get("name", "Unknown"),
                        ex.get("reps", 0),
                        json.dumps(ex)  # Save entire dict as JSON
                    )
                )
            
            conn.commit()
        finally:
            conn.close()
