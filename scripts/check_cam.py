import sys
import os
import cv2

# Add project root to system path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.infrastructure.webcam import WebcamSource

def main():
    print("Starting the webcam test...")
    try:
        # Instantiate Infrastructure class
        cam = WebcamSource(source_index=0)
        print("Webcam initialized successfully via Infrastructure Layer.")
        
        while True:
            ret, frame = cam.get_frame()
            if not ret:
                print("Error reading frame")
                break
                
            cv2.imshow('Test Infrastructure', frame)
            
            # Press 'q' to exit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        cam.release()
        cv2.destroyAllWindows()
        print("Test completed successfully.")
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    main()