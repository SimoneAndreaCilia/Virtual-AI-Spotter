import math
from typing import Tuple

def calculate_angle(a: Tuple[float, float], 
                    b: Tuple[float, float], 
                    c: Tuple[float, float]) -> float:
    """
    Calculate the angle in degrees between three points (a, b, c).
    b is the vertex of the angle.
    
    Args:
        a: Coordinates (x, y) of the first point (e.g. Shoulder)
        b: Coordinates (x, y) of the vertex (e.g. Elbow)
        c: Coordinate (x, y) of the third point (e.g. Wrist)
        
    Returns:
        float: Angle in degrees (0-180)
    """
    # Extract coordinates for clarity and speed (avoids NumPy overhead)
    ax, ay = a[0], a[1]
    bx, by = b[0], b[1]
    cx, cy = c[0], c[1]
    
    # Calculate vectors BA and BC
    # Vector BA = A - B
    ba_x = ax - bx
    ba_y = ay - by
    
    # Vector BC = C - B
    bc_x = cx - bx
    bc_y = cy - by
    
    # Dot Product
    dot_product = (ba_x * bc_x) + (ba_y * bc_y)
    
    # Magnitude of vectors
    mag_ba = math.sqrt(ba_x**2 + ba_y**2)
    mag_bc = math.sqrt(bc_x**2 + bc_y**2)
    
    # Avoid division by zero
    if mag_ba * mag_bc == 0:
        return 0.0
        
    # Calculate cosine
    cosine_angle = dot_product / (mag_ba * mag_bc)
    
    # Handle numeric errors (clamp between -1.0 and 1.0)
    cosine_angle = max(-1.0, min(1.0, cosine_angle))
    
    # Calculate angle in radians and convert to degrees
    angle = math.degrees(math.acos(cosine_angle))
    
    return round(angle, 2)