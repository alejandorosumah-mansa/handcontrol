"""
Test Phase 5: Main Loop + Actions
Tests gesture handling and action dispatching without camera
"""
import time
import platform
from unittest.mock import Mock, patch
from typing import Dict, Any

# Import HandControl modules
from gesture_recognition import GestureType
from config import Config

class MockLandmarks:
    """Mock hand landmarks for testing"""
    
    def __init__(self, landmarks_dict: Dict[int, tuple]):
        """
        Initialize mock landmarks
        
        Args:
            landmarks_dict: Dict mapping landmark IDs to (x, y) coordinates
        """
        self.landmarks = landmarks_dict
    
    def get_landmark(self, landmark_id: int):
        """Get landmark coordinates"""
        return self.landmarks.get(landmark_id, (0.5, 0.5))

class MockFrame:
    """Mock camera frame for testing"""
    
    def __init__(self, width: int = 640, height: int = 480):
        self.shape = (height, width, 3)  # OpenCV format: (height, width, channels)

def test_main_loop_integration() -> bool:
    """Test main loop integration without camera"""
    print("Testing main loop integration...")
    
    # Mock the camera-dependent imports
    with patch('main.Camera') as mock_camera_class, \
         patch('main.cv2') as mock_cv2, \
         patch('main.HandTracker') as mock_tracker_class, \
         patch('main.pyautogui') as mock_pyautogui:
        
        # Configure mocks
        mock_camera = Mock()
        mock_camera.open.return_value = True
        mock_camera.read.return_value = (True, MockFrame())
        mock_camera_class.return_value = mock_camera
        
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        
        # Import after patching
        from main import HandControlApp
        
        # Create app with no preview
        app = HandControlApp(preview=False)
        
        # Test pause/resume functionality
        assert not app.is_paused, "Should start unpaused"
        
        # Test cooldown functionality
        assert app._can_click(), "Should be able to click initially"
        assert app._can_scroll(), "Should be able to scroll initially"
        
        app.last_click_time = time.time()
        assert not app._can_click(), "Should not be able to click immediately after"
        
        # Test platform detection
        expected_macos = platform.system() == 'Darwin'
        assert app.is_macos == expected_macos, f"Platform detection failed: {app.is_macos} != {expected_macos}"
        
        print("✅ Main loop integration test PASSED")
        return True

def test_gesture_handling() -> bool:
    """Test gesture handling without camera"""
    print("Testing gesture handling...")
    
    with patch('main.Camera') as mock_camera_class, \
         patch('main.cv2') as mock_cv2, \
         patch('main.HandTracker') as mock_tracker_class, \
         patch('main.pyautogui') as mock_pyautogui:
        
        # Configure mocks
        mock_camera = Mock()
        mock_camera.open.return_value = True
        mock_camera.read.return_value = (True, MockFrame())
        mock_camera_class.return_value = mock_camera
        
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        
        from main import HandControlApp
        
        app = HandControlApp(preview=False)
        
        # Mock cursor controller
        app.cursor_controller = Mock()
        
        # Test MOVE gesture
        landmarks = MockLandmarks({8: (0.3, 0.4)})  # Index finger tip
        app._handle_gesture(GestureType.MOVE, {}, landmarks)
        
        # Should call move_cursor with correct parameters
        app.cursor_controller.move_cursor.assert_called_once()
        args = app.cursor_controller.move_cursor.call_args[0]
        assert len(args) == 4, "move_cursor should be called with 4 arguments"
        assert args[0] == 0.3 * 640, "X coordinate should be scaled correctly"  # 0.3 * frame_width
        assert args[1] == 0.4 * 480, "Y coordinate should be scaled correctly"  # 0.4 * frame_height
        
        # Test LEFT_CLICK gesture
        app.cursor_controller.reset_mock()
        app.last_click_time = 0  # Allow clicking
        app._handle_gesture(GestureType.LEFT_CLICK, {}, None)
        app.cursor_controller.left_click.assert_called_once()
        
        # Test RIGHT_CLICK gesture
        app.cursor_controller.reset_mock()
        app.last_click_time = 0  # Allow clicking
        app._handle_gesture(GestureType.RIGHT_CLICK, {}, None)
        app.cursor_controller.right_click.assert_called_once()
        
        # Test DOUBLE_CLICK gesture
        app.cursor_controller.reset_mock()
        app.last_click_time = 0  # Allow clicking
        app._handle_gesture(GestureType.DOUBLE_CLICK, {}, None)
        app.cursor_controller.double_click.assert_called_once()
        
        # Test SCROLL gesture
        app.cursor_controller.reset_mock()
        app.last_scroll_time = 0  # Allow scrolling
        app._handle_gesture(GestureType.SCROLL, {'scroll_delta': 10}, None)
        app.cursor_controller.scroll.assert_called_once_with(1)  # Positive direction
        
        # Test SCROLL gesture (opposite direction)
        app.cursor_controller.reset_mock()
        app.last_scroll_time = 0  # Allow scrolling
        app._handle_gesture(GestureType.SCROLL, {'scroll_delta': -15}, None)
        app.cursor_controller.scroll.assert_called_once_with(-1)  # Negative direction
        
        # Test DRAG gesture
        app.cursor_controller.reset_mock()
        app._handle_gesture(GestureType.DRAG, {}, None)
        app.cursor_controller.toggle_drag.assert_called_once()
        
        print("✅ Gesture handling test PASSED")
        return True

