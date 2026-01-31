import math
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
    # Estraiamo le coordinate per chiarezza e velocità (evita overhead NumPy)
    ax, ay = a[0], a[1]
    bx, by = b[0], b[1]
    cx, cy = c[0], c[1]
    
    # Calcoliamo i vettori BA e BC
    # Vettore BA = A - B
    ba_x = ax - bx
    ba_y = ay - by
    
    # Vettore BC = C - B
    bc_x = cx - bx
    bc_y = cy - by
    
    # Prodotto scalare (Dot Product)
    dot_product = (ba_x * bc_x) + (ba_y * bc_y)
    
    # Magnitudo (Lunghezza) dei vettori
    mag_ba = math.sqrt(ba_x**2 + ba_y**2)
    mag_bc = math.sqrt(bc_x**2 + bc_y**2)
    
    # Evitiamo divisione per zero
    if mag_ba * mag_bc == 0:
        return 0.0
        
    # Calcolo del coseno
    cosine_angle = dot_product / (mag_ba * mag_bc)
    
    # Gestione errori numerici (clamp tra -1.0 e 1.0)
    cosine_angle = max(-1.0, min(1.0, cosine_angle))
    
    # Calcolo angolo in radianti e conversione in gradi
    angle = math.degrees(math.acos(cosine_angle))
    
    return round(angle, 2)