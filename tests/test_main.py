"""Tests for main application integration"""
import pytest
from unittest.mock import patch, Mock, MagicMock
from gesture_recognition import GestureType


def test_version():
    # Import without triggering cv2 recursion
    import importlib.util
    spec = importlib.util.spec_from_file_location("__init__", "__init__.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.__version__ == "2.0.0"


def test_app_init(mock_pyautogui):
    with patch('main.Camera') as mc, \
         patch('main.HandTracker') as mt:
        cam = Mock()
        cam.open.return_value = True
        mc.return_value = cam
        mt.return_value = Mock()

        from main import HandControlApp
        app = HandControlApp(preview=False)
        assert hasattr(app, 'camera')
        assert hasattr(app, 'tracker')
        assert hasattr(app, 'gesture_recognizer')
        assert hasattr(app, 'cursor_controller')
        assert hasattr(app, 'keyboard_mode')
        app.cleanup()


def test_keyboard_feedback(mock_pyautogui):
    with patch('main.Camera') as mc, \
         patch('main.HandTracker') as mt:
        cam = Mock()
        cam.open.return_value = True
        mc.return_value = cam
        mt.return_value = Mock()

        from main import HandControlApp
        app = HandControlApp(preview=False)

        app._keyboard_feedback("keyboard_activating", {"remaining": 1.5})
        assert "1.5" in app.keyboard_feedback_message

        app._keyboard_feedback("keyboard_active", {})
        assert app.keyboard_feedback_message == "KEYBOARD MODE"

        app._keyboard_feedback("keyboard_inactive", {})
        assert app.keyboard_feedback_message == ""
        app.cleanup()


def test_can_click(mock_pyautogui):
    with patch('main.Camera') as mc, \
         patch('main.HandTracker') as mt:
        cam = Mock()
        cam.open.return_value = True
        mc.return_value = cam
        mt.return_value = Mock()

        from main import HandControlApp
        import time
        app = HandControlApp(preview=False)
        assert app._can_click()
        app.last_click_time = time.time()
        assert not app._can_click()
        app.cleanup()
