"""
Test Phase 6: Enhanced Keyboard Shortcut Mode
Tests integrated keyboard mode functionality
"""
import time
import platform
from unittest.mock import Mock, patch
from keyboard_mode import KeyboardMode, KeyboardShortcut, KeyboardModeVisualizer

def test_keyboard_mode_integration() -> bool:
    """Test keyboard mode class integration"""
    print("Testing keyboard mode integration...")
    
    feedback_events = []
    def mock_feedback(event, data):
        feedback_events.append((event, data))
    
    keyboard_mode = KeyboardMode(hold_time=0.1, feedback_callback=mock_feedback)
    
    # Test activation sequence
    result = keyboard_mode.update(True, {'finger_count': 5})
    assert result is None
    assert len(feedback_events) == 1
    assert feedback_events[0][0] == "keyboard_activating"
    
    # Wait and activate
    time.sleep(0.11)
    result = keyboard_mode.update(True, {'finger_count': 5})
    assert result is None
    assert keyboard_mode.is_active
    
    # Test shortcut execution
    result = keyboard_mode.update(False, {'finger_count': 1, 'thumb_extended': False})
    assert result == KeyboardShortcut.ESCAPE
    assert not keyboard_mode.is_active  # Auto-exit
    
    print("✅ Keyboard mode integration working")
    return True

def test_visualizer_available() -> bool:
    """Test that visualizer handles OpenCV availability gracefully"""
    print("Testing keyboard mode visualizer...")
    
    visualizer = KeyboardModeVisualizer()
    
    # Should not crash regardless of OpenCV availability
    mock_frame = Mock()
    mock_frame.shape = [480, 640]
    
    status = {
        'is_active': False,
        'is_activating': False,
        'platform': 'Darwin'
    }
    
    try:
        visualizer.draw_keyboard_status(mock_frame, status)
        visualizer.draw_shortcut_reference(mock_frame)
        print("✅ Visualizer handles gracefully")
        return True
    except Exception as e:
        print(f"❌ Visualizer error: {e}")
        return False

def test_platform_specific_shortcuts() -> bool:
    """Test platform-specific keyboard shortcuts"""
    print("Testing platform-specific shortcuts...")
    
    with patch('pyautogui.hotkey') as mock_hotkey, \
         patch('pyautogui.press') as mock_press:
        
        keyboard_mode = KeyboardMode()
        
        # Test copy shortcut
        keyboard_mode.execute_shortcut(KeyboardShortcut.COPY)
        
        if platform.system() == 'Darwin':
            mock_hotkey.assert_called_with('cmd', 'c')
        else:
            mock_hotkey.assert_called_with('ctrl', 'c')
        
        # Test app switch
        mock_hotkey.reset_mock()
        keyboard_mode.execute_shortcut(KeyboardShortcut.APP_SWITCH)
        
        if platform.system() == 'Darwin':
            mock_hotkey.assert_called_with('cmd', 'tab')
        else:
            mock_hotkey.assert_called_with('alt', 'tab')
        
        # Test single key
        mock_press.reset_mock()
        keyboard_mode.execute_shortcut(KeyboardShortcut.ESCAPE)
        mock_press.assert_called_with('escape')
        
        print("✅ Platform-specific shortcuts working")
        return True

def test_auto_exit_behavior() -> bool:
    """Test that keyboard mode auto-exits after shortcut execution"""
    print("Testing auto-exit behavior...")
    
    keyboard_mode = KeyboardMode(hold_time=0.01)
    
    # Activate keyboard mode
    keyboard_mode.update(True, {'finger_count': 5})
    time.sleep(0.02)
    keyboard_mode.update(True, {'finger_count': 5})
    assert keyboard_mode.is_active
    
    # Execute shortcut - should auto-exit
    result = keyboard_mode.update(False, {'finger_count': 2, 'thumb_extended': False})
    assert result == KeyboardShortcut.ENTER
    assert not keyboard_mode.is_active  # Auto-exit
    
    print("✅ Auto-exit behavior working")
    return True

