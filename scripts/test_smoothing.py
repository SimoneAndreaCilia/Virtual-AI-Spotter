import sys
import os
import numpy as np
import time

# Aggiungi la root al path per importare i moduli src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.smoothing import OneEuroFilter, PointSmoother

def test_one_euro_filter():
    print("Testing OneEuroFilter...")
    
    # Configurazione filtro
    min_cutoff = 1.0
    beta = 0.0
    f = OneEuroFilter(min_cutoff=min_cutoff, beta=beta)
    
    # Generazione segnale rumoroso (onda sinusoidale + rumore)
    t = np.linspace(0, 5, 100)
    signal = np.sin(t)
    noise = np.random.normal(0, 0.1, size=len(t))
    noisy_signal = signal + noise
    
    filtered_signal = []
    start_time = time.time()
    
    for i, val in enumerate(noisy_signal):
        # Simuliamo il tempo reale
        current_time = start_time + t[i]
        filtered_val = f(val, current_time)
        filtered_signal.append(filtered_val)
        
    # Calcolo riduzione Jitter (Varianza delle differenze/derivata)
    # L'obiettivo è ridurre le fluttuazioni ad alta frequenza
    
    noisy_diff = np.diff(noisy_signal)
    filtered_diff = np.diff(filtered_signal)
    
    noisy_jitter = np.var(noisy_diff)
    filtered_jitter = np.var(filtered_diff)
    
    print(f"Original Jitter (Var of diff): {noisy_jitter:.4f}")
    print(f"Filtered Jitter (Var of diff): {filtered_jitter:.4f}")
    
    if filtered_jitter < noisy_jitter:
        print("PASS: Jitter reduced.")
    else:
        print("FAIL: Jitter not reduced.")

def test_point_smoother():
    print("\nTesting PointSmoother...")
    ps = PointSmoother(min_cutoff=1.0, beta=1.0)
    
    p1 = (100, 100)
    p2 = (105, 102) # Piccolo movimento
    p3 = (200, 200) # Grande Salto (veloce)
    
    t0 = time.time()
    s1 = ps(p1, t0)
    s2 = ps(p2, t0 + 0.1)
    s3 = ps(p3, t0 + 0.2)
    
    print(f"Input: {p1} -> Smoothed: {s1}")
    print(f"Input: {p2} -> Smoothed: {s2}")
    print(f"Input: {p3} -> Smoothed: {s3}")
    
    # Check basic logic
    assert s1 == p1, "First point should be practically identical"
    # s2 dovrebbe essere vicino a p2 ma non necessariamente identico (smoothing)
    # s3 dovrebbe inseguire velocemente p3 grazie a beta

if __name__ == "__main__":
    test_one_euro_filter()
    test_point_smoother()
