"""
Keyboard Shortcut Mode for HandControl
"""
import time
import platform
from typing import Dict, Any, Optional, Callable
from enum import Enum
import pyautogui


class KeyboardShortcut(Enum):
    ESCAPE = "escape"
    ENTER = "enter"
    COPY = "copy"
    PASTE = "paste"
    APP_SWITCH = "app_switch"


class KeyboardMode:
    def __init__(self, hold_time: float = 1.0, feedback_callback: Optional[Callable] = None):
        self.hold_time = hold_time
        self.feedback_callback = feedback_callback
        self.is_active = False
        self.activation_start_time: Optional[float] = None
        self.is_macos = platform.system() == 'Darwin'
        self.is_windows = platform.system() == 'Windows'
        self.is_linux = platform.system() == 'Linux'
        pyautogui.FAILSAFE = True

    def update(self, all_fingers_extended: bool, finger_data: Dict[str, Any]) -> Optional[KeyboardShortcut]:
        current_time = time.time()

        if all_fingers_extended:
            if not self.is_active and self.activation_start_time is None:
                self.activation_start_time = current_time
                if self.feedback_callback:
                    self.feedback_callback("keyboard_activating", {"remaining": self.hold_time})
            elif self.activation_start_time and not self.is_active:
                held = current_time - self.activation_start_time
                remaining = max(0, self.hold_time - held)
                if self.feedback_callback:
                    self.feedback_callback("keyboard_activating", {"remaining": remaining})
                if held >= self.hold_time:
                    self.is_active = True
                    self.activation_start_time = None
                    if self.feedback_callback:
                        self.feedback_callback("keyboard_active", {})
        else:
            if self.is_active:
                shortcut = self._detect_shortcut(finger_data)
                if shortcut:
                    self._exit()
                    return shortcut
            else:
                self.activation_start_time = None
                if self.feedback_callback:
                    self.feedback_callback("keyboard_inactive", {})
        return None

    def _detect_shortcut(self, finger_data: Dict[str, Any]) -> Optional[KeyboardShortcut]:
        count = finger_data.get('finger_count', 0)
        thumb = finger_data.get('thumb_extended', False)

        if count == 1:
            return KeyboardShortcut.ESCAPE
        elif count == 2:
            return KeyboardShortcut.ENTER
        elif count == 3:
            return KeyboardShortcut.COPY
        elif count == 4:
            return KeyboardShortcut.PASTE
        elif count == 0 and thumb:
            return KeyboardShortcut.APP_SWITCH
        return None

    def execute_shortcut(self, shortcut: KeyboardShortcut) -> None:
        if shortcut == KeyboardShortcut.ESCAPE:
            pyautogui.press('escape')
        elif shortcut == KeyboardShortcut.ENTER:
            pyautogui.press('enter')
        elif shortcut == KeyboardShortcut.COPY:
            pyautogui.hotkey('cmd' if self.is_macos else 'ctrl', 'c')
        elif shortcut == KeyboardShortcut.PASTE:
            pyautogui.hotkey('cmd' if self.is_macos else 'ctrl', 'v')
        elif shortcut == KeyboardShortcut.APP_SWITCH:
            if self.is_macos:
                pyautogui.hotkey('cmd', 'tab')
            else:
                pyautogui.hotkey('alt', 'tab')

        if self.feedback_callback:
            self.feedback_callback("shortcut_executed", {"shortcut": shortcut.value})

    def _exit(self) -> None:
        self.is_active = False
        self.activation_start_time = None
        if self.feedback_callback:
            self.feedback_callback("keyboard_inactive", {})

    def force_exit(self) -> None:
        self._exit()

    def get_status(self) -> Dict[str, Any]:
        status = {
            'is_active': self.is_active,
            'is_activating': self.activation_start_time is not None,
            'platform': platform.system(),
            'hold_time': self.hold_time,
        }
        if self.activation_start_time:
            elapsed = time.time() - self.activation_start_time
            status['activation_progress'] = min(1.0, elapsed / self.hold_time)
            status['remaining_time'] = max(0, self.hold_time - elapsed)
        return status


class KeyboardModeVisualizer:
    def __init__(self):
        try:
            import cv2
            self.cv2 = cv2
            self.available = True
        except ImportError:
            self.available = False

    def draw_keyboard_status(self, frame, status: Dict[str, Any]) -> None:
        if not self.available:
            return
        h, w = frame.shape[:2]

        if status['is_active']:
            text = "KEYBOARD MODE"
            color = (0, 255, 0)
            ts = self.cv2.getTextSize(text, self.cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            cx = w // 2 - ts[0] // 2
            self.cv2.rectangle(frame, (cx - 10, 50), (cx + ts[0] + 10, 85), (0, 0, 0), -1)
            self.cv2.putText(frame, text, (cx, 78), self.cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        elif status.get('is_activating'):
            progress = status.get('activation_progress', 0)
            remaining = status.get('remaining_time', 0)
            text = f"KEYBOARD {remaining:.1f}s"
            color = (0, 255, 255)
            bar_w = 200
            cx = w // 2 - bar_w // 2
            self.cv2.rectangle(frame, (cx, 50), (cx + bar_w, 75), (60, 60, 60), -1)
            self.cv2.rectangle(frame, (cx, 50), (cx + int(bar_w * progress), 75), color, -1)
            self.cv2.putText(frame, text, (cx, 95), self.cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    def draw_shortcut_reference(self, frame) -> None:
        if not self.available:
            return
        h, w = frame.shape[:2]
        shortcuts = [
            "1 finger → Esc", "2 → Enter", "3 → Copy",
            "4 → Paste", "Thumb → App Switch",
        ]
        y0 = h - len(shortcuts) * 22 - 10
        self.cv2.rectangle(frame, (8, y0 - 5), (220, h - 5), (0, 0, 0), -1)
        for i, s in enumerate(shortcuts):
            self.cv2.putText(frame, s, (12, y0 + i * 22 + 15),
                             self.cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