def test_gesture_to_shortcut_mapping() -> bool:
    """Test all gesture to shortcut mappings"""
    print("Testing gesture to shortcut mappings...")
    
    keyboard_mode = KeyboardMode()
    
    test_cases = [
        ({'finger_count': 1, 'thumb_extended': False}, KeyboardShortcut.ESCAPE, "1 finger → Escape"),
        ({'finger_count': 2, 'thumb_extended': False}, KeyboardShortcut.ENTER, "2 fingers → Enter"),
        ({'finger_count': 3, 'thumb_extended': False}, KeyboardShortcut.COPY, "3 fingers → Copy"),
        ({'finger_count': 4, 'thumb_extended': False}, KeyboardShortcut.PASTE, "4 fingers → Paste"),
        ({'finger_count': 0, 'thumb_extended': True}, KeyboardShortcut.APP_SWITCH, "Thumb only → App Switch"),
    ]
    
    for gesture_data, expected_shortcut, description in test_cases:
        detected_shortcut = keyboard_mode._detect_shortcut(gesture_data)
        assert detected_shortcut == expected_shortcut, f"Failed: {description}"
        print(f"  ✅ {description}")
    
    return True

def test_main_loop_integration() -> bool:
    """Test integration with main loop (mocked)"""
    print("Testing main loop integration...")
    
    # Mock the dependencies that require OpenCV
    with patch('main.Camera') as mock_camera_class, \
         patch('main.HandTracker') as mock_tracker_class:
        
        # Configure mocks
        mock_camera = Mock()
        mock_camera.open.return_value = True
        mock_camera.read.return_value = (True, Mock())
        mock_camera_class.return_value = mock_camera
        
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        
        # Import after mocking
        from main import HandControlApp
        
        app = HandControlApp(preview=False)
        
        # Test that keyboard mode is initialized
        assert hasattr(app, 'keyboard_mode')
        assert hasattr(app, 'keyboard_visualizer')
        assert hasattr(app, 'keyboard_feedback_message')
        
        # Test feedback callback
        app._keyboard_feedback("keyboard_activating", {"remaining": 1.5})
        assert "KEYBOARD 1.5s" in app.keyboard_feedback_message
        
        app._keyboard_feedback("keyboard_active", {})
        assert app.keyboard_feedback_message == "KEYBOARD MODE"
        
        app._keyboard_feedback("keyboard_inactive", {})
        assert app.keyboard_feedback_message == ""
        
        print("✅ Main loop integration working")
        return True

def test_failsafe_always_enabled() -> bool:
    """Test that FAILSAFE is always enabled"""
    print("Testing FAILSAFE enforcement...")
    
    # Set initial state to False
    import pyautogui
    pyautogui.FAILSAFE = False
    
    # Create keyboard mode - should enable FAILSAFE
    keyboard_mode = KeyboardMode()
    
    assert pyautogui.FAILSAFE == True, "FAILSAFE should be enabled by KeyboardMode"
    
    print("✅ FAILSAFE always enabled")
    return True

def run_all_tests() -> bool:
    """Run all Phase 6 tests"""
    print("=== Testing Phase 6: Enhanced Keyboard Shortcut Mode ===\n")
    
    tests = [
        test_keyboard_mode_integration,
        test_visualizer_available,
        test_platform_specific_shortcuts,
        test_auto_exit_behavior,
        test_gesture_to_shortcut_mapping,
        test_main_loop_integration,
        test_failsafe_always_enabled
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
        print(f"🎉 All Phase 6 tests PASSED ({passed}/{total})")
        return True
    else:
        print(f"❌ Some Phase 6 tests FAILED ({passed}/{total})")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    
    if success:
        print("\n✅ Phase 6 COMPLETE!")
        print("\nEnhanced Keyboard Shortcut Mode features:")
        print("  🖐️ All 5 fingers held 1 second → KEYBOARD MODE")
        print("  ⚡ 1 finger (index) → Escape")
        print("  ↵ 2 fingers (index+middle) → Enter")  
        print("  📋 3 fingers (index+middle+ring) → Cmd+C (macOS) / Ctrl+C (Linux)")
        print("  📄 4 fingers (no thumb) → Cmd+V / Ctrl+V")
        print("  🔄 Thumb only → Cmd+Tab / Alt+Tab")
        print("  🔄 Auto-exit after shortcut fires")
        print("  🖥️ Auto-detect platform for modifier keys")
        print("  👁️ Visual feedback with progress bar and shortcut reference")
        print("  🛡️ FAILSAFE always enabled")
        
    else:
        print("\n❌ Phase 6 needs fixes before proceeding")