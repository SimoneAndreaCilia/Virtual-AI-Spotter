import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from src.core.entities.user import User
from src.core.entities.session import Session

class DatabaseManager:
    def __init__(self, db_path: str = "src/data/gym.db", schema_path: str = "src/data/schema.sql"):
        # Assicuriamoci che la cartella 'src/data' esista o che il percorso sia assoluto
        # Se lo script viene lanciato da root, 'src/data/gym.db' funziona.
        self.db_path = db_path
        self.schema_path = schema_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Inizializza il database creando le tabelle se non esistono."""
        if not os.path.exists(self.schema_path):
             # Fallback se lo schema non è trovato dove previsto (es. test)
             self.schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        
        with open(self.schema_path, "r") as f:
            schema = f.read()
        
        conn = self._get_connection()
        conn.executescript(schema)
        conn.close()

    # --- USER OPERATIONS ---
    
    def save_user(self, user: User):
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
        """Recupera un utente per ID, o l'ultimo creato se ID è None."""
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

    # --- SESSION OPERATIONS ---

    def save_session(self, session: Session):
        """Salva la sessione e tutti i suoi esercizi."""
        conn = self._get_connection()
        try:
            # 1. Salva Sessione
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
            
            # 2. Salva Esercizi (Semplificato: li aggiungiamo tutti, idealmente solo i nuovi)
            # Per evitare duplicati in questa implementazione semplice, cancelliamo e riscriviamo gli esercizi di questa sessione
            # In produzione: meglio una logica di append o ID univoci per esercizi
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
                        json.dumps(ex) # Salviamo tutto il dizionario come JSON
                    )
                )
            
            conn.commit()
        finally:
            conn.close()
