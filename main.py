import sys
from src.core.app import SpotterApp

def main():
    """
    Entry point for Virtual AI Spotter.
    Bootstrap the Application Controller.
    """
    try:
        app = SpotterApp()
        app.setup()
        app.run()
    except KeyboardInterrupt:
        print("\nAborted by user.")
    except Exception as e:
        print(f"Critial Error: {e}")
        # Optionally log if logger isn't set up yet
        sys.exit(1)

if __name__ == "__main__":
    main()