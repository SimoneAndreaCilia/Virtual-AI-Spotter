from config.settings import SQUAT_THRESHOLDS, PUSHUP_THRESHOLDS, CURL_THRESHOLDS
from config.translation_strings import i18n
from src.core.config_types import AppConfig, ExerciseConfig

class CLI:
    @staticmethod
    def get_initial_config() -> AppConfig:
        """
        Orchestrates the initial CLI setup sequence.
        Returns a dict with all necessary config.
        """
        CLI._select_language()
        
        ex_name, ex_config, t_sets, t_reps = CLI._select_exercise_settings()
        
        return {
            'language': i18n.current_lang,
            'exercise_name': ex_name,
            'exercise_config': ex_config,
            'target_sets': t_sets,
            'target_reps': t_reps,
            'camera_id': 0 # Default, could be asked too
        }

    @staticmethod
    def _select_language():
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

    @staticmethod
    def _select_exercise_settings():
        print("\n" + "="*40)
        print(f" {i18n.get('ui_title').upper()} - {i18n.get('ui_workout_setup')}")
        print("="*40)
        
        print(" 1. Bicep Curl")
        print(" 2. Squat")
        print(" 3. Push Up")
        print(" 4. Plank")
        
        ex_choice = input(f"\n{i18n.get('ui_quit')} ({i18n.get('ui_select_ex')}): ").strip()
        
        exercise_name = "Bicep Curl"
        config = {}
        
        if ex_choice == '2':
            exercise_name = "Squat"
            config = {
                "up_angle": SQUAT_THRESHOLDS["UP_ANGLE"],
                "down_angle": SQUAT_THRESHOLDS["DOWN_ANGLE"]
            }
        elif ex_choice == '3':
            exercise_name = "PushUp"
            config = {
                "up_angle": PUSHUP_THRESHOLDS["UP_ANGLE"],
                "down_angle": PUSHUP_THRESHOLDS["DOWN_ANGLE"],
                "form_angle_min": PUSHUP_THRESHOLDS["FORM_ANGLE_MIN"]
            }
        elif ex_choice == '4':
            exercise_name = "Plank"
            config = {} # Thresholds are global constants or can be passed here
        else:
            exercise_name = "Bicep Curl"
            config = {
                "up_angle": CURL_THRESHOLDS["UP_ANGLE"],
                "down_angle": CURL_THRESHOLDS["DOWN_ANGLE"]
            }
            
        print(f" -> {i18n.get('ui_selected')}: {exercise_name}")

        # Side Selection
        side_choice = input(f" {i18n.get('ui_side_choice')}: ").strip().upper()
        if side_choice == 'L':
            config["side"] = "left"
        elif side_choice == 'B':
            config["side"] = "both"
        else:
            config["side"] = "right"
            
        side_key = f"side_{config['side']}"
        print(f" -> {i18n.get('ui_side_val')}: {i18n.get(side_key)}")

        # Sets & Reps
        print(f"\n [{i18n.get('ui_settings')}]")
        try:
            sets_input = input(f" {i18n.get('ui_target_sets')}: ").strip()
            target_sets = int(sets_input) if sets_input else 3
            
            if exercise_name == "Plank":
                 target_reps = 0 # Ignored for time-based usually, or means "Max Time"
                 print(f" {i18n.get('ui_target_reps')} skipped for Plank.")
            else:
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
