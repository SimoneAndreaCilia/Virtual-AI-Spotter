import math
import time

class OneEuroFilter:
    def __init__(self, min_cutoff=1.0, beta=0.0, d_cutoff=1.0):
        """
        One Euro Filter implementation for smoothing noisy signals.
        
        Args:
            min_cutoff: Minimum cutoff frequency (Hz) for low speed/static.
            beta: Speed coefficient. Higher = less lag during movement.
            d_cutoff: Cutoff frequency for derivative calculation.
        """
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        
        self.x_prev = None
        self.dx_prev = None
        self.t_prev = None

    def __call__(self, x, t=None):
        if t is None:
            t = time.time()
            
        if self.x_prev is None:
            self.x_prev = x
            self.dx_prev = 0
            self.t_prev = t
            return x

        dt = t - self.t_prev
        if dt <= 0:
            return self.x_prev  # Avoid division by zero and unordered time

        # Compute the alpha for the low pass filter
        a_d = self.smoothing_factor(dt, self.d_cutoff)
        
        # Estimate the derivative (speed of change)
        dx = (x - self.x_prev) / dt
        dx_hat = self.exponential_smoothing(a_d, dx, self.dx_prev)

        # Dynamic cutoff frequency based on speed
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        a = self.smoothing_factor(dt, cutoff)
        
        # Smooth the signal
        x_hat = self.exponential_smoothing(a, x, self.x_prev)

        # Update state
        self.x_prev = x_hat
        self.dx_prev = dx_hat
        self.t_prev = t
        
        return x_hat

    def smoothing_factor(self, dt, cutoff):
        r = 2 * math.pi * cutoff * dt
        return r / (r + 1)

    def exponential_smoothing(self, a, x, x_prev):
        return a * x + (1 - a) * x_prev
    
    def reset(self):
        self.x_prev = None
        self.dx_prev = None
        self.t_prev = None

class PointSmoother:
    """Helper to smooth 2D points (x, y)."""
    def __init__(self, min_cutoff=1.0, beta=0.0, d_cutoff=1.0):
        self.filter_x = OneEuroFilter(min_cutoff, beta, d_cutoff)
        self.filter_y = OneEuroFilter(min_cutoff, beta, d_cutoff)
        
    def __call__(self, point, t=None):
        x, y = point
        sx = self.filter_x(x, t)
        sy = self.filter_y(y, t)
        return (sx, sy)
        
    def reset(self):
        self.filter_x.reset()
        self.filter_y.reset()
