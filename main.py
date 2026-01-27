import cv2
import sys
import logging
from ultralytics import YOLO

# Imports dai tuoi moduli (Architecture)
from src.infrastructure.webcam import WebcamSource
from src.exercises.curl import BicepCurl

# Configurazione Logging (Per debugging professionale)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log"), # Salva su file
        logging.StreamHandler(sys.stdout)    # Stampa su terminale
    ]
)

def main():
    logging.info("--- Avvio Virtual AI Spotter ---")

    # 1. Caricamento del Modello AI (YOLOv8 Pose)
    # La prima volta scaricherà automaticamente 'yolov8n-pose.pt'
    try:
        logging.info("Caricamento modello YOLOv8...")
        model = YOLO('assets/models/yolov8n-pose.pt') 
        # Forziamo l'uso della GPU (CUDA) se disponibile
        model.to('cuda') 
        logging.info(f"Modello caricato su: {model.device}")
    except Exception as e:
        logging.error(f"Errore caricamento modello: {e}")
        return

    # 2. Inizializzazione Hardware (Webcam)
    try:
        cam = WebcamSource(source_index=0)
        logging.info("Webcam inizializzata.")
    except Exception as e:
        logging.error(f"Errore Webcam: {e}")
        return

    # 3. Inizializzazione Esercizio (Dependency Injection)
    # Configuriamo un Curl col braccio DESTRO
    curl_exercise = BicepCurl(config={
        "side": "right", 
        "up_angle": 35,      # Soglia flessione
        "down_angle": 160    # Soglia estensione
    })
    logging.info("Esercizio Bicep Curl configurato.")

    # --- MAIN LOOP (Il cuore dell'app) ---
    print("\nPREMI 'q' PER USCIRE\n")
    
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
            # Plot disegna già lo scheletro di base
            annotated_frame = results[0].plot() 
            
            # Verifichiamo se YOLO ha trovato keypoints
            # Controlliamo semplicemente se 'conf' (confidence) esiste ed è popolato
            if results[0].keypoints is not None and results[0].keypoints.data.shape[0] > 0:
                
                # ORA è sicuro chiamare l'indice [0] perché sappiamo che c'è qualcuno
                keypoints = results[0].keypoints.data[0].cpu().numpy()
                
                # Passiamo i dati alla logica dell'esercizio
                analysis = curl_exercise.process_frame(keypoints)

                # D. UI Overlay (Disegno Dati)
                # ... (il resto del codice di disegno rimane uguale) ...
                cv2.rectangle(annotated_frame, (0, 0), (250, 150), (245, 117, 16), -1)
                
                # Reps
                cv2.putText(annotated_frame, 'REPS', (15, 25), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
                cv2.putText(annotated_frame, str(analysis.reps), (10, 70), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2, cv2.LINE_AA)
                
                # Stage (Up/Down)
                cv2.putText(annotated_frame, 'STAGE', (95, 25), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
                cv2.putText(annotated_frame, analysis.stage, (90, 70), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

                # Feedback
                color_feedback = (0, 255, 0) if analysis.is_valid else (0, 0, 255)
                cv2.putText(annotated_frame, f"Angolo: {int(analysis.angle)}", (10, 100), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                cv2.putText(annotated_frame, analysis.correction, (10, 130), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_feedback, 1, cv2.LINE_AA)

            # E. Output a Video
            cv2.imshow('Virtual AI Spotter', annotated_frame)

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