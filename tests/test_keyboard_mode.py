"""
Tests for keyboard mode functionality
"""
import pytest
import time
import platform
from unittest.mock import patch, Mock

def test_keyboard_mode_initialization():
    """Test keyboard mode initialization"""
    from keyboard_mode import KeyboardMode
    
    feedback_events = []
    def mock_feedback(event, data):
        feedback_events.append((event, data))
    
    kb_mode = KeyboardMode(hold_time=1.0, feedback_callback=mock_feedback)
    
    assert kb_mode.hold_time == 1.0
    assert not kb_mode.is_active
    assert kb_mode.activation_start_time is None
    assert kb_mode.is_macos == (platform.system() == 'Darwin')

def test_keyboard_mode_activation_sequence():
    """Test keyboard mode activation sequence"""
    from keyboard_mode import KeyboardMode
    
    feedback_events = []
    def mock_feedback(event, data):
        feedback_events.append((event, data))
    
    kb_mode = KeyboardMode(hold_time=0.1, feedback_callback=mock_feedback)
    
    # Start activation
    result = kb_mode.update(True, {'finger_count': 5})
    assert result is None
    assert not kb_mode.is_active
    assert kb_mode.activation_start_time is not None
    assert len(feedback_events) == 1
    assert feedback_events[0][0] == "keyboard_activating"
    
    # Wait and complete activation
    time.sleep(0.11)
    result = kb_mode.update(True, {'finger_count': 5})
    assert result is None
    assert kb_mode.is_active
    assert kb_mode.activation_start_time is None

def test_keyboard_shortcut_detection():
    """Test keyboard shortcut detection from finger patterns"""
    from keyboard_mode import KeyboardMode, KeyboardShortcut
    
    kb_mode = KeyboardMode()
    
    test_cases = [
        ({'finger_count': 1, 'thumb_extended': False}, KeyboardShortcut.ESCAPE),
        ({'finger_count': 2, 'thumb_extended': False}, KeyboardShortcut.ENTER),
        ({'finger_count': 3, 'thumb_extended': False}, KeyboardShortcut.COPY),
        ({'finger_count': 4, 'thumb_extended': False}, KeyboardShortcut.PASTE),
        ({'finger_count': 0, 'thumb_extended': True}, KeyboardShortcut.APP_SWITCH),
    ]
    
    for finger_data, expected_shortcut in test_cases:
        detected = kb_mode._detect_shortcut(finger_data)
        assert detected == expected_shortcut

def test_keyboard_shortcut_execution():
    """Test keyboard shortcut execution"""
    from keyboard_mode import KeyboardMode, KeyboardShortcut
    
    with patch('pyautogui.press') as mock_press, \
         patch('pyautogui.hotkey') as mock_hotkey:
        
        kb_mode = KeyboardMode()
        
        # Test single key
        kb_mode.execute_shortcut(KeyboardShortcut.ESCAPE)
        mock_press.assert_called_with('escape')
        
        kb_mode.execute_shortcut(KeyboardShortcut.ENTER)
        mock_press.assert_called_with('enter')
        
        # Test key combinations
        kb_mode.execute_shortcut(KeyboardShortcut.COPY)
        if platform.system() == 'Darwin':
            mock_hotkey.assert_called_with('cmd', 'c')
        else:
            mock_hotkey.assert_called_with('ctrl', 'c')

def test_auto_exit_behavior():
    """Test auto-exit after shortcut execution"""
    from keyboard_mode import KeyboardMode, KeyboardShortcut
    
    kb_mode = KeyboardMode(hold_time=0.01)
    
    # Activate keyboard mode
    kb_mode.update(True, {'finger_count': 5})
    time.sleep(0.02)
    kb_mode.update(True, {'finger_count': 5})
    assert kb_mode.is_active
    
    # Execute shortcut - should auto-exit
    result = kb_mode.update(False, {'finger_count': 1, 'thumb_extended': False})
    assert result == KeyboardShortcut.ESCAPE
    assert not kb_mode.is_active

def test_force_exit():
    """Test force exit functionality"""
    from keyboard_mode import KeyboardMode
    
    kb_mode = KeyboardMode(hold_time=0.01)
    
    # Activate keyboard mode
    kb_mode.is_active = True
    
    # Force exit
    kb_mode.force_exit()
    assert not kb_mode.is_active

def test_status_reporting():
    """Test status reporting functionality"""
    from keyboard_mode import KeyboardMode
    
    kb_mode = KeyboardMode(hold_time=1.0)
    
    # Test initial status
    status = kb_mode.get_status()
    assert not status['is_active']
    assert not status['is_activating']
    assert 'platform' in status
    
    # Test activating status
    kb_mode.activation_start_time = time.time()
    status = kb_mode.get_status()
    assert status['is_activating']
    assert 'activation_progress' in status
    assert 'remaining_time' in status
    
    # Test active status
    kb_mode.is_active = True
    kb_mode.activation_start_time = None
    status = kb_mode.get_status()
    assert status['is_active']
    assert not status['is_activating']