def test_keyboard_mode() -> bool:
    """Test keyboard mode functionality"""
    print("Testing keyboard mode...")
    
    with patch('main.Camera') as mock_camera_class, \
         patch('main.cv2') as mock_cv2, \
         patch('main.HandTracker') as mock_tracker_class, \
         patch('main.pyautogui') as mock_pyautogui:
        
        # Configure mocks
        mock_camera = Mock()
        mock_camera.open.return_value = True
        mock_camera.read.return_value = (True, MockFrame())
        mock_camera_class.return_value = mock_camera
        
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        
        from main import HandControlApp
        
        app = HandControlApp(preview=False)
        app.cursor_controller = Mock()
        
        # Test keyboard shortcuts for different finger combinations
        test_cases = [
            # (finger_count, thumb_extended, expected_keys, description)
            (1, False, ['escape'], "1 finger → Escape"),
            (2, False, ['enter'], "2 fingers → Enter"),
            (3, False, ['cmd' if app.is_macos else 'ctrl', 'c'], "3 fingers → Copy"),
            (4, False, ['cmd' if app.is_macos else 'ctrl', 'v'], "4 fingers → Paste"),
            (0, True, ['cmd' if app.is_macos else 'alt', 'tab'], "Thumb only → App Switch"),
        ]
        
        for finger_count, thumb_extended, expected_keys, description in test_cases:
            app.cursor_controller.reset_mock()
            gesture_data = {
                'finger_count': finger_count,
                'thumb_extended': thumb_extended
            }
            
            app._handle_keyboard_mode(gesture_data)
            app.cursor_controller.keyboard_shortcut.assert_called_once_with(expected_keys)
            print(f"  ✅ {description}")
        
        # Test keyboard mode activation timing
        app.keyboard_mode_active = False
        app.keyboard_hold_time = 0.1  # Short time for testing
        
        # First call - should start keyboard mode
        app._handle_gesture(GestureType.KEYBOARD, {'finger_count': 5}, None)
        assert app.keyboard_mode_active, "Keyboard mode should be activated"
        
        # Wait and call again - should trigger keyboard action
        time.sleep(0.11)  # Wait longer than hold time
        app.cursor_controller.reset_mock()
        app._handle_gesture(GestureType.KEYBOARD, {'finger_count': 1, 'thumb_extended': False}, None)
        app.cursor_controller.keyboard_shortcut.assert_called_once_with(['escape'])
        assert not app.keyboard_mode_active, "Keyboard mode should exit after action"
        
        print("✅ Keyboard mode test PASSED")
        return True

