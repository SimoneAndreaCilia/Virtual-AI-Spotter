import cv2
import sys
import logging
from ultralytics import YOLO

# Imports dai tuoi moduli (Architecture)
from src.infrastructure.webcam import WebcamSource
from src.exercises.curl import BicepCurl
from src.ui.visualizer import Visualizer
from config.settings import (
    MODEL_PATH, DEVICE, CAMERA_ID, 
    CURL_THRESHOLDS, LOGS_DIR
)
from config.translation_strings import i18n

# Configurazione Logging (Per debugging professionale)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"{LOGS_DIR}/app.log"), # Salva su file
        logging.StreamHandler(sys.stdout)    # Stampa su terminale
    ]
)

def select_language():
    """Chiede all'utente di selezionare la lingua all'avvio."""
    print("\n" + "="*40)
    print(" VIRTUAL AI SPOTTER - LANGUAGE SELECTION")
    print("="*40)
    print(" [I] Italiano")
    print(" [E] English")
    print("="*40)
    
    while True:
        choice = input("Select Language (I/E): ").strip().upper()
        if choice == 'I':
            i18n.set_language("IT")
            print(" -> Lingua impostata: ITALIANO")
            break
        elif choice == 'E':
            i18n.set_language("EN")
            print(" -> Language set: ENGLISH")
            break
        else:
            print("Invalid choice. Please press 'I' or 'E'.")

def main():
    # 0. Selezione Lingua
    select_language()

    logging.info("--- Avvio Virtual AI Spotter ---")

    # 1. Caricamento del Modello AI (YOLOv8 Pose)
    try:
        logging.info(f"Caricamento modello YOLOv8 da {MODEL_PATH}...")
        model = YOLO(MODEL_PATH) 
        # Forziamo l'uso della GPU (CUDA) se disponibile
        model.to(DEVICE) 
        logging.info(f"Modello caricato su: {model.device}")
    except Exception as e:
        logging.error(f"Errore caricamento modello: {e}")
        return

    # 2. Inizializzazione Hardware (Webcam)
    try:
        cam = WebcamSource(source_index=CAMERA_ID)
        logging.info(f"Webcam inizializzata (ID: {CAMERA_ID}).")
    except Exception as e:
        logging.error(f"Errore Webcam: {e}")
        return

    # 3. Inizializzazione Componenti (Exercise & UI)
    
    # Visualizer: gestisce tutta la grafica
    visualizer = Visualizer()
    
    # Configuriamo un Curl col braccio DESTRO usando i parametri da settings
    curl_exercise = BicepCurl(config={
        "side": "right", 
        "up_angle": CURL_THRESHOLDS["UP_ANGLE"],
        "down_angle": CURL_THRESHOLDS["DOWN_ANGLE"]
    })
    logging.info("Esercizio Bicep Curl configurato.")

    # --- MAIN LOOP (Il cuore dell'app) ---
    print(f"\n{i18n.get('ui_quit')}\n")
    
    try:
        while True:
            # A. Input
            ret, frame = cam.get_frame()
            if not ret:
                logging.warning("Frame non ricevuto.")
                break

            # B. Inference (AI)
            # verbose=False riduce lo spam nel terminale
            results = model(frame, verbose=False) 
            
            # C. Elaborazione Logica
            # Prendiamo il primo risultato (c'è solo una persona?)
            # Non usiamo più results[0].plot() per avere il controllo totale sulla grafica
            # annotatated_frame = results[0].plot() # RIMOSSO per usare Visualizer
            
            # Usiamo una copia del frame originale per disegnare
            display_frame = frame.copy()

            # Verifichiamo se YOLO ha trovato keypoints
            if results[0].keypoints is not None and results[0].keypoints.data.shape[0] > 0:
                
                # ORA è sicuro chiamare l'indice [0] perché sappiamo che c'è qualcuno
                keypoints = results[0].keypoints.data[0].cpu().numpy()
                
                # 1. Disegna Scheletro Custom
                visualizer.draw_skeleton(display_frame, keypoints)

                # 2. Analisi Esercizio
                analysis = curl_exercise.process_frame(keypoints)

                # 3. UI Overlay (Dashboard & Feedback)
                # Nota: 'analysis' contiene i dati grezzi, Visualizer sa come mostrarli
                # analysis.correction ora dovrebbe essere una CHIAVE di traduzione o testo
                # Per ora assumiamo che BicepCurl ritorni stringhe o chiavi. 
                # (Se BicepCurl ritorna testo fisso, Visualizer proverà a tradurlo o lo mostrerà così com'è)
                
                visualizer.draw_dashboard(
                    display_frame, 
                    reps=analysis.reps, 
                    state=analysis.stage, 
                    feedback_key=analysis.correction # Passiamo la stringa di correzione
                )
                
                # Opzionale: Disegna angolo gomito direttamente sul giunto
                # Trova giunto gomito destro (index 8) o sinistro (7) in base alla config
                elbow_idx = 8 if curl_exercise.side == "right" else 7
                if len(keypoints) > elbow_idx:
                    visualizer.draw_angle_arc(display_frame, keypoints[elbow_idx], analysis.angle)

            # E. Output a Video
            cv2.imshow(i18n.get('ui_title'), display_frame)

            # F. Gestione Uscita
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        logging.critical(f"Crash improvviso: {e}", exc_info=True)
    finally:
        # G. Cleanup (Rilascio risorse)
        cam.release()
        cv2.destroyAllWindows()
        logging.info("Applicazione chiusa correttamente.")

if __name__ == "__main__":
    main()