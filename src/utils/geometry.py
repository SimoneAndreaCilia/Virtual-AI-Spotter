import numpy as np
from typing import Tuple

def calculate_angle(a: Tuple[float, float], 
                    b: Tuple[float, float], 
                    c: Tuple[float, float]) -> float:
    """
    Calcola l'angolo in gradi tra tre punti (a, b, c).
    b è il vertice dell'angolo.
    
    Args:
        a: Coordinate (x, y) del primo punto (es. Spalla)
        b: Coordinate (x, y) del vertice (es. Gomito)
        c: Coordinate (x, y) del terzo punto (es. Polso)
        
    Returns:
        float: Angolo in gradi (0-180)
    """
    # Convertiamo in array numpy per efficienza vettoriale
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    # Calcoliamo i vettori BA e BC
    # Esempio: vettore BA = A - B
    ba = a - b
    bc = c - b
    
    # Calcoliamo il coseno dell'angolo usando il prodotto scalare (dot product)
    # Formula: cos(theta) = (u . v) / (|u| * |v|)
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    
    # Gestione errori numerici: clippiamo il valore tra -1.0 e 1.0
    cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
    
    # Convertiamo da radianti a gradi
    angle = np.degrees(np.arccos(cosine_angle))
    
    return round(angle, 2)