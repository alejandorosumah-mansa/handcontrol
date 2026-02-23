"""Tests for cursor control"""
import pytest
import time
from unittest.mock import patch
from config import Config


def test_cursor_init(mock_pyautogui):
    from cursor_control import CursorController
    c = CursorController(Config())
    assert c.screen_width == 1920
    assert c.screen_height == 1080


def test_webcam_to_screen_center(mock_pyautogui):
    from cursor_control import CursorController
    c = CursorController(Config())
    sx, sy = c.webcam_to_screen(0.5, 0.5)
    assert abs(sx - 960) < 5
    assert abs(sy - 540) < 5


def test_move_cursor(mock_pyautogui):
    from cursor_control import CursorController
    c = CursorController(Config())
    c.move_cursor(0.5, 0.5)
    mock_pyautogui['move'].assert_called_once()


def test_click_actions(mock_pyautogui):
    from cursor_control import CursorController
    c = CursorController(Config())
    c.left_click()
    mock_pyautogui['click'].assert_called_with(button='left')
    c.right_click()
    mock_pyautogui['click'].assert_called_with(button='right')


def test_drag(mock_pyautogui):
    from cursor_control import CursorController
    c = CursorController(Config())
    assert not c.is_dragging
    c.start_drag()
    assert c.is_dragging
    c.stop_drag()
    assert not c.is_dragging


def test_toggle_drag(mock_pyautogui):
    from cursor_control import CursorController
    c = CursorController(Config())
    c.toggle_drag()
    assert c.is_dragging
    c.toggle_drag()
    assert not c.is_dragging


def test_smoothing_reset(mock_pyautogui):
    from cursor_control import CursorController
    c = CursorController(Config())
    c.move_cursor(0.5, 0.5)
    c.reset_smoothing()
    assert c.last_position is None


def test_keyboard_shortcut_platform(mock_pyautogui):
    from cursor_control import CursorController
    import platform
    c = CursorController(Config())
    c.keyboard_shortcut(['ctrl', 'c'])
    if platform.system() == 'Darwin':
        mock_pyautogui['hotkey'].assert_called_with('cmd', 'c')
    else:
        mock_pyautogui['hotkey'].assert_called_with('ctrl', 'c')
