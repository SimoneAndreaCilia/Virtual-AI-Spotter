-- ==========================================
-- Tabella USERS
-- Rappresenta gli atleti che usano l'applicazione.
-- Contiene dati anagrafici, biometrici e configurazioni.
-- ==========================================
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,       -- UUID univoco dell'utente
    username TEXT NOT NULL,    -- Nome visualizzato
    created_at TEXT NOT NULL,  -- Data di creazione profilo (ISO format)
    height REAL,               -- Altezza in cm (opzionale)
    weight REAL,               -- Peso in kg (opzionale)
    preferences TEXT           -- JSON string per impostazioni (tema, lingua, ecc.)
);

-- ==========================================
-- Tabella SESSIONS
-- Rappresenta un singolo allenamento (workout).
-- Collega un utente a un periodo di tempo specifico.
-- ==========================================
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,       -- UUID univoco della sessione
    user_id TEXT NOT NULL,     -- Riferimento all'utente (Foreign Key)
    start_time TEXT NOT NULL,  -- Inizio allenamento
    end_time TEXT,             -- Fine allenamento (NULL se in corso)
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ==========================================
-- Tabella EXERCISES
-- Rappresenta ogni singolo esercizio o set svolto.
-- Es: "3 serie di Curl" o un singolo record per "10 ripetizioni"
-- ==========================================
CREATE TABLE IF NOT EXISTS exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- ID incrementale (1, 2, 3...)
    session_id TEXT NOT NULL,             -- Riferimento alla sessione
    name TEXT NOT NULL,                   -- Nome esercizio (es. "Bicep Curl")
    reps INTEGER,                         -- Numero di ripetizioni contate
    details TEXT,                         -- JSON string per angoli, feedback correttivi, ecc.
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP, -- Quando è stato registrato
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
