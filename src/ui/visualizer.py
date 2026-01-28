import cv2
import numpy as np
from config.settings import COLORS, THICKNESS
from config.translation_strings import i18n

class Visualizer:
    def __init__(self):
        """
        Gestisce tutta la logica di disegno su schermo.
        """
        # Mappa delle connessioni dello scheletro (Indici COCO Keypoints)
        # 5: Spalla SX, 7: Gomito SX, 9: Polso SX
        # 6: Spalla DX, 8: Gomito DX, 10: Polso DX
        # 11: Anca SX, 13: Ginocchio SX, 15: Caviglia SX
        # 12: Anca DX, 14: Ginocchio DX, 16: Caviglia DX
        self.connections = [
            (5, 7), (7, 9),       # Braccio SX
            (6, 8), (8, 10),      # Braccio DX
            (11, 13), (13, 15),   # Gamba SX
            (12, 14), (14, 16),   # Gamba DX
            (5, 6), (11, 12),     # Spalle e Anche
            (5, 11), (6, 12)      # Tronco
        ]

    def draw_skeleton(self, frame, keypoints):
        """
        Disegna le linee dello scheletro e i giunti sui keypoints rilevati.
        Expects keypoints as a numpy array of shape (17, 2) or similar via YOLO.
        """
        if keypoints is None or len(keypoints) == 0:
            return

        # 1. Disegna i Giunti (Cerchi)
        # 1. Disegna i Giunti (Cerchi)
        for row in keypoints:
            x, y = row[0], row[1] # Prendi solo x, y (ignorando confidence)
            # Ignora punti a (0,0) o con confidenza bassa (se filtrati prima)
            if x > 0 and y > 0:
                cv2.circle(frame, (int(x), int(y)), 5, COLORS["YELLOW"], -1)

        # 2. Disegna le Ossa (Linee)
        for idx_start, idx_end in self.connections:
            # Verifica che gli indici non escano dall'array (sicurezza)
            if idx_start < len(keypoints) and idx_end < len(keypoints):
                p1 = (int(keypoints[idx_start][0]), int(keypoints[idx_start][1]))
                p2 = (int(keypoints[idx_end][0]), int(keypoints[idx_end][1]))
                
                # Disegna solo se entrambi i punti sono validi
                if p1[0] > 0 and p1[1] > 0 and p2[0] > 0 and p2[1] > 0:
                    cv2.line(frame, p1, p2, COLORS["BLUE"], THICKNESS["SKELETON"])

    def draw_dashboard(self, frame, reps, state, feedback_key):
        """
        Disegna il pannello informativo (HUD) con conteggio e stato.
        """
        h, w, _ = frame.shape
        
        # --- 1. Ottimizzazione Overlay (ROI-based transparency) ---
        # Invece di copiare tutto il frame (lento), lavoriamo solo sulla ROI
        dashboard_h, dashboard_w = 180, 250
        
        # Safety check: se il frame è più piccolo della dashboard (improbabile ma possibile)
        if h < dashboard_h or w < dashboard_w:
             return

        # Estraiamo la Region of Interest (slicing numpy è reference, quindi veloce)
        # Ma per il blending ci serve modificarla, quindi va bene lavorarci su.
        roi = frame[0:dashboard_h, 0:dashboard_w]
        
        # Creiamo un blocco di colore solido delle stesse dimensioni della ROI
        # Nota: COLORS["OVERLAY_BG"] è una tupla (B, G, R). np.full vuole shape e fill_value.
        # fill_value broadcasta correttamente se passiamo la tupla colore.
        rect = np.full(roi.shape, COLORS["OVERLAY_BG"], dtype=np.uint8)
        
        # Applica trasparenza (alpha blending) solo sulla ROI
        alpha = 0.6
        # Risultato = (alpha * SRC1) + ((1 - alpha) * SRC2) + gamma
        # Qui SRC1 è il frame originale (sfondo), SRC2 è il rettangolo colorato (overlay)
        # Se vogliamo l'effetto scuro trasparente:
        # frame_pixel * 0.6 + rect_pixel * 0.4
        cv2.addWeighted(roi, alpha, rect, 1 - alpha, 0, roi)
        
        # Essendo 'roi' una vista del frame originale (se fatto via slicing), 
        # opencv addWeighted con dst=roi modifica in-place il frame originale?
        # Sì, se passiamo dst=roi.
        # frame[0:dashboard_h, 0:dashboard_w] = roi # Non strettamente necessario se dst=roi, ma esplicito è meglio.

        # --- 2. Testi Statici (Labels) ---
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Label REPS
        lbl_reps = i18n.get("ui_reps")
        cv2.putText(frame, f"{lbl_reps}: {reps}", (15, 50), 
                    font, 1.2, COLORS["WHITE"], 2, cv2.LINE_AA)

        # Label STATE
        lbl_state = i18n.get("ui_state")
        
        # Mappa stati interni -> Chiavi traduzione
        # Nota: 'up' e 'down' sono specifici del curl qui, in futuro si potrebbe generalizzare
        state_map = {
            "up": "curl_state_up",
            "down": "curl_state_down",
            "start": "state_start",
            "unknown": "state_unknown"
        }
        
        key = state_map.get(state, None)
        if key:
            translation = i18n.get(key)
            # Fallback banale se la chiave non esiste (es. "MISSING: ...")
            if not translation.startswith("MISSING"):
                display_state = translation
            else:
                display_state = state.upper()
        else:
            display_state = state.upper()

        cv2.putText(frame, f"{lbl_state}: {display_state}", (15, 100), 
                    font, 0.7, COLORS["YELLOW"], 2, cv2.LINE_AA)
        
        # --- 3. Feedback Dinamico (Grande e Centrale) ---
        self._draw_dynamic_feedback(frame, feedback_key, w)

    def _draw_dynamic_feedback(self, frame, feedback_key, width):
        """
        Gestisce il colore e la posizione del feedback correttivo.
        """
        if not feedback_key:
            return

        text = i18n.get(feedback_key)
        
        # Determina il colore in base al contenuto della chiave o del testo
        # Logica: "err" -> Rosso, "good/perfect" -> Verde, altro -> Giallo
        if "err" in feedback_key or "Extension" in text:
            color = COLORS["RED"]
        elif "good" in feedback_key or "perfect" in feedback_key:
            color = COLORS["GREEN"]
        else:
            color = COLORS["YELLOW"]

        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 1.0
        thickness = 2
        
        # Calcola la dimensione del testo per centrarlo
        text_size = cv2.getTextSize(text, font, scale, thickness)[0]
        text_x = (width - text_size[0]) // 2  # Centro orizzontale
        text_y = 50  # In alto, ma fuori dalla dashboard

        # Ombra nera per leggibilità (Stroke effect)
        cv2.putText(frame, text, (text_x + 2, text_y + 2), font, scale, COLORS["BLACK"], thickness + 2)
        # Testo colorato
        cv2.putText(frame, text, (text_x, text_y), font, scale, color, thickness)

    def draw_angle_arc(self, frame, center, angle_val):
        """
        (Opzionale) Disegna l'arco dell'angolo sul giunto (es. gomito).
        Center: tupla (x, y) del giunto.
        """
        if center[0] == 0: return

        # Visualizza il valore numerico vicino al giunto
        cv2.putText(frame, f"{int(angle_val)}", (int(center[0]) - 20, int(center[1]) - 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLORS["WHITE"], 2)