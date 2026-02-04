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

    def draw_dashboard(self, frame, exercise_name, reps, target_reps, current_set, target_sets, state, feedback_key):
        """
        Disegna il pannello informativo (HUD) con conteggio serie/ripetizioni e stato.
        """
        # --- 1. Nuova Dashboard "Modern Style" ---
        
        h, w, _ = frame.shape
        
        # Configurazione Layout
        margin = 20
        box_w = 300
        box_h = 250 # Aumentato per far stare Titolo + 3 righe
        x1, y1 = margin, margin
        x2, y2 = x1 + box_w, y1 + box_h
        
        # Disegna sfondo con angoli arrotondati
        self._draw_rounded_rect(frame, (x1, y1), (x2, y2), COLORS["OVERLAY_BG"], 
                                radius=15, alpha=0.7, border_color=COLORS["YELLOW"], border_thickness=1)

        # Separatori orizzontali (Ora 4 sezioni)
        row_h = box_h // 4
        y_line1 = y1 + row_h
        y_line2 = y1 + (row_h * 2)
        y_line3 = y1 + (row_h * 3)
        
        cv2.line(frame, (x1 + 10, y_line1), (x2 - 10, y_line1), COLORS["WHITE"], 1)
        cv2.line(frame, (x1 + 10, y_line2), (x2 - 10, y_line2), COLORS["WHITE"], 1)
        cv2.line(frame, (x1 + 10, y_line3), (x2 - 10, y_line3), COLORS["WHITE"], 1)

        # Font setup
        font_label = cv2.FONT_HERSHEY_SIMPLEX
        font_val = cv2.FONT_HERSHEY_DUPLEX
        
        # --- RIGA 1: TITOLO ESERCIZIO ---
        # Centrato
        title_text = exercise_name.upper()
        title_font_scale = 0.9
        title_size = cv2.getTextSize(title_text, font_val, title_font_scale, 2)[0]
        title_x = x1 + (box_w - title_size[0]) // 2
        
        cv2.putText(frame, title_text, (title_x, y_line1 - 25), font_val, title_font_scale, COLORS["YELLOW"], 2, cv2.LINE_AA)

        # --- RIGA 2: SETS (SERIE) ---
        lbl_set = i18n.get("ui_set").upper()
        cv2.putText(frame, lbl_set, (x1 + 20, y_line2 - 25), font_label, 0.7, COLORS["WHITE"], 1, cv2.LINE_AA)
        
        # Value "1 / 3"
        set_str = f"{current_set} / {target_sets}"
        set_size = cv2.getTextSize(set_str, font_val, 1.2, 2)[0]
        set_x = x2 - 20 - set_size[0]
        
        cv2.putText(frame, set_str, (set_x + 2, y_line2 - 22), font_val, 1.2, COLORS["BLACK"], 4, cv2.LINE_AA)
        cv2.putText(frame, set_str, (set_x, y_line2 - 24), font_val, 1.2, COLORS["YELLOW"], 2, cv2.LINE_AA)

        # --- RIGA 3: REPS (RIPETIZIONI) ---
        # Label "Reps"
        lbl_reps = i18n.get("ui_reps")
        cv2.putText(frame, lbl_reps, (x1 + 20, y_line3 - 25), font_label, 0.7, COLORS["WHITE"], 1, cv2.LINE_AA)
        
        # Value "5 / 8"
        reps_str = f"{reps} / {target_reps}"
        reps_size = cv2.getTextSize(reps_str, font_val, 1.2, 2)[0]
        reps_x = x2 - 20 - reps_size[0]
        
        cv2.putText(frame, reps_str, (reps_x + 2, y_line3 - 22), font_val, 1.2, COLORS["BLACK"], 4, cv2.LINE_AA)
        col_reps = COLORS["WHITE"]
        if reps >= target_reps: col_reps = COLORS["GREEN"] # Evidenzia completamento
        cv2.putText(frame, reps_str, (reps_x, y_line3 - 24), font_val, 1.2, col_reps, 2, cv2.LINE_AA)

        # --- RIGA 4: STATE (FASE) ---
        # Label "Fase"
        lbl_state = i18n.get("ui_state")
        cv2.putText(frame, lbl_state, (x1 + 20, y2 - 25), font_label, 0.7, COLORS["WHITE"], 1, cv2.LINE_AA)

        # Mapping stato -> icona e colore
        state_key_map = {
            "up": ("curl_state_up", COLORS["GREEN"], "up"),
            "down": ("curl_state_down", (0, 165, 255), "down"), # Orange/Reddish
            
            # Squat States
            "squat_up": ("squat_state_up", COLORS["GREEN"], "up"),
            "squat_down": ("squat_state_down", (0, 165, 255), "down"),
            
            # PushUp States
            "pushup_up": ("pushup_state_up", COLORS["GREEN"], "up"),
            "pushup_down": ("pushup_state_down", (0, 165, 255), "down"),
            
            "start": ("state_start", COLORS["WHITE"], "neutral"),
            "unknown": ("state_unknown", COLORS["GRAY"], "neutral")
        }
        
        tr_key, state_color, arrow_type = state_key_map.get(state, ("state_unknown", COLORS["GRAY"], "neutral"))
        state_text = i18n.get(tr_key)
        if state_text.startswith("MISSING"): state_text = state.upper()
        
        # Value Stato (Allineato a destra)
        # Troncare se troppo lungo (hard cap 18 chars)
        if len(state_text) > 20: state_text = state_text[:20] + "..."
        
        # Calcolo dimensione Label "Fase" per evitare overlap
        label_size = cv2.getTextSize(lbl_state, font_label, 0.7, 1)[0]
        label_end_x = x1 + 20 + label_size[0]
        
        val_end_x = x2 - 20
        max_val_width = val_end_x - (label_end_x + 20) # 20px padding
        
        font_scale_st = 0.9
        state_size = cv2.getTextSize(state_text, font_val, font_scale_st, 2)[0]
        
        # Riduci finché non entra (minimo 0.5)
        while state_size[0] > max_val_width and font_scale_st > 0.5:
            font_scale_st -= 0.1
            state_size = cv2.getTextSize(state_text, font_val, font_scale_st, 2)[0]
            
        st_x = val_end_x - state_size[0]
        
        cv2.putText(frame, state_text, (st_x + 2, y2 - 22), font_val, font_scale_st, COLORS["BLACK"], 4, cv2.LINE_AA)
        cv2.putText(frame, state_text, (st_x, y2 - 24), font_val, font_scale_st, state_color, 2, cv2.LINE_AA)

        # --- 3. Feedback Dinamico (Grande e Centrale) ---
        self._draw_dynamic_feedback(frame, feedback_key, w)

    def _draw_rounded_rect(self, img, pt1, pt2, color, radius=15, alpha=0.5, border_color=None, border_thickness=1):
        """
        Disegna un rettangolo arrotondato con riempimento semi-trasparente e bordo opzionale.
        Ottimizzato per Performance: usa ROI (Region of Interest) invece di copiare l'intera immagine.
        """
        x1, y1 = pt1
        x2, y2 = pt2
        
        # Validazione e Clamping coordinate (per sicurezza)
        h_img, w_img = img.shape[:2]
        x1 = max(0, min(x1, w_img))
        y1 = max(0, min(y1, h_img))
        x2 = max(0, min(x2, w_img))
        y2 = max(0, min(y2, h_img))
        
        # Assicuriamoci che x1 < x2 e y1 < y2
        if x1 >= x2 or y1 >= y2:
            return

        roi_w = x2 - x1
        roi_h = y2 - y1
        
        # 1. Estraiamo la ROI (Region of Interest) dall'immagine originale
        roi = img[y1:y2, x1:x2]
        
        # 2. Creiamo una copia della ROI su cui disegnare (buffer molto più piccolo del frame intero)
        overlay_roi = roi.copy()
        
        # 3. Disegniamo le forme su overlay_roi usando coordinate RELATIVE (0,0 è l'angolo in alto a sx della ROI)
        # Angoli (Cerchi)
        cv2.circle(overlay_roi, (radius, radius), radius, color, -1)
        cv2.circle(overlay_roi, (radius, roi_h - radius), radius, color, -1)
        cv2.circle(overlay_roi, (roi_w - radius, radius), radius, color, -1)
        cv2.circle(overlay_roi, (roi_w - radius, roi_h - radius), radius, color, -1)
        
        # Rettangoli di connessione (Corpo centrale)
        cv2.rectangle(overlay_roi, (radius, 0), (roi_w - radius, roi_h), color, -1)
        cv2.rectangle(overlay_roi, (0, radius), (roi_w, roi_h - radius), color, -1)
        
        # 4. Alpha Blending solo sulla ROI
        cv2.addWeighted(overlay_roi, alpha, roi, 1 - alpha, 0, roi)
        
        # 5. Reinseriamo la ROI nell'immagine originale (In-place modification)
        img[y1:y2, x1:x2] = roi
        
        # 6. Disegna il bordo (Opzionale) - Questo lo facciamo sull'immagine principale per semplicità
        if border_color and border_thickness > 0:
            # Linee rette
            cv2.line(img, (x1+radius, y1), (x2-radius, y1), border_color, border_thickness)
            cv2.line(img, (x1+radius, y2), (x2-radius, y2), border_color, border_thickness)
            cv2.line(img, (x1, y1+radius), (x1, y2-radius), border_color, border_thickness)
            cv2.line(img, (x2, y1+radius), (x2, y2-radius), border_color, border_thickness)
            
            # Archi per gli angoli
            cv2.ellipse(img, (x1+radius, y1+radius), (radius, radius), 180, 0, 90, border_color, border_thickness)
            cv2.ellipse(img, (x1+radius, y2-radius), (radius, radius), 90, 0, 90, border_color, border_thickness)
            cv2.ellipse(img, (x2-radius, y1+radius), (radius, radius), 270, 0, 90, border_color, border_thickness)
            cv2.ellipse(img, (x2-radius, y2-radius), (radius, radius), 0, 0, 90, border_color, border_thickness)

    def _draw_dumbbell_icon(self, img, center, color, size=20):
        """Disegna un'icona stilizzata di un manubrio."""
        cx, cy = center
        half = size // 2
        # Asta
        cv2.line(img, (cx - half, cy), (cx + half, cy), color, 2)
        # Pesi (rettangoli arrotondati o linee spesse)
        cv2.rectangle(img, (cx - half - 4, cy - half + 2), (cx - half, cy + half - 2), color, -1)
        cv2.rectangle(img, (cx + half, cy - half + 2), (cx + half + 4, cy + half - 2), color, -1)

    def _draw_arrow_icon(self, img, center, color, size=15, direction="neutral"):
        """Disegna un'icona freccia SU o GIU."""
        cx, cy = center
        half = size // 2
        
        if direction == "up":
            # Freccia SU
            pts = np.array([
                [cx, cy - half - 2],        # Punta
                [cx - half, cy + 2],   # Sinistra
                [cx + half, cy + 2]    # Destra
            ])
            cv2.fillPoly(img, [pts], color)
            # Corpo rettangolare sotto
            cv2.rectangle(img, (cx - 2, cy + 2), (cx + 2, cy + half + 4), color, -1)
            
        elif direction == "down":
            # Freccia GIU
            pts = np.array([
                [cx, cy + half + 2],        # Punta
                [cx - half, cy - 2],   # Sinistra
                [cx + half, cy - 2]    # Destra
            ])
            cv2.fillPoly(img, [pts], color)
            # Corpo rettangolare sopra
            cv2.rectangle(img, (cx - 2, cy - half - 4), (cx + 2, cy - 2), color, -1)
            
        else:
            # Cerchio o quadrato per neutral
            cv2.circle(img, (cx, cy), half // 2, color, -1)

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

    def draw_dashboard_from_state(self, frame, state):
        """
        Adapter method to draw dashboard using the UIState dataclass.
        """
        # Draw Skeleton first if keypoints exist
        if state.keypoints is not None:
             self.draw_skeleton(frame, state.keypoints)

        self.draw_dashboard(
            frame,
            exercise_name=state.exercise_name,
            reps=state.reps,
            target_reps=state.target_reps,
            current_set=state.current_set,
            target_sets=state.target_sets,
            state=state.state,
            feedback_key=state.feedback_key
        )
        
        # Overlays for REST/FINISHED
        if state.workout_state == "REST":
            self._draw_overlay_message(frame, i18n.get("ui_rest_title"), i18n.get("ui_rest_subtitle"))
        elif state.workout_state == "FINISHED":
            self._draw_overlay_message(frame, i18n.get("ui_finish_title"), i18n.get("ui_finish_subtitle"))
            
        return frame

    def _draw_overlay_message(self, frame, title, subtitle):
        h, w, _ = frame.shape
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        font = cv2.FONT_HERSHEY_DUPLEX
        t_size = cv2.getTextSize(title, font, 2.0, 3)[0]
        t_x = (w - t_size[0]) // 2
        t_y = (h // 2) - 20
        cv2.putText(frame, title, (t_x, t_y), font, 2.0, (0, 255, 0), 3, cv2.LINE_AA)
        
        s_size = cv2.getTextSize(subtitle, font, 1.0, 2)[0]
        s_x = (w - s_size[0]) // 2
        s_y = (h // 2) + 40
        cv2.putText(frame, subtitle, (s_x, s_y), font, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
