import sys
import os
import cv2

# Add project root to system path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.infrastructure.webcam import WebcamSource

def main():
    print("Avvio test webcam...")
    try:
        # Instantiate Infrastructure class
        cam = WebcamSource(source_index=0)
        print("Webcam inizializzata con successo via Infrastructure Layer.")
        
        while True:
            ret, frame = cam.get_frame()
            if not ret:
                print("Errore lettura frame")
                break
                
            cv2.imshow('Test Infrastructure', frame)
            
            # Press 'q' to exit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        cam.release()
        cv2.destroyAllWindows()
        print("Test completato.")
        
    except Exception as e:
        print(f"ERRORE CRITICO: {e}")

if __name__ == "__main__":
    main()