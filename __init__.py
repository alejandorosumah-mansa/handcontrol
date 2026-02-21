"""
HandControl - Gesture-based cursor control
A computer vision system for controlling the cursor using hand gestures
"""

__version__ = "1.0.0"
__author__ = "HandControl Team"
__description__ = "Gesture-based cursor control using computer vision"

# Import main components for programmatic access
try:
    from .config import Config
    from .cursor_control import CursorController
    from .gesture_recognition import GestureRecognizer, GestureType
    from .keyboard_mode import KeyboardMode
    from .smoothing import PointSmoother, OneEuroFilter, EMAFilter
except ImportError:
    # Allow imports to fail gracefully if dependencies aren't available
    pass

__all__ = [
    'Config',
    'CursorController', 
    'GestureRecognizer',
    'GestureType',
    'KeyboardMode',
    'PointSmoother',
    'OneEuroFilter',
    'EMAFilter'
]