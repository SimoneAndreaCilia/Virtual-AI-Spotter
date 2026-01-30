import cv2
import sys
import logging
import time
from ultralytics import YOLO

# Imports dai tuoi moduli (Architecture)
from src.infrastructure.webcam import WebcamSource
from src.core.factory import ExerciseFactory
from src.ui.visualizer import Visualizer
from src.data.db_manager import DatabaseManager
from src.core.entities.user import User
from src.core.entities.session import Session

from config.settings import (
    MODEL_PATH, DEVICE, CAMERA_ID, 
    CURL_THRESHOLDS, SQUAT_THRESHOLDS, LOGS_DIR
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

def select_exercise_settings():
    """
    Chiede all'utente quale esercizio svolgere e le impostazioni (Serie/Reps).
    Restituisce: (exercise_name, config_dict, target_sets, target_reps)
    """
    print("\n" + "="*40)
    print(f" {i18n.get('ui_title').upper()} - {i18n.get('ui_workout_setup')}")
    print("="*40)
    
    # 1. Scelta Esercizio
    print(" 1. Bicep Curl")
    print(" 2. Squat")
    
    ex_choice = input(f"\n{i18n.get('ui_quit')} ({i18n.get('ui_select_ex')}): ").strip()
    
    exercise_name = "Bicep Curl"
    config = {}
    
    if ex_choice == '2':
        exercise_name = "Squat"
        config = {
            "up_angle": SQUAT_THRESHOLDS["UP_ANGLE"],
            "down_angle": SQUAT_THRESHOLDS["DOWN_ANGLE"]
        }
    else:
        # Default o Scelta 1
        exercise_name = "Bicep Curl"
        config = {
            "up_angle": CURL_THRESHOLDS["UP_ANGLE"],
            "down_angle": CURL_THRESHOLDS["DOWN_ANGLE"]
        }
        
    print(f" -> {i18n.get('ui_selected')}: {exercise_name}")

    # 2. Scelta Lato (Solo per Curl o Squat asimmetrici, ma lo teniamo generico)
    # Per semplicità lo chiediamo sempre, default Right
    side_choice = input(f" {i18n.get('ui_side_choice')}: ").strip().upper()
    if side_choice == 'L':
        config["side"] = "left"
    elif side_choice == 'B':
        config["side"] = "both"
    else:
        config["side"] = "right"
        
    # Visualizza la scelta localizzata (es. side_left -> SINISTRO, side_both -> ENTRAMBI)
    side_key = f"side_{config['side']}"
    print(f" -> {i18n.get('ui_side_val')}: {i18n.get(side_key)}")

    # 3. Scelta Serie e Ripetizioni
    print(f"\n [{i18n.get('ui_settings')}]")
    try:
        sets_input = input(f" {i18n.get('ui_target_sets')}: ").strip()
        target_sets = int(sets_input) if sets_input else 3
        
        reps_input = input(f" {i18n.get('ui_target_reps')}: ").strip()
        target_reps = int(reps_input) if reps_input else 8
    except ValueError:
        print(" ! Invalid input. Using defaults (3x8).")
        target_sets = 3
        target_reps = 8
        
    print(f" -> {i18n.get('ui_goal')}: {target_sets} Sets x {target_reps} Reps")
    print("="*40)
    input(f"\n{i18n.get('ui_start_prompt')}")
    
    return exercise_name, config, target_sets, target_reps

def main():
    # 0. UI Iniziale (Console)
    select_language()
    
    # [NEW] Selezione Esercizio e Target
    ex_name, ex_config, target_sets, target_reps = select_exercise_settings()

    logging.info("--- Avvio Virtual AI Spotter ---")
    
    # Inizializzazione Database
    try:
        logging.info("Inizializzazione Database...")
        db_manager = DatabaseManager()
        
        # Carica Utente (o crea Default)
        current_user = db_manager.get_user()
        if not current_user:
            logging.info("Nessun utente trovato. Creazione utente Default.")
            current_user = User(username="Athlete", height=175.0, weight=70.0)
            db_manager.save_user(current_user)
        else:
            logging.info(f"Bentornato, {current_user.username}!")
            
        # Crea Nuova Sessione con Targets
        current_session = Session(
            user_id=current_user.id,
            target_sets=target_sets,
            target_reps=target_reps
        )
        logging.info(f"Nuova sessione avviata: {current_session.id}")
        
    except Exception as e:
        logging.critical(f"Errore inizializzazione DB: {e}", exc_info=True)
        return

    # 1. Caricamento del Modello AI (YOLOv8 Pose)
    try:
        logging.info(f"Caricamento modello YOLOv8 da {MODEL_PATH}...")
        model = YOLO(MODEL_PATH) 
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
    visualizer = Visualizer()
    
    # [NEW] Creazione Esercizio tramite Factory
    current_exercise = ExerciseFactory.create_exercise(ex_name, ex_config)
    logging.info(f"Esercizio {ex_name} configurato.")
    
    # --- LOGICA DI STATO DEL WORKOUT ---
    current_set = 1
    workout_state = "EXERCISE" # EXERCISE | REST | FINISHED
    
    # Messaggio overlay per il REST/FINISHED
    overlay_message = ""
    
    print(f"\n{i18n.get('ui_quit')}\n")
    
    try:
        while True:
            # A. Input
            ret, frame = cam.get_frame()
            if not ret:
                logging.warning("Frame non ricevuto.")
                break

            # B. Check completamento sessione
            if workflow_completed(current_set, target_sets):
                workout_state = "FINISHED"

            # C. Inference (AI) - Solo se non siamo FINISHED (o facciamo comunque tracking?)
            # Facciamo tracking sempre per vedere se l'utente si muove anche in pausa
            results = model(frame, verbose=False) 
            display_frame = frame.copy()

            dashboard_reps = 0
            dashboard_state = "start"
            dashboard_feedback = ""

            # Check se abbiamo persone
            if results[0].keypoints is not None and results[0].keypoints.data.shape[0] > 0:
                keypoints = results[0].keypoints.data[0].cpu().numpy()
                visualizer.draw_skeleton(display_frame, keypoints)

                if workout_state == "EXERCISE":
                    # --- 2. Analisi Esercizio ---
                    # Passiamo il timestamp attuale per gestire correttamente lo smoothing OneEuro
                    analysis = current_exercise.process_frame(keypoints, timestamp=time.time())
                    
                    dashboard_reps = analysis.reps
                    dashboard_state = analysis.stage
                    dashboard_feedback = analysis.correction
                    
                    # [NEW] Logica Completamento Set
                    if analysis.reps >= target_reps:
                        # SET COMPLETATO!
                        logging.info(f"Set {current_set} completed!")
                        
                        # 1. Salva il set nella sessione
                        current_session.add_exercise({
                            "name": ex_name,
                            "set_index": current_set,
                            "reps": analysis.reps,
                            "config": ex_config
                        })
                        
                        # 2. Passa a Pausa (o Finish se era l'ultimo)
                        if current_set >= target_sets:
                            workout_state = "FINISHED"
                            current_session.end_session()
                            db_manager.save_session(current_session)
                        else:
                            workout_state = "REST"
                        
                        # Resetta contatore esercizio per il prossimo set
                        current_exercise.reset()

            # --- D. UI Overlay ---
            
            # Recupera nome tradotto dell'esercizio
            # Se ex_name è "Bicep Curl", key="curl_name". Se "Squat", key="squat_name".
            if "curl" in ex_name.lower():
                display_name = i18n.get("curl_name")
            elif "squat" in ex_name.lower():
                display_name = i18n.get("squat_name")
            else:
                display_name = ex_name

            # Mostra Dashboard (Standard)
            visualizer.draw_dashboard(
                display_frame,
                exercise_name=display_name,
                reps=dashboard_reps,
                target_reps=target_reps,
                current_set=current_set if current_set <= target_sets else target_sets,
                target_sets=target_sets,
                state=dashboard_state,
                feedback_key=dashboard_feedback
            )
            
            # Overlay Speciali (REST / FINISHED)
            if workout_state == "REST":
                draw_overlay_message(display_frame, i18n.get("ui_rest_title"), i18n.get("ui_rest_subtitle"))
            elif workout_state == "FINISHED":
                draw_overlay_message(display_frame, i18n.get("ui_finish_title"), i18n.get("ui_finish_subtitle"))

            # E. Output a Video
            cv2.imshow(i18n.get('ui_title'), display_frame)

            # F. Gestione Input Tastiera
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            
            if workout_state == "REST" and (key == ord('c') or key == ord('C')):
                # Inizia prossimo set
                current_set += 1
                workout_state = "EXERCISE"
                logging.info(f"Starting Set {current_set}")

    except Exception as e:
        logging.critical(f"Crash improvviso: {e}", exc_info=True)
    finally:
        # G. Cleanup
        cam.release()
        cv2.destroyAllWindows()
        
        # Salvataggio di sicurezza se uscito forzatamente ma non finito
        if 'current_session' in locals() and not current_session.end_time:
             # Se la sessione non è stata chiusa (es. Quit a metà)
             pass # Si potrebbe salvare parziale, ma lasciamo così per ora

        logging.info("Applicazione chiusa correttamente.")

def workflow_completed(current_set, target_sets):
    return current_set > target_sets

def draw_overlay_message(frame, title, subtitle):
    """
    Disegna un overlay scuro a tutto schermo con un messaggio centrale.
    """
    h, w, _ = frame.shape
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
    
    font = cv2.FONT_HERSHEY_DUPLEX
    
    # Title
    t_size = cv2.getTextSize(title, font, 2.0, 3)[0]
    t_x = (w - t_size[0]) // 2
    t_y = (h // 2) - 20
    cv2.putText(frame, title, (t_x, t_y), font, 2.0, (0, 255, 0), 3, cv2.LINE_AA)
    
    # Subtitle
    s_size = cv2.getTextSize(subtitle, font, 1.0, 2)[0]
    s_x = (w - s_size[0]) // 2
    s_y = (h // 2) + 40
    cv2.putText(frame, subtitle, (s_x, s_y), font, 1.0, (255, 255, 255), 2, cv2.LINE_AA)

if __name__ == "__main__":
    main()