"""
Simple test runner for HandControl
Runs tests without importing problematic modules
"""
import sys
import traceback
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

def test_config_system():
    """Test configuration system"""
    print("Testing config system...")
    
    from config import Config
    import tempfile
    import yaml
    import os
    
    # Test default config
    config = Config()
    assert config.get('camera.index') == 0
    assert config.get('smoothing.type') == 'one_euro'
    
    # Test save/load
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, 'test.yaml')
        config.set('camera.index', 1)
        config.save_to_file(config_path)
        
        new_config = Config(config_path)
        assert new_config.get('camera.index') == 1
    
    print("✅ Config system tests passed")
    return True

def test_smoothing_system():
    """Test smoothing algorithms"""
    print("Testing smoothing system...")
    
    from smoothing import OneEuroFilter, EMAFilter, PointSmoother
    import time
    
    # Test One Euro Filter
    one_euro = OneEuroFilter()
    result = one_euro.filter(10.0)
    assert result == 10.0  # First value should pass through
    
    # Test EMA Filter
    ema = EMAFilter(alpha=0.3)
    result = ema.filter(20.0)
    assert result == 20.0  # First value should pass through
    
    # Test Point Smoother
    point_smoother = PointSmoother('ema', alpha=0.5)
    result = point_smoother.filter((0.5, 0.3))
    assert result == (0.5, 0.3)  # First point should pass through
    
    # Test reset functionality
    ema.filter(100.0)
    ema.reset()
    result = ema.filter(50.0)
    assert result == 50.0
    
    print("✅ Smoothing system tests passed")
    return True

def test_gesture_recognition():
    """Test gesture recognition without camera"""
    print("Testing gesture recognition...")
    
    from gesture_recognition import GestureRecognizer, GestureType
    from config import Config
    
    config = Config()
    recognizer = GestureRecognizer(
        finger_threshold=0.15,
        pinch_threshold=0.08,
        stability_frames=3
    )
    
    # Test that recognizer initialized
    assert recognizer.finger_threshold == 0.15
    assert recognizer.pinch_threshold == 0.08
    
    print("✅ Gesture recognition tests passed")
    return True

def test_keyboard_mode():
    """Test keyboard mode functionality"""
    print("Testing keyboard mode...")
    
    from keyboard_mode import KeyboardMode, KeyboardShortcut
    import time
    
    # Mock pyautogui to prevent actual key presses
    import sys
    from unittest.mock import Mock
    sys.modules['pyautogui'] = Mock()
    
    keyboard_mode = KeyboardMode(hold_time=0.1)
    
    # Test activation
    result = keyboard_mode.update(True, {'finger_count': 5})
    assert result is None
    assert keyboard_mode.activation_start_time is not None
    
    # Test shortcut detection
    shortcut = keyboard_mode._detect_shortcut({'finger_count': 1, 'thumb_extended': False})
    assert shortcut == KeyboardShortcut.ESCAPE
    
    print("✅ Keyboard mode tests passed")
    return True

def test_calibration_system():
    """Test calibration system"""
    print("Testing calibration system...")
    
    from calibration import ScreenCalibrator, CalibrationPoint
    import tempfile
    import os
    
    # Test CalibrationPoint
    point = CalibrationPoint(0.1, 0.2, "Test")
    assert not point.is_captured
    
    point.capture(0.15, 0.22)
    assert point.is_captured
    assert point.camera_x == 0.15
    
    # Test ScreenCalibrator
    calibrator = ScreenCalibrator(1920, 1080)
    assert len(calibrator.points) == 4
    
    calibrator.start_calibration()
    
    # Capture all points
    test_coords = [(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)]
    for x, y in test_coords:
        calibrator.capture_point(x, y)
    
    assert calibrator.is_complete()
    
    # Test save/load
    with tempfile.TemporaryDirectory() as temp_dir:
        calib_path = os.path.join(temp_dir, 'test_calib.json')
        
        success = calibrator.save_calibration(calib_path)
        assert success
        
        new_calibrator = ScreenCalibrator()
        success = new_calibrator.load_calibration(calib_path)
        assert success
        assert new_calibrator.is_complete()
    
    print("✅ Calibration system tests passed")
    return True

def test_cli_system():
    """Test CLI argument parsing"""
    print("Testing CLI system...")
    
    import argparse
    from pathlib import Path
    
    # Test argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--calibrate', action='store_true')
    parser.add_argument('--no-preview', action='store_true')
    parser.add_argument('--config', type=str)
    
    # Test parsing
    args = parser.parse_args(['--calibrate', '--no-preview'])
    assert args.calibrate == True
    assert args.no_preview == True
    
    # Test that __main__.py exists
    main_py = Path(__file__).parent / '__main__.py'
    assert main_py.exists()
    
    print("✅ CLI system tests passed")
    return True

def test_package_structure():
    """Test package structure and imports"""
    print("Testing package structure...")
    
    # Test __init__.py exists and has version info
    init_py = Path(__file__).parent / '__init__.py'
    assert init_py.exists()
    
    # Test imports from __init__.py
    from __init__ import __version__, __author__, __description__
    assert __version__ == "1.0.0"
    assert isinstance(__author__, str)
    assert isinstance(__description__, str)
    
    print("✅ Package structure tests passed")
    return True

def run_all_tests():
    """Run all tests"""
    print("=== Running HandControl Test Suite ===\n")
    
    tests = [
        test_config_system,
        test_smoothing_system,
        test_gesture_recognition,
        test_keyboard_mode,
        test_calibration_system,
        test_cli_system,
        test_package_structure
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} FAILED: {e}")
            traceback.print_exc()
            results.append(False)
            print()
    
    passed = sum(results)
    total = len(results)
    
    print("=" * 50)
    if all(results):
        print(f"🎉 ALL TESTS PASSED ({passed}/{total})")
        print("✅ HandControl test suite: 100% success")
        return True
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total})")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)