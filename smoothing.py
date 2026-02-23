"""
Cursor smoothing algorithms for HandControl
One Euro Filter and EMA with optimized parameters for hand tracking
"""
import time
import math
from typing import Optional, Tuple
from abc import ABC, abstractmethod


class Smoother(ABC):
    @abstractmethod
    def filter(self, value: float, timestamp: Optional[float] = None) -> float:
        pass

    @abstractmethod
    def reset(self) -> None:
        pass


class LowPassFilter:
    def __init__(self, alpha: float = 0.1):
        self.alpha = max(0.0, min(1.0, alpha))
        self.prev_output: Optional[float] = None

    def set_alpha(self, alpha: float) -> None:
        self.alpha = max(0.0, min(1.0, alpha))

    def filter(self, value: float) -> float:
        if self.prev_output is None:
            self.prev_output = value
        else:
            self.prev_output = self.alpha * value + (1.0 - self.alpha) * self.prev_output
        return self.prev_output

    def reset(self) -> None:
        self.prev_output = None


class OneEuroFilter(Smoother):
    """
    One Euro Filter - adapts smoothing based on movement speed.
    
    Tuned for hand tracking:
    - Low mincutoff (0.3) = heavy smoothing when hand is still (kills jitter)
    - Higher beta (0.05) = fast response when hand moves quickly
    - Result: elastic feel, smooth but responsive
    """

    def __init__(self,
                 freq: float = 60.0,
                 mincutoff: float = 0.3,
                 beta: float = 0.05,
                 dcutoff: float = 1.0):
        self.freq = freq
        self.mincutoff = mincutoff
        self.beta = beta
        self.dcutoff = dcutoff
        self.x_filter = LowPassFilter()
        self.dx_filter = LowPassFilter()
        self.prev_time: Optional[float] = None
        self.prev_value: Optional[float] = None

    def _get_alpha(self, cutoff: float, dt: float) -> float:
        tau = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def filter(self, value: float, timestamp: Optional[float] = None) -> float:
        if timestamp is None:
            timestamp = time.time()

        if self.prev_time is None or self.prev_value is None:
            self.prev_time = timestamp
            self.prev_value = value
            return value

        dt = timestamp - self.prev_time
        if dt <= 0:
            dt = 1.0 / self.freq

        dx = (value - self.prev_value) / dt
        self.dx_filter.set_alpha(self._get_alpha(self.dcutoff, dt))
        dx_smooth = self.dx_filter.filter(dx)

        cutoff = self.mincutoff + self.beta * abs(dx_smooth)
        self.x_filter.set_alpha(self._get_alpha(cutoff, dt))
        result = self.x_filter.filter(value)

        self.prev_time = timestamp
        self.prev_value = result
        return result

    def reset(self) -> None:
        self.x_filter.reset()
        self.dx_filter.reset()
        self.prev_time = None
        self.prev_value = None


class EMAFilter(Smoother):
    def __init__(self, alpha: float = 0.3):
        self.alpha = max(0.0, min(1.0, alpha))
        self.prev_value: Optional[float] = None

    def filter(self, value: float, timestamp: Optional[float] = None) -> float:
        if self.prev_value is None:
            self.prev_value = value
        else:
            self.prev_value = self.alpha * value + (1.0 - self.alpha) * self.prev_value
        return self.prev_value

    def reset(self) -> None:
        self.prev_value = None


class PointSmoother:
    """2D point smoother using separate X and Y filters"""

    def __init__(self, smoother_type: str = 'one_euro', **kwargs):
        self.smoother_type = smoother_type
        if smoother_type == 'one_euro':
            self.x_smoother = OneEuroFilter(**kwargs)
            self.y_smoother = OneEuroFilter(**kwargs)
        elif smoother_type == 'ema':
            self.x_smoother = EMAFilter(**kwargs)
            self.y_smoother = EMAFilter(**kwargs)
        else:
            raise ValueError(f"Unknown smoother type: {smoother_type}")

    def filter(self, point: Tuple[float, float],
               timestamp: Optional[float] = None) -> Tuple[float, float]:
        x, y = point
        return (
            self.x_smoother.filter(x, timestamp),
            self.y_smoother.filter(y, timestamp),
        )

    def reset(self) -> None:
        self.x_smoother.reset()
        self.y_smoother.reset()
