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

    def draw_dashboard(self, frame, reps, state, feedback_key):
        """
        Disegna il pannello informativo (HUD) con conteggio e stato.
        """
        # --- 1. Nuova Dashboard "Modern Style" ---
        
        h, w, _ = frame.shape
        
        # Configurazione Layout
        margin = 20
        box_w = 300  # Aumentato da 260 a 300 per evitare overlap
        box_h = 160
        x1, y1 = margin, margin
        x2, y2 = x1 + box_w, y1 + box_h
        
        # Disegna sfondo con angoli arrotondati
        self._draw_rounded_rect(frame, (x1, y1), (x2, y2), COLORS["OVERLAY_BG"], 
                                radius=15, alpha=0.7, border_color=COLORS["YELLOW"], border_thickness=1)

        # Separatore orizzontale
        center_y = y1 + (box_h // 2)
        cv2.line(frame, (x1 + 10, center_y), (x2 - 10, center_y), COLORS["WHITE"], 1)

        # Font setup
        font_label = cv2.FONT_HERSHEY_SIMPLEX
        font_val = cv2.FONT_HERSHEY_DUPLEX
        
        # --- SEZIONE ALTA: RIPETIZIONI ---
        # Icona Dumbbell (semplici cerchi + linea)
        icon_x = x1 + 30
        row1_y = y1 + (box_h // 4)
        self._draw_dumbbell_icon(frame, (icon_x, row1_y), color=COLORS["WHITE"], size=20)
        
        # Etichetta "Reps"
        lbl_reps = i18n.get("ui_reps")
        cv2.putText(frame, lbl_reps, (x1 + 60, row1_y + 8), font_label, 0.7, COLORS["WHITE"], 1, cv2.LINE_AA)
        
        # Valore Numerico (Allineato a destra)
        reps_str = str(reps)
        reps_size = cv2.getTextSize(reps_str, font_val, 1.5, 2)[0]
        reps_x = x2 - 20 - reps_size[0]
        
        # Ombra + Testo
        cv2.putText(frame, reps_str, (reps_x + 2, row1_y + 12), font_val, 1.5, COLORS["BLACK"], 4, cv2.LINE_AA)
        cv2.putText(frame, reps_str, (reps_x, row1_y + 10), font_val, 1.5, COLORS["WHITE"], 2, cv2.LINE_AA)

        # --- SEZIONE BASSA: FASE (STATE) ---
        # Mapping stato -> icona e colore
        state_key_map = {
            "up": ("curl_state_up", COLORS["GREEN"], "up"),
            "down": ("curl_state_down", (0, 165, 255), "down"), # Orange/Reddish
            "start": ("state_start", COLORS["WHITE"], "neutral"),
            "unknown": ("state_unknown", COLORS["GRAY"], "neutral")
        }
        
        tr_key, state_color, arrow_type = state_key_map.get(state, ("state_unknown", COLORS["GRAY"], "neutral"))
        state_text = i18n.get(tr_key)
        if state_text.startswith("MISSING"): state_text = state.upper()

        row2_y = center_y + (box_h // 4)
        
        # Icona Freccia
        self._draw_arrow_icon(frame, (icon_x, row2_y), color=state_color, size=15, direction=arrow_type)

        # Etichetta "Fase"
        lbl_state = i18n.get("ui_state")
        cv2.putText(frame, lbl_state, (x1 + 60, row2_y + 8), font_label, 0.7, COLORS["WHITE"], 1, cv2.LINE_AA)

        # Calcolo precisi spazi per evitare overlap
        label_size = cv2.getTextSize(lbl_state, font_label, 0.7, 1)[0]
        label_end_x = x1 + 60 + label_size[0]
        
        # Spazio disponibile per il valore = (Fine Box - Padding) - (Fine Label + Padding)
        val_end_x = x2 - 20
        max_val_width = val_end_x - (label_end_x + 15) # 15px di sicurezza
        
        # Valore Stato (Allineato a destra)
        # Troncare se troppo lungo (hard cap 15 chars)
        if len(state_text) > 15: state_text = state_text[:15] + "..."
        
        font_scale_st = 1.0
        state_size = cv2.getTextSize(state_text, font_val, font_scale_st, 2)[0]
        
        # Riduci finché non entra (minimo 0.4)
        while state_size[0] > max_val_width and font_scale_st > 0.4:
            font_scale_st -= 0.1
            state_size = cv2.getTextSize(state_text, font_val, font_scale_st, 2)[0]

        st_x = val_end_x - state_size[0]
        
        # Ombra + Testo
        cv2.putText(frame, state_text, (st_x + 2, row2_y + 12), font_val, font_scale_st, COLORS["BLACK"], 4, cv2.LINE_AA)
        cv2.putText(frame, state_text, (st_x, row2_y + 10), font_val, font_scale_st, state_color, 2, cv2.LINE_AA)

        # --- 3. Feedback Dinamico (Grande e Centrale) ---
        self._draw_dynamic_feedback(frame, feedback_key, w)

    def _draw_rounded_rect(self, img, pt1, pt2, color, radius=15, alpha=0.5, border_color=None, border_thickness=1):
        """
        Disegna un rettangolo arrotondato con riempimento semi-trasparente e bordo opzionale.
        """
        x1, y1 = pt1
        x2, y2 = pt2
        
        # Crea overlay per la trasparenza
        overlay = img.copy()
        
        # Disegna i 4 cerchi agli angoli e i rettangoli di connessione (sul layer overlay)
        # Angoli
        cv2.circle(overlay, (x1+radius, y1+radius), radius, color, -1)
        cv2.circle(overlay, (x1+radius, y2-radius), radius, color, -1)
        cv2.circle(overlay, (x2-radius, y1+radius), radius, color, -1)
        cv2.circle(overlay, (x2-radius, y2-radius), radius, color, -1)
        
        # Corpi centrali
        cv2.rectangle(overlay, (x1+radius, y1), (x2-radius, y2), color, -1)
        cv2.rectangle(overlay, (x1, y1+radius), (x2, y2-radius), color, -1)
        
        # Applica alpha blending
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
        
        # Disegna il bordo (se richiesto) direttamente sull'immagine finale (non trasparente)
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