"""
Tests for main application integration
"""
import pytest
from unittest.mock import patch, Mock, MagicMock

def test_main_app_initialization(mock_pyautogui, sample_config):
    """Test main application initialization"""
    with patch('main.Camera') as mock_camera_class, \
         patch('main.HandTracker') as mock_tracker_class:
        
        # Configure mocks
        mock_camera = Mock()
        mock_camera.open.return_value = True
        mock_camera_class.return_value = mock_camera
        
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        
        from main import HandControlApp
        
        app = HandControlApp(preview=False)
        
        # Verify components are initialized
        assert hasattr(app, 'camera')
        assert hasattr(app, 'tracker')
        assert hasattr(app, 'gesture_recognizer')
        assert hasattr(app, 'cursor_controller')
        assert hasattr(app, 'keyboard_mode')
        assert hasattr(app, 'keyboard_visualizer')

def test_main_app_with_config(mock_pyautogui, temp_dir, sample_config):
    """Test main application with custom config"""
    import yaml
    import os
    from config import Config
    
    # Create custom config file
    config_path = os.path.join(temp_dir, 'custom_config.yaml')
    with open(config_path, 'w') as f:
        yaml.dump(sample_config, f)
    
    with patch('main.Camera') as mock_camera_class, \
         patch('main.HandTracker') as mock_tracker_class:
        
        mock_camera = Mock()
        mock_camera.open.return_value = True
        mock_camera_class.return_value = mock_camera
        
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        
        from main import HandControlApp
        
        app = HandControlApp(config_path=config_path, preview=False)
        
        # Verify config was loaded
        assert app.config.get('camera.width') == 640
        assert app.config.get('smoothing.type') == 'one_euro'

def test_main_app_gesture_handling(mock_pyautogui, mock_hand_landmarks):
    """Test gesture handling in main application"""
    with patch('main.Camera') as mock_camera_class, \
         patch('main.HandTracker') as mock_tracker_class:
        
        mock_camera = Mock()
        mock_camera.open.return_value = True
        mock_camera.read.return_value = (True, Mock())
        mock_camera_class.return_value = mock_camera
        
        mock_tracker = Mock()
        mock_tracker.track.return_value = mock_hand_landmarks
        mock_tracker_class.return_value = mock_tracker
        
        from main import HandControlApp
        from gesture_recognition import GestureType
        
        app = HandControlApp(preview=False)
        
        # Mock gesture data
        gesture_data = {
            'finger_count': 1,
            'thumb_extended': False
        }
        
        # Test MOVE gesture
        app._handle_gesture(GestureType.MOVE, {}, mock_hand_landmarks)
        
        # Test LEFT_CLICK gesture
        app.last_click_time = 0  # Reset cooldown
        app._handle_gesture(GestureType.LEFT_CLICK, {}, None)

def test_main_app_pause_resume(mock_pyautogui):
    """Test pause/resume functionality"""
    with patch('main.Camera') as mock_camera_class, \
         patch('main.HandTracker') as mock_tracker_class:
        
        mock_camera = Mock()
        mock_camera.open.return_value = True
        mock_camera_class.return_value = mock_camera
        
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        
        from main import HandControlApp
        
        app = HandControlApp(preview=False)
        
        # Test initial state
        assert not app.is_paused
        
        # Test pause
        app.is_paused = True
        assert app.is_paused

def test_main_app_cooldowns(mock_pyautogui):
    """Test cooldown functionality"""
    import time
    
    with patch('main.Camera') as mock_camera_class, \
         patch('main.HandTracker') as mock_tracker_class:
        
        mock_camera = Mock()
        mock_camera.open.return_value = True
        mock_camera_class.return_value = mock_camera
        
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        
        from main import HandControlApp
        
        app = HandControlApp(preview=False)
        app.click_cooldown = 0.1  # Short cooldown for testing
        
        # Test initial state
        assert app._can_click()
        
        # Test cooldown
        app.last_click_time = time.time()
        assert not app._can_click()
        
        # Test cooldown expiration
        time.sleep(0.11)
        assert app._can_click()

def test_main_app_keyboard_feedback(mock_pyautogui):
    """Test keyboard mode feedback"""
    with patch('main.Camera') as mock_camera_class, \
         patch('main.HandTracker') as mock_tracker_class:
        
        mock_camera = Mock()
        mock_camera.open.return_value = True
        mock_camera_class.return_value = mock_camera
        
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        
        from main import HandControlApp
        
        app = HandControlApp(preview=False)
        
        # Test feedback callback
        app._keyboard_feedback("keyboard_activating", {"remaining": 1.5})
        assert "KEYBOARD 1.5s" in app.keyboard_feedback_message
        
        app._keyboard_feedback("keyboard_active", {})
        assert app.keyboard_feedback_message == "KEYBOARD MODE"
        
        app._keyboard_feedback("keyboard_inactive", {})
        assert app.keyboard_feedback_message == ""

