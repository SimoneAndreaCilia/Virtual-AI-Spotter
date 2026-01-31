import os

# --- 1. CONFIGURAZIONE PERCORSI (PATHS) ---
# Calcola dinamicamente la root del progetto per evitare errori "File not found"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Percorsi assoluti alle risorse
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
MODELS_DIR = os.path.join(ASSETS_DIR, "models")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
DB_PATH = os.path.join(BASE_DIR, "src", "data", "gym_data.db")

# --- 2. CONFIGURAZIONE AI & MODELLO ---
MODEL_NAME = "yolov8n-pose.pt" # Modello Nano (più veloce) o 'yolov8s-pose.pt' (più preciso)
MODEL_PATH = os.path.join(MODELS_DIR, MODEL_NAME)
CONFIDENCE_THRESHOLD = 0.5     # Ignora rilevamenti con confidenza < 50%
DEVICE = "cuda"                # Usa "cpu" se non hai una GPU NVIDIA, "cuda" o "mps" (Mac)

# --- 3. CONFIGURAZIONE CAMERA ---
CAMERA_ID = 0           # 0 per webcam integrata, 1 per esterna
FRAME_WIDTH = 1280      # Risoluzione desiderata (HD)
FRAME_HEIGHT = 720
FPS = 30

# --- 4. LOGICA ESERCIZI (SOGLIE ANGOLARI) ---
# Modifica questi valori per calibrare la difficoltà degli esercizi

# Parametri Squat
SQUAT_THRESHOLDS = {
    "UP_ANGLE": 160,       # Gamba quasi dritta (In piedi)
    "DOWN_ANGLE": 90,      # Accosciata parallela (Orizzontale)
    "WARN_ANGLE": 110      # Soglia di avvertimento "Scendi di più"
}

# Parametri Bicep Curl
CURL_THRESHOLDS = {
    "UP_ANGLE": 30,        # Massima contrazione (Mani vicino alle spalle)
    "DOWN_ANGLE": 160,     # Braccio disteso
    "ERROR_ELBOW": 15      # Tolleranza movimento gomito (se si muove troppo è errore)
}

# Parametri Push Up
PUSHUP_THRESHOLDS = {
    "UP_ANGLE": 160,       # Arms extended
    "DOWN_ANGLE": 90,      # Arms bent at 90 degrees
    "FORM_ANGLE_MIN": 160  # Body line tolerance (approx 180 is straight)
}

# Parametri Smoothing (Strutture Dati)
BUFFER_SIZE = 10           # Numero di frame per la media mobile (riduce il tremolio)
HYSTERESIS_TOLERANCE = 5   # Tolleranza (gradi) per il debouncing del cambio stato (es. +5/-5)

# --- 5. VISUALIZZAZIONE (UI) ---
# Colori in formato BGR (Blue, Green, Red) per OpenCV
COLORS = {
    "WHITE": (255, 255, 255),
    "BLACK": (0, 0, 0),
    "GREEN": (0, 255, 0),      # Successo / Form Corretta
    "RED": (0, 0, 255),        # Errore / Form Errata
    "YELLOW": (0, 255, 255),   # Warning / Info / Giunti
    "BLUE": (255, 0, 0),       # Scheletro
    "GRAY": (128, 128, 128),   # Grigio standard
    "OVERLAY_BG": (40, 40, 40) # Sfondo scuro semitrasparente
}

# Spessori linee
THICKNESS = {
    "SKELETON": 2,
    "TEXT": 2,
    "BOX": -1  # -1 riempie la forma
}