import sys
import os

# Add project root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from config.translation_strings import i18n, TRANSLATIONS

def verify_translations():
    print("Verifying Translations...")
    
    # Keys to check
    keys_to_check = [
        "ui_workout_setup", "ui_select_ex", "ui_selected", 
        "ui_side_choice", "ui_side_val", "ui_settings", 
        "ui_target_sets", "ui_target_reps", "ui_goal", 
        "ui_start_prompt", "ui_rest_title", "ui_rest_subtitle", 
        "ui_finish_title", "ui_finish_subtitle",
        # Squat
        "squat_name", "squat_state_up", "squat_state_down", "squat_perfect_form", "squat_err_depth"
    ]
    
    # Check Italian
    print("\n[IT] Checking Italian Keys...")
    i18n.set_language("IT")
    for key in keys_to_check:
        val = i18n.get(key)
        if "MISSING" in val:
            print(f"FAIL: Key '{key}' missing in IT")
            sys.exit(1)
        print(f"OK: {key} -> {val}")
        
    # Check English
    print("\n[EN] Checking English Keys...")
    i18n.set_language("EN")
    for key in keys_to_check:
        val = i18n.get(key)
        if "MISSING" in val:
            print(f"FAIL: Key '{key}' missing in EN")
            sys.exit(1)
        print(f"OK: {key} -> {val}")

    print("\nSUCCESS: All translation keys found.")

if __name__ == "__main__":
    verify_translations()
