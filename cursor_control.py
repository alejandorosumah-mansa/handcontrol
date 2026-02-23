"""
Cursor control with smoothing, calibration, and window management.
"""
import time
import platform
from typing import Tuple, Optional
import pyautogui

from smoothing import PointSmoother
from config import Config
from calibration import ScreenCalibrator


class CursorController:
    """Maps finger position to screen coordinates with smoothing and calibration."""

    def __init__(self, config: Config, calibrator: Optional[ScreenCalibrator] = None):
        self.config = config

        self.screen_width, self.screen_height = pyautogui.size()

        dead_zone = config.get('cursor.dead_zone', 0.08)
        self.dead_zone_x = dead_zone
        self.dead_zone_y = dead_zone

        smoothing_cfg = config.get('smoothing', {})
        stype = smoothing_cfg.get('type', 'one_euro')

        if stype == 'one_euro':
            params = {
                'freq': smoothing_cfg.get('one_euro_freq', 60),
                'mincutoff': smoothing_cfg.get('one_euro_mincutoff', 0.3),
                'beta': smoothing_cfg.get('one_euro_beta', 0.05),
                'dcutoff': smoothing_cfg.get('one_euro_dcutoff', 1.0),
            }
        else:
            params = {'alpha': smoothing_cfg.get('ema_alpha', 0.3)}

        self.smoother = PointSmoother(stype, **params)

        self.sensitivity = config.get('cursor.sensitivity', 1.0)
        self.use_acceleration = config.get('cursor.acceleration_curve', True)
        self.is_macos = platform.system() == 'Darwin'

        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0  # No pause between actions for speed

        self.last_position: Optional[Tuple[float, float]] = None
        self.is_dragging = False
        self.calibrator = calibrator

    def webcam_to_screen(self, norm_x: float, norm_y: float) -> Tuple[float, float]:
        """Convert normalized webcam coords (0-1) to screen coords."""
        # Use calibration if available
        if self.calibrator and self.calibrator.is_complete():
            mapped_x, mapped_y = self.calibrator.map_point(norm_x, norm_y)
        else:
            # Dead zone mapping
            eff_x = max(self.dead_zone_x, min(1.0 - self.dead_zone_x, norm_x))
            eff_y = max(self.dead_zone_y, min(1.0 - self.dead_zone_y, norm_y))
            mapped_x = (eff_x - self.dead_zone_x) / (1.0 - 2 * self.dead_zone_x)
            mapped_y = (eff_y - self.dead_zone_y) / (1.0 - 2 * self.dead_zone_y)

        return mapped_x * self.screen_width, mapped_y * self.screen_height

    def move_cursor(self, norm_x: float, norm_y: float) -> None:
        """Move cursor using normalized coordinates (0-1)."""
        screen_x, screen_y = self.webcam_to_screen(norm_x, norm_y)
        smooth_x, smooth_y = self.smoother.filter((screen_x, screen_y))

        # Clamp
        smooth_x = max(0, min(self.screen_width - 1, smooth_x))
        smooth_y = max(0, min(self.screen_height - 1, smooth_y))

        pyautogui.moveTo(int(smooth_x), int(smooth_y), _pause=False)
        self.last_position = (smooth_x, smooth_y)

    def left_click(self) -> None:
        pyautogui.click(button='left')

    def right_click(self) -> None:
        pyautogui.click(button='right')

    def double_click(self) -> None:
        pyautogui.doubleClick()

    def scroll(self, direction: int, amount: int = 1) -> None:
        pyautogui.scroll(amount * direction)

    def start_drag(self) -> None:
        if not self.is_dragging:
            pyautogui.mouseDown()
            self.is_dragging = True

    def stop_drag(self) -> None:
        if self.is_dragging:
            pyautogui.mouseUp()
            self.is_dragging = False

    def toggle_drag(self) -> None:
        if self.is_dragging:
            self.stop_drag()
        else:
            self.start_drag()

    def keyboard_shortcut(self, keys: list) -> None:
        platform_keys = []
        for key in keys:
            k = key.lower()
            if k in ('cmd', 'command') and not self.is_macos:
                platform_keys.append('ctrl')
            elif k == 'ctrl' and self.is_macos:
                platform_keys.append('cmd')
            else:
                platform_keys.append(key)
        pyautogui.hotkey(*platform_keys)

    def reset_smoothing(self) -> None:
        self.smoother.reset()
        self.last_position = None