def test_main_app_cleanup(mock_pyautogui):
    """Test application cleanup"""
    with patch('main.Camera') as mock_camera_class, \
         patch('main.HandTracker') as mock_tracker_class:
        
        mock_camera = Mock()
        mock_camera.open.return_value = True
        mock_camera.close = Mock()
        mock_camera_class.return_value = mock_camera
        
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        
        from main import HandControlApp
        
        app = HandControlApp(preview=False)
        
        # Test cleanup
        app.cleanup()
        
        # Verify camera was closed
        mock_camera.close.assert_called_once()

def test_main_app_status_drawing(mock_pyautogui):
    """Test status drawing functionality"""
    with patch('main.Camera') as mock_camera_class, \
         patch('main.HandTracker') as mock_tracker_class, \
         patch('main.CV2_AVAILABLE', True), \
         patch('main.cv2') as mock_cv2:
        
        mock_camera = Mock()
        mock_camera.open.return_value = True
        mock_camera_class.return_value = mock_camera
        
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        
        from main import HandControlApp
        from gesture_recognition import GestureType
        
        app = HandControlApp(preview=False)
        
        # Mock frame
        mock_frame = Mock()
        mock_frame.shape = [480, 640]
        
        # Test status drawing
        app._draw_status(mock_frame, GestureType.MOVE)
        
        # Should have called cv2 drawing functions
        assert mock_cv2.getTextSize.called
        assert mock_cv2.rectangle.called
        assert mock_cv2.putText.called

def test_cli_entry_point():
    """Test CLI entry point functionality"""
    with patch('__main__.HandControlApp') as mock_app_class, \
         patch('__main__.run_calibration_tool') as mock_calibration:
        
        mock_app = Mock()
        mock_app_class.return_value = mock_app
        
        from __main__ import main
        
        # Test normal run mode
        with patch('sys.argv', ['handcontrol']):
            with patch('argparse.ArgumentParser.parse_args') as mock_parse:
                args = Mock()
                args.calibrate = False
                args.create_config = False
                args.no_preview = False
                args.config = None
                mock_parse.return_value = args
                
                result = main()
                
                # Should have created and run app
                mock_app_class.assert_called_once()
                mock_app.run.assert_called_once()

def test_cli_calibration_mode():
    """Test CLI calibration mode"""
    with patch('__main__.run_calibration_tool') as mock_calibration:
        
        mock_calibration.return_value = True
        
        from __main__ import main
        
        # Test calibration mode
        with patch('sys.argv', ['handcontrol', '--calibrate']):
            with patch('argparse.ArgumentParser.parse_args') as mock_parse:
                args = Mock()
                args.calibrate = True
                args.create_config = False
                args.camera = 0
                mock_parse.return_value = args
                
                result = main()
                
                # Should have called calibration tool
                mock_calibration.assert_called_once_with(camera_index=0)
                assert result == 0

def test_cli_create_config():
    """Test CLI create config mode"""
    with patch('__main__.create_default_config') as mock_create:
        
        mock_create.return_value = 'config.yaml'
        
        from __main__ import main
        
        # Test create config mode
        with patch('sys.argv', ['handcontrol', '--create-config']):
            with patch('argparse.ArgumentParser.parse_args') as mock_parse:
                args = Mock()
                args.calibrate = False
                args.create_config = True
                mock_parse.return_value = args
                
                result = main()
                
                # Should have called create config
                mock_create.assert_called_once()
                assert result == 0

def test_cli_error_handling():
    """Test CLI error handling"""
    from __main__ import main
    
    # Test import error handling
    with patch('__main__.HandControlApp', side_effect=ImportError("Missing dependency")):
        with patch('sys.argv', ['handcontrol']):
            with patch('argparse.ArgumentParser.parse_args') as mock_parse:
                args = Mock()
                args.calibrate = False
                args.create_config = False
                mock_parse.return_value = args
                
                result = main()
                assert result == 1

def test_failsafe_always_enabled(mock_pyautogui):
    """Test that FAILSAFE is always enabled in main app"""
    with patch('main.Camera') as mock_camera_class, \
         patch('main.HandTracker') as mock_tracker_class:
        
        mock_camera = Mock()
        mock_camera.open.return_value = True
        mock_camera_class.return_value = mock_camera
        
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        
        # Set FAILSAFE to False initially
        with patch('pyautogui.FAILSAFE', False):
            from main import HandControlApp
            
            app = HandControlApp(preview=False)
            
            # Should be enabled after initialization
            import pyautogui
            assert pyautogui.FAILSAFE == True

def test_main_app_version_info():
    """Test version information availability"""
    from __init__ import __version__, __author__, __description__
    
    assert __version__ == "1.0.0"
    assert isinstance(__author__, str)
    assert isinstance(__description__, str)
    assert len(__description__) > 0