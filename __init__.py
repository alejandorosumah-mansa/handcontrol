"""
Minority Report — Gesture-based cursor control
"""

__version__ = "2.0.0"
__author__ = "HandControl Team"
__description__ = "Gesture-based cursor control using computer vision — Minority Report edition"

try:
    from config import Config
    from cursor_control import CursorController
    from gesture_recognition import GestureRecognizer, GestureType
    from keyboard_mode import KeyboardMode
    from smoothing import PointSmoother, OneEuroFilter, EMAFilter
    from hand_tracker import HandTracker, HandLandmarks, HandTrackingResult
    from calibration import ScreenCalibrator
except (ImportError, NameError):
    pass

__all__ = [
    'Config', 'CursorController', 'GestureRecognizer', 'GestureType',
    'KeyboardMode', 'PointSmoother', 'OneEuroFilter', 'EMAFilter',
    'HandTracker', 'HandLandmarks', 'HandTrackingResult', 'ScreenCalibrator',
]
