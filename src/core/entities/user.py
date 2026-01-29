import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional

@dataclass
class User:
    """
    Rappresenta l'utente dell'applicazione.
    """
    username: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    height: Optional[float] = None  # in cm
    weight: Optional[float] = None  # in kg
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    def update_preferences(self, new_prefs: Dict[str, Any]):
        """Aggiorna le preferenze utente."""
        self.preferences.update(new_prefs)
