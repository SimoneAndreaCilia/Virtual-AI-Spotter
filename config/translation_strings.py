# config/translation_strings.py

TRANSLATIONS = {
    "IT": {
        # --- UI GENERALE ---
        "ui_title": "Virtual AI Spotter",
        "ui_select_lang": "Premi 'I' per Italiano | Press 'E' for English",
        "ui_quit": "Premi 'Q' per Uscire",
        "ui_reps": "Ripetizioni",
        "ui_set": "Serie",
        "ui_state": "Fase",
        "ui_fps": "FPS",
        
        # --- BICEP CURL (Feedback) ---
        "curl_name": "Curl Bicipiti",
        "curl_state_up": "SU (Contrazione)",
        "curl_state_down": "GIU (Estensione)",
        
        # Feedback correttivi (Errori comuni)
        "curl_err_extension": "Stendi tutto il braccio! (Angolo > 160°)",
        "curl_err_flexion": "Sali di piu'! Chiudi l'angolo.",
        "curl_err_elbow": "Gomito troppo avanti! Tienilo fermo.",
        
        # Feedback positivi
        "curl_good_rep": "Ottima ripetizione!",
        "curl_perfect_form": "Forma perfetta!",
        "err_body_not_visible": "Corpo non visibile",
        "state_unknown": "SCONOSCIUTO",
        "state_start": "PRONTO",
        
        # --- SQUAT (Feedback) ---
        "squat_name": "Squat",
        "squat_state_up": "SU (In Piedi)",
        "squat_state_down": "GIU (Accosciata)",
        "squat_perfect_form": "Ottimo Squat!",
        "squat_err_depth": "Scendi di più! (Sotto 90°)",
        
        # --- NEW CLI & OVERLAY STRINGS ---
        "ui_workout_setup": "IMPOSTAZIONE WORKOUT",
        "ui_select_ex": "Seleziona Esercizio (1-2)",
        "ui_selected": "Selezionato",
        "ui_side_choice": "Lato (Sinistro 'L' / Destro 'R' / Entrambi 'B') [Default R]",
        "ui_side_val": "LATO",
        "side_left": "SINISTRO",
        "side_right": "DESTRO",
        "side_both": "ENTRAMBI",
        "ui_settings": "Impostazioni",
        "ui_target_sets": "Quante Serie? [Default 3]",
        "ui_target_reps": "Quante Ripetizioni per Serie? [Default 8]",
        "ui_goal": "Obiettivo",
        "ui_start_prompt": "Premi INVIO per iniziare...",
        "ui_rest_title": "TEMPO DI RECUPERO",
        "ui_rest_subtitle": "Premi 'C' per la prossima serie",
        "ui_finish_title": "ALLENAMENTO COMPLETATO!",
        "ui_finish_subtitle": "Premi 'Q' per uscire"
    },
    
    "EN": {
        # --- GENERAL UI ---
        "ui_title": "Virtual AI Spotter",
        "ui_select_lang": "Press 'I' for Italian | Premi 'E' per Italiano",
        "ui_quit": "Press 'Q' to Quit",
        "ui_reps": "Reps",
        "ui_set": "Set",
        "ui_state": "Phase",
        "ui_fps": "FPS",
        
        # --- BICEP CURL (Feedback) ---
        "curl_name": "Bicep Curl",
        "curl_state_up": "UP (Squeeze)",
        "curl_state_down": "DOWN (Stretch)",
        
        # Corrective Feedback (Common mistakes)
        "curl_err_extension": "Full extension needed! (Angle > 160°)",
        "curl_err_flexion": "Curl higher! Squeeze the bicep.",
        "curl_err_elbow": "Elbow moving too much! Keep it tucked.",
        
        # Positive Feedback
        "curl_good_rep": "Good rep!",
        "curl_perfect_form": "Perfect form!",
        "err_body_not_visible": "Body not visible",
        "state_unknown": "UNKNOWN",
        "state_start": "READY",
        
        # --- SQUAT (Feedback) ---
        "squat_name": "Squat",
        "squat_state_up": "UP (Standing)",
        "squat_state_down": "DOWN (Squat)",
        "squat_perfect_form": "Great Squat!",
        "squat_err_depth": "Go lower! (Below 90°)",
        
        # --- NEW CLI & OVERLAY STRINGS ---
        "ui_workout_setup": "WORKOUT SETUP",
        "ui_select_ex": "Select Exercise (1-2)",
        "ui_selected": "Selected",
        "ui_side_choice": "Side (Left 'L' / Right 'R' / Both 'B') [Default R]",
        "ui_side_val": "SIDE",
        "side_left": "LEFT",
        "side_right": "RIGHT",
        "side_both": "BOTH",
        "ui_settings": "Settings",
        "ui_target_sets": "Target Sets [Default 3]",
        "ui_target_reps": "Target Reps per Set [Default 8]",
        "ui_goal": "Goal",
        "ui_start_prompt": "Press ENTER to start workout...",
        "ui_rest_title": "REST TIME",
        "ui_rest_subtitle": "Press 'C' to start next set",
        "ui_finish_title": "WORKOUT COMPLETE!",
        "ui_finish_subtitle": "Press 'Q' to exit"
    }
}

class LanguageManager:
    """
    Gestisce la lingua corrente e restituisce le stringhe tradotte.
    Implementa il pattern Singleton (di fatto) istanziando un oggetto globale.
    """
    def __init__(self):
        self.current_lang = "EN" # Default language
        
    def set_language(self, lang_code):
        """Imposta la lingua (IT o EN)."""
        if lang_code in TRANSLATIONS:
            self.current_lang = lang_code
            
    def get(self, key):
        """
        Restituisce la traduzione per la chiave richiesta.
        Se la chiave non esiste, restituisce un placeholder per debug.
        """
        lang_dict = TRANSLATIONS.get(self.current_lang, TRANSLATIONS["EN"])
        return lang_dict.get(key, f"MISSING: {key}")

# Istanza globale da importare negli altri file
i18n = LanguageManager()