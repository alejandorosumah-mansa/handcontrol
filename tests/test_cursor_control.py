"""
Tests for cursor control system
"""
import pytest
import platform
from unittest.mock import patch, Mock

def test_cursor_controller_initialization(mock_pyautogui, sample_config):
    """Test cursor controller initialization"""
    from cursor_control import CursorController
    from config import Config
    
    config = Config()
    config.config = sample_config
    
    controller = CursorController(config)
    
    assert controller.screen_width == 1920
    assert controller.screen_height == 1080
    assert controller.dead_zone_x == 0.1
    assert controller.is_macos == (platform.system() == 'Darwin')

def test_webcam_to_screen_mapping(mock_pyautogui, sample_config):
    """Test webcam coordinate to screen coordinate mapping"""
    from cursor_control import CursorController
    from config import Config
    
    config = Config()
    config.config = sample_config
    controller = CursorController(config)
    
    # Test center mapping
    screen_x, screen_y = controller.webcam_to_screen(320, 240, 640, 480)
    assert abs(screen_x - 960) < 1  # Should map to screen center
    assert abs(screen_y - 540) < 1
    
    # Test corner mappings (after dead zone)
    screen_x, screen_y = controller.webcam_to_screen(64, 48, 640, 480)  # 10% in
    assert screen_x == 0  # Should map to screen edge
    assert screen_y == 0

def test_dead_zone_behavior(mock_pyautogui, sample_config):
    """Test dead zone filtering"""
    from cursor_control import CursorController
    from config import Config
    
    config = Config()
    config.config = sample_config
    controller = CursorController(config)
    
    # Test points in dead zone boundaries
    test_cases = [
        (32, 24, 640, 480),   # 5% in (should be clamped to dead zone)
        (576, 432, 640, 480), # 90% in (should be clamped)
        (320, 240, 640, 480), # Center (should map to center)
    ]
    
    for webcam_x, webcam_y, w, h in test_cases:
        screen_x, screen_y = controller.webcam_to_screen(webcam_x, webcam_y, w, h)
        # All results should be valid screen coordinates
        assert 0 <= screen_x <= 1920
        assert 0 <= screen_y <= 1080

def test_cursor_movement(mock_pyautogui, sample_config):
    """Test cursor movement with smoothing"""
    from cursor_control import CursorController
    from config import Config
    
    config = Config()
    config.config = sample_config
    controller = CursorController(config)
    
    # Test cursor movement
    controller.move_cursor(320, 240, 640, 480)
    
    # Should have called pyautogui.moveTo
    mock_pyautogui['move'].assert_called_once()

def test_mouse_actions(mock_pyautogui, sample_config):
    """Test mouse click and scroll actions"""
    from cursor_control import CursorController
    from config import Config
    
    config = Config()
    config.config = sample_config
    controller = CursorController(config)
    
    # Test left click
    controller.left_click()
    mock_pyautogui['click'].assert_called_with(button='left')
    
    # Test right click
    controller.right_click()
    mock_pyautogui['click'].assert_called_with(button='right')
    
    # Test double click (reset mock first)
    mock_pyautogui['click'].reset_mock()
    controller.double_click()
    # Note: pyautogui.doubleClick() is separate from click()
    
    # Test scroll
    with patch('pyautogui.scroll') as mock_scroll:
        controller.scroll(1)  # Scroll up
        mock_scroll.assert_called_with(1)
        
        controller.scroll(-1, 3)  # Scroll down 3 units
        mock_scroll.assert_called_with(-3)

def test_drag_functionality(mock_pyautogui, sample_config):
    """Test drag start/stop/toggle functionality"""
    from cursor_control import CursorController
    from config import Config
    
    config = Config()
    config.config = sample_config
    controller = CursorController(config)
    
    with patch('pyautogui.mouseDown') as mock_down, \
         patch('pyautogui.mouseUp') as mock_up:
        
        # Test start drag
        assert not controller.is_dragging
        controller.start_drag()
        assert controller.is_dragging
        mock_down.assert_called_once()
        
        # Test stop drag
        controller.stop_drag()
        assert not controller.is_dragging
        mock_up.assert_called_once()
        
        # Test toggle drag
        mock_down.reset_mock()
        controller.toggle_drag()
        assert controller.is_dragging
        mock_down.assert_called_once()
        
        mock_up.reset_mock()
        controller.toggle_drag()
        assert not controller.is_dragging
        mock_up.assert_called_once()

def test_keyboard_shortcuts(mock_pyautogui, sample_config):
    """Test keyboard shortcut functionality"""
    from cursor_control import CursorController
    from config import Config
    
    config = Config()
    config.config = sample_config
    controller = CursorController(config)
    
    # Test simple key
    controller.keyboard_shortcut(['escape'])
    mock_pyautogui['hotkey'].assert_called_with('escape')
    
    # Test key combination
    controller.keyboard_shortcut(['ctrl', 'c'])
    mock_pyautogui['hotkey'].assert_called_with('ctrl', 'c')

def test_platform_specific_shortcuts(mock_pyautogui, sample_config):
    """Test platform-specific keyboard shortcuts"""
    from cursor_control import CursorController
    from config import Config
    
    config = Config()
    config.config = sample_config
    controller = CursorController(config)
    
    # Test command key conversion
    if platform.system() == 'Darwin':
        # On macOS, ctrl should become cmd
        controller.keyboard_shortcut(['ctrl', 'c'])
        mock_pyautogui['hotkey'].assert_called_with('cmd', 'c')
    else:
        # On other platforms, cmd should become ctrl
        controller.keyboard_shortcut(['cmd', 'c'])
        mock_pyautogui['hotkey'].assert_called_with('ctrl', 'c')

def test_smoothing_reset(mock_pyautogui, sample_config):
    """Test smoothing reset functionality"""
    from cursor_control import CursorController
    from config import Config
    
    config = Config()
    config.config = sample_config
    controller = CursorController(config)
    
    # Move cursor to establish history
    controller.move_cursor(100, 100, 640, 480)
    
    # Reset smoothing
    controller.reset_smoothing()
    
    # Should reset internal state
    assert controller.last_position is None

def test_sensitivity_and_acceleration(mock_pyautogui, sample_config):
    """Test cursor sensitivity and acceleration"""
    from cursor_control import CursorController
    from config import Config
    
    # Test with different sensitivity
    config = Config()
    config.config = sample_config.copy()
    config.config['cursor']['sensitivity'] = 2.0
    config.config['cursor']['acceleration_curve'] = True
    
    controller = CursorController(config)
    
    # Move cursor multiple times to test acceleration
    controller.move_cursor(320, 240, 640, 480)  # Center
    controller.move_cursor(420, 240, 640, 480)  # Move right
    
    # Should have made multiple moveTo calls
    assert mock_pyautogui['move'].call_count >= 2

def test_coordinate_bounds_checking(mock_pyautogui, sample_config):
    """Test that coordinates are bounded to screen"""
    from cursor_control import CursorController
    from config import Config
    
    config = Config()
    config.config = sample_config
    controller = CursorController(config)
    
    # Test extreme coordinates
    controller.move_cursor(0, 0, 640, 480)      # Top-left
    controller.move_cursor(640, 480, 640, 480)  # Bottom-right
    
    # Should not crash and should call moveTo
    assert mock_pyautogui['move'].call_count >= 2
    
    # Check that coordinates passed to moveTo are within screen bounds
    for call in mock_pyautogui['move'].call_args_list:
        x, y = call[0]
        assert 0 <= x < 1920
        assert 0 <= y < 1080

def test_failsafe_enabled(mock_pyautogui, sample_config):
    """Test that FAILSAFE is always enabled"""
    from cursor_control import CursorController
    from config import Config
    
    config = Config()
    config.config = sample_config
    
    # Set FAILSAFE to False before creating controller
    with patch('pyautogui.FAILSAFE', False):
        controller = CursorController(config)
        
        # Should be set to True by constructor
        import pyautogui
        assert pyautogui.FAILSAFE == True

def test_smoothing_types(mock_pyautogui, sample_config):
    """Test different smoothing filter types"""
    from cursor_control import CursorController
    from config import Config
    
    # Test One Euro Filter
    config = Config()
    config.config = sample_config.copy()
    config.config['smoothing']['type'] = 'one_euro'
    
    controller = CursorController(config)
    assert controller.smoother.smoother_type == 'one_euro'
    
    # Test EMA Filter
    config.config['smoothing']['type'] = 'ema'
    controller = CursorController(config)
    assert controller.smoother.smoother_type == 'ema'