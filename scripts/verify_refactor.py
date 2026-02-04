
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    print("1. Testing Imports...")
    from src.core.app import SpotterApp
    from src.core.session_manager import SessionManager
    from src.infrastructure.ai_inference import PoseEstimator
    from src.ui.cli import CLI
    print("   Imports Successful.")

    print("2. Testing Class Instantiation (Mocking)...")
    # We won't instantiate SpotterApp fully because it acts on __init__ for some simple vars but setup() does the heavy lifting.
    app = SpotterApp()
    print(f"   SpotterApp instance: {app}")

    print("3. Testing Factory...")
    from src.core.factory import ExerciseFactory
    # Just check if class exists
    print(f"   Factory: {ExerciseFactory}")

    print("4. Testing Visualizer...")
    from src.ui.visualizer import Visualizer
    vis = Visualizer()
    if hasattr(vis, 'draw_dashboard_from_state'):
        print("   Visualizer has new method 'draw_dashboard_from_state'")
    else:
        raise AttributeError("Visualizer missing 'draw_dashboard_from_state'")

    print("\nSUCCESS: All static checks passed.")

except Exception as e:
    print(f"\nFAILURE: {e}")
    sys.exit(1)
