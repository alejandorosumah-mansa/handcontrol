"""Tests for keyboard mode"""
import pytest
import time
import platform
from unittest.mock import patch
from keyboard_mode import KeyboardMode, KeyboardShortcut


def test_init():
    kb = KeyboardMode(hold_time=1.0)
    assert not kb.is_active
    assert kb.is_macos == (platform.system() == 'Darwin')


def test_activation_sequence():
    kb = KeyboardMode(hold_time=0.05)
    kb.update(True, {'finger_count': 5})
    assert not kb.is_active
    time.sleep(0.06)
    kb.update(True, {'finger_count': 5})
    assert kb.is_active


def test_shortcut_detection():
    kb = KeyboardMode()
    cases = [
        ({'finger_count': 1, 'thumb_extended': False}, KeyboardShortcut.ESCAPE),
        ({'finger_count': 2, 'thumb_extended': False}, KeyboardShortcut.ENTER),
        ({'finger_count': 3, 'thumb_extended': False}, KeyboardShortcut.COPY),
        ({'finger_count': 4, 'thumb_extended': False}, KeyboardShortcut.PASTE),
        ({'finger_count': 0, 'thumb_extended': True}, KeyboardShortcut.APP_SWITCH),
    ]
    for data, expected in cases:
        assert kb._detect_shortcut(data) == expected


def test_auto_exit():
    kb = KeyboardMode(hold_time=0.01)
    kb.update(True, {'finger_count': 5})
    time.sleep(0.02)
    kb.update(True, {'finger_count': 5})
    assert kb.is_active

    result = kb.update(False, {'finger_count': 1, 'thumb_extended': False})
    assert result == KeyboardShortcut.ESCAPE
    assert not kb.is_active


def test_force_exit():
    kb = KeyboardMode()
    kb.is_active = True
    kb.force_exit()
    assert not kb.is_active


def test_status():
    kb = KeyboardMode(hold_time=1.0)
    s = kb.get_status()
    assert not s['is_active']
    assert not s['is_activating']

    kb.activation_start_time = time.time()
    s = kb.get_status()
    assert s['is_activating']
    assert 'activation_progress' in s


def test_execute_shortcut():
    with patch('pyautogui.press') as mock_press, \
         patch('pyautogui.hotkey') as mock_hotkey:
        kb = KeyboardMode()
        kb.execute_shortcut(KeyboardShortcut.ESCAPE)
        mock_press.assert_called_with('escape')


def test_invalid_patterns():
    kb = KeyboardMode()
    assert kb._detect_shortcut({'finger_count': 5, 'thumb_extended': False}) is None
    assert kb._detect_shortcut({'finger_count': 0, 'thumb_extended': False}) is None


def test_feedback_callback():
    events = []
    kb = KeyboardMode(hold_time=0.01, feedback_callback=lambda e, d: events.append(e))
    kb.update(True, {'finger_count': 5})
    assert 'keyboard_activating' in events


def test_activation_reset_on_finger_drop():
    kb = KeyboardMode(hold_time=1.0)
    kb.update(True, {'finger_count': 5})
    assert kb.activation_start_time is not None
    kb.update(False, {})
    assert kb.activation_start_time is None