def test_cooldown_system() -> bool:
    """Test cooldown system"""
    print("Testing cooldown system...")
    
    with patch('main.Camera') as mock_camera_class, \
         patch('main.cv2') as mock_cv2, \
         patch('main.HandTracker') as mock_tracker_class, \
         patch('main.pyautogui') as mock_pyautogui:
        
        # Configure mocks
        mock_camera = Mock()
        mock_camera.open.return_value = True
        mock_camera.read.return_value = (True, MockFrame())
        mock_camera_class.return_value = mock_camera
        
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        
        from main import HandControlApp
        
        app = HandControlApp(preview=False)
        app.cursor_controller = Mock()
        app.click_cooldown = 0.1  # Short cooldown for testing
        app.scroll_cooldown = 0.05
        
        # Test click cooldown
        app.last_click_time = 0  # Allow first click
        app._handle_gesture(GestureType.LEFT_CLICK, {}, None)
        assert app.cursor_controller.left_click.called, "First click should work"
        
        # Immediate second click should be blocked
        app.cursor_controller.reset_mock()
        app._handle_gesture(GestureType.LEFT_CLICK, {}, None)
        assert not app.cursor_controller.left_click.called, "Second click should be blocked"
        
        # After cooldown, click should work again
        time.sleep(0.11)
        app.cursor_controller.reset_mock()
        app._handle_gesture(GestureType.LEFT_CLICK, {}, None)
        assert app.cursor_controller.left_click.called, "Click should work after cooldown"
        
        # Test scroll cooldown  
        app.last_scroll_time = 0  # Allow first scroll
        app._handle_gesture(GestureType.SCROLL, {'scroll_delta': 10}, None)
        assert app.cursor_controller.scroll.called, "First scroll should work"
        
        # Immediate second scroll should be blocked
        app.cursor_controller.reset_mock()
        app._handle_gesture(GestureType.SCROLL, {'scroll_delta': 10}, None)
        assert not app.cursor_controller.scroll.called, "Second scroll should be blocked"
        
        print("✅ Cooldown system test PASSED")
        return True

def test_failsafe_enabled() -> bool:
    """Test that pyautogui FAILSAFE is enabled"""
    print("Testing FAILSAFE...")
    
    with patch('main.Camera') as mock_camera_class, \
         patch('main.cv2') as mock_cv2, \
         patch('main.HandTracker') as mock_tracker_class, \
         patch('main.pyautogui') as mock_pyautogui:
        
        # Configure mocks
        mock_camera = Mock()
        mock_camera.open.return_value = True
        mock_camera_class.return_value = mock_camera
        
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        
        # Set initial state to False to verify it gets set to True
        mock_pyautogui.FAILSAFE = False
        
        from main import HandControlApp
        
        app = HandControlApp(preview=False)
        
        # Check that FAILSAFE was enabled
        assert mock_pyautogui.FAILSAFE == True, "pyautogui.FAILSAFE should be set to True"
        
        print("✅ FAILSAFE test PASSED")
        return True

def run_all_tests() -> bool:
    """Run all Phase 5 tests"""
    print("=== Testing Phase 5: Main Loop + Actions ===\n")
    
    tests = [
        test_main_loop_integration,
        test_gesture_handling,
        test_keyboard_mode,
        test_cooldown_system,
        test_failsafe_enabled
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} FAILED with error: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
            print()
    
    passed = sum(results)
    total = len(results)
    
    if all(results):
        print(f"🎉 All Phase 5 tests PASSED ({passed}/{total})")
        return True
    else:
        print(f"❌ Some Phase 5 tests FAILED ({passed}/{total})")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    
    if success:
        print("\n✅ Phase 5 ready for integration!")
        print("Main loop implements:")
        print("  - Camera → landmarks → gesture → cursor action → preview window")
        print("  - MOVE → cursor follows index finger") 
        print("  - LEFT_CLICK → pinch index+middle")
        print("  - RIGHT_CLICK → 3 finger pinch")
        print("  - DOUBLE_CLICK → thumb-index pinch")
        print("  - SCROLL → 2 fingers spread, Y movement")
        print("  - DRAG → fist+thumb → toggle drag")
        print("  - KEYBOARD → all 5 fingers held 1 second")
        print("  - p = pause/resume, q = quit, r = reset")
        print("  - pyautogui.FAILSAFE = True ALWAYS")
    else:
        print("\n❌ Phase 5 needs fixes before proceeding")
    
    print(f"\nNote: Full camera integration requires OpenCV installation")
    print(f"      (Currently not possible due to disk space: 99% full)")