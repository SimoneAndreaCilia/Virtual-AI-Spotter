-- ==========================================
-- USERS table
-- Represents the athletes who use the application.
-- Contains personal data, biometrics, and configurations.
-- ==========================================
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,       -- UUID unique user identifier
    username TEXT NOT NULL,    -- Display name
    created_at TEXT NOT NULL,  -- Profile creation date (ISO format)
    height REAL,               -- Height in cm (optional)
    weight REAL,               -- Weight in kg (optional)
    preferences TEXT           -- JSON string for settings (theme, language, etc.)
);

-- ==========================================
-- SESSIONS table
-- Represents a single workout session.
-- Links a user to a specific time period.
-- ==========================================
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,       -- UUID unique session identifier
    user_id TEXT NOT NULL,     -- Reference to the user (Foreign Key)
    start_time TEXT NOT NULL,  -- Start of the workout
    end_time TEXT,             -- End of the workout (NULL if in progress)
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ==========================================
-- EXERCISES table
-- Represents each individual exercise or set performed.
-- Example: "3 sets of Curl" or a single record for "10 reps"
-- ==========================================
CREATE TABLE IF NOT EXISTS exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- Incremental ID (1, 2, 3...)
    session_id TEXT NOT NULL,             -- Reference to the session (Foreign Key)
    name TEXT NOT NULL,                   -- Exercise name (e.g. "Bicep Curl")
    reps INTEGER,                         -- Number of repetitions counted
    details TEXT,                         -- JSON string for angles, corrective feedback, etc.
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP, -- When it was registered
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