def test_platform_detection():
    """Test platform-specific behavior"""
    from keyboard_mode import KeyboardMode
    
    kb_mode = KeyboardMode()
    
    current_platform = platform.system()
    if current_platform == 'Darwin':
        assert kb_mode.is_macos
        assert not kb_mode.is_windows
        assert not kb_mode.is_linux
    elif current_platform == 'Windows':
        assert not kb_mode.is_macos
        assert kb_mode.is_windows
        assert not kb_mode.is_linux
    elif current_platform == 'Linux':
        assert not kb_mode.is_macos
        assert not kb_mode.is_windows
        assert kb_mode.is_linux

def test_feedback_callback():
    """Test feedback callback functionality"""
    from keyboard_mode import KeyboardMode, KeyboardShortcut
    
    feedback_events = []
    def mock_feedback(event, data):
        feedback_events.append((event, data))
    
    with patch('pyautogui.press'):
        kb_mode = KeyboardMode(hold_time=0.05, feedback_callback=mock_feedback)
        
        # Test activation feedback
        kb_mode.update(True, {'finger_count': 5})
        assert len(feedback_events) >= 1
        assert feedback_events[0][0] == "keyboard_activating"
        
        # Test activation complete
        time.sleep(0.06)
        kb_mode.update(True, {'finger_count': 5})
        active_events = [e for e in feedback_events if e[0] == "keyboard_active"]
        assert len(active_events) >= 1
        
        # Test shortcut execution feedback
        feedback_events.clear()
        kb_mode.execute_shortcut(KeyboardShortcut.ESCAPE)
        assert len(feedback_events) >= 1
        assert feedback_events[0][0] == "shortcut_executed"

def test_keyboard_visualizer_initialization():
    """Test keyboard visualizer initialization"""
    from keyboard_mode import KeyboardModeVisualizer
    
    visualizer = KeyboardModeVisualizer()
    # Should not crash regardless of OpenCV availability
    assert hasattr(visualizer, 'available')

def test_keyboard_visualizer_drawing():
    """Test keyboard visualizer drawing methods"""
    from keyboard_mode import KeyboardModeVisualizer
    
    visualizer = KeyboardModeVisualizer()
    
    # Mock frame
    mock_frame = Mock()
    mock_frame.shape = [480, 640]
    
    # Test status drawing
    status = {
        'is_active': False,
        'is_activating': False,
        'platform': 'Darwin'
    }
    
    # Should not crash
    visualizer.draw_keyboard_status(mock_frame, status)
    visualizer.draw_shortcut_reference(mock_frame)

def test_keyboard_visualizer_active_status():
    """Test keyboard visualizer with active status"""
    from keyboard_mode import KeyboardModeVisualizer
    
    visualizer = KeyboardModeVisualizer()
    mock_frame = Mock()
    mock_frame.shape = [480, 640]
    
    # Test active status
    status = {
        'is_active': True,
        'is_activating': False,
        'platform': 'Darwin'
    }
    
    visualizer.draw_keyboard_status(mock_frame, status)

def test_keyboard_visualizer_activating_status():
    """Test keyboard visualizer with activating status"""
    from keyboard_mode import KeyboardModeVisualizer
    
    visualizer = KeyboardModeVisualizer()
    mock_frame = Mock()
    mock_frame.shape = [480, 640]
    
    # Test activating status with progress
    status = {
        'is_active': False,
        'is_activating': True,
        'activation_progress': 0.5,
        'remaining_time': 0.5,
        'platform': 'Darwin'
    }
    
    visualizer.draw_keyboard_status(mock_frame, status)

def test_failsafe_enforcement():
    """Test that FAILSAFE is always enabled"""
    from keyboard_mode import KeyboardMode
    
    with patch('pyautogui.FAILSAFE', False):
        kb_mode = KeyboardMode()
        
        # Should be enabled after initialization
        import pyautogui
        assert pyautogui.FAILSAFE == True

def test_invalid_finger_patterns():
    """Test handling of invalid finger patterns"""
    from keyboard_mode import KeyboardMode
    
    kb_mode = KeyboardMode()
    
    # Test patterns that don't match any shortcut
    invalid_patterns = [
        {'finger_count': 5, 'thumb_extended': False},
        {'finger_count': 0, 'thumb_extended': False},
        {'finger_count': 1, 'thumb_extended': True},
    ]
    
    for pattern in invalid_patterns:
        result = kb_mode._detect_shortcut(pattern)
        assert result is None

def test_activation_timeout():
    """Test activation timeout behavior"""
    from keyboard_mode import KeyboardMode
    
    kb_mode = KeyboardMode(hold_time=0.1)
    
    # Start activation
    kb_mode.update(True, {'finger_count': 5})
    assert kb_mode.activation_start_time is not None
    
    # Stop before timeout
    kb_mode.update(False, {})
    assert kb_mode.activation_start_time is None
    assert not kb_mode.is_active