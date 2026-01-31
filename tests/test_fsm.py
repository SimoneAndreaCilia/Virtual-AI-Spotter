import unittest
import sys
import os

# Add project root to path to allow importing src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.fsm import RepetitionCounter
from config.settings import HYSTERESIS_TOLERANCE

class TestRepetitionCounter(unittest.TestCase):
    def setUp(self):
        # Configurazione standard (es. Squat/PushUp)
        # Down: < 90, Up: > 160
        self.fsm = RepetitionCounter(up_threshold=160, down_threshold=90, start_stage="up")
        
        # Configurazione invertita (es. Curl)
        # Up (Flexion): < 30, Down (Extension): > 160
        self.fsm_curl = RepetitionCounter(up_threshold=30, down_threshold=160, start_stage="down", inverted=True)

    def test_standard_rep_counting(self):
        """Testa il conteggio standard: Start -> Down -> Up (Count)"""
        # 1. Start UP (Angle 170)
        reps, state = self.fsm.process(170)
        self.assertEqual(state, "up")
        self.assertEqual(reps, 0)
        
        # 2. Go Down (Angle 80) < 90 (Down Thresh) + 5 (Hyst) = 95
        # Feed multiple frames for debouncing
        self.fsm.process(80) 
        reps, state = self.fsm.process(80) 
        self.assertEqual(state, "down")
        
        # 3. Go Up (Angle 170) > 160 (Up Thresh) - 5 (Hyst) = 155
        self.fsm.process(170)
        reps, state = self.fsm.process(170)
        self.assertEqual(state, "up")
        self.assertEqual(reps, 1) # Should count here

    def test_standard_hysteresis(self):
        """Testa che piccole variazioni intorno alla soglia non cambino stato subito"""
        # Start Up
        self.fsm.process(170)
        self.fsm.process(170)
        
        # Go near Down threshold (90) but not quite (96 > 90+5)
        # Hysteresis is added to threshold: 90 + 5 = 95. So 96 is > 95. No switch.
        reps, state = self.fsm.process(96)
        self.assertEqual(state, "up")
        
        # Go exactly 94 (< 95). Should switch if stable.
        self.fsm.process(94)
        reps, state = self.fsm.process(94)
        self.assertEqual(state, "down")

    def test_inverted_rep_counting(self):
        """Testa logica invertita (Curl): Start Down -> Up (Flexion) -> Rep Count?"""
        # Curl Start Down (Extension > 160)
        self.fsm_curl.process(170)
        reps, state = self.fsm_curl.process(170)
        self.assertEqual(state, "down")
        self.assertEqual(reps, 0)
        
        # Go Up/Flexion (< 30). Threshold 30.
        # Logic: < 30 + 5 (Hyst) = 35. 
        # So 20 is < 35. Should switch to UP.
        self.fsm_curl.process(20)
        reps, state = self.fsm_curl.process(20)
        self.assertEqual(state, "up")
        self.assertEqual(reps, 1) # Counts on entering Up phase (Peak contraction)
        
        # Go Down/Extension (> 160). Threshold 160.
        # Logic: > 160 - 5 = 155.
        # So 170 > 155. Should switch to DOWN.
        self.fsm_curl.process(170)
        reps, state = self.fsm_curl.process(170)
        self.assertEqual(state, "down") 
        self.assertEqual(reps, 1) # Count stays same

    def test_debouncing_noise(self):
        """Testa che frame spuri non triggerino il cambio stato"""
        # Start Up
        self.fsm.process(170)
        self.fsm.process(170)
        
        # Singolo frame di rumore (0 gradi - glitch)
        reps, state = self.fsm.process(0)
        self.assertEqual(state, "up") # Non deve cambiare
        
        # Ritorno a valore normale
        reps, state = self.fsm.process(170) 
        self.assertEqual(state, "up")

if __name__ == '__main__':
    unittest.main()
