"""
Tests for calibration system
"""
import pytest
import json
import os
from unittest.mock import patch, Mock

def test_calibration_point_initialization():
    """Test CalibrationPoint initialization"""
    from calibration import CalibrationPoint
    
    point = CalibrationPoint(0.1, 0.2, "Test Point")
    
    assert point.screen_x == 0.1
    assert point.screen_y == 0.2
    assert point.name == "Test Point"
    assert not point.is_captured
    assert point.camera_x is None
    assert point.camera_y is None

def test_calibration_point_capture():
    """Test CalibrationPoint capture functionality"""
    from calibration import CalibrationPoint
    
    point = CalibrationPoint(0.1, 0.2, "Test Point")
    
    # Capture coordinates
    point.capture(0.15, 0.22)
    
    assert point.is_captured
    assert point.camera_x == 0.15
    assert point.camera_y == 0.22

def test_calibration_point_serialization():
    """Test CalibrationPoint to_dict and from_dict"""
    from calibration import CalibrationPoint
    
    # Test uncaptured point
    point = CalibrationPoint(0.1, 0.2, "Test Point")
    data = point.to_dict()
    
    assert data['name'] == "Test Point"
    assert data['screen'] == [0.1, 0.2]
    assert data['camera'] is None
    assert not data['captured']
    
    # Test captured point
    point.capture(0.15, 0.22)
    data = point.to_dict()
    
    assert data['camera'] == [0.15, 0.22]
    assert data['captured']
    
    # Test from_dict
    loaded_point = CalibrationPoint.from_dict(data)
    assert loaded_point.name == "Test Point"
    assert loaded_point.screen_x == 0.1
    assert loaded_point.screen_y == 0.2
    assert loaded_point.camera_x == 0.15
    assert loaded_point.camera_y == 0.22
    assert loaded_point.is_captured

def test_screen_calibrator_initialization():
    """Test ScreenCalibrator initialization"""
    from calibration import ScreenCalibrator, CalibrationState
    
    calibrator = ScreenCalibrator(1920, 1080)
    
    assert calibrator.screen_width == 1920
    assert calibrator.screen_height == 1080
    assert len(calibrator.points) == 4
    assert calibrator.current_point_index == 0
    assert calibrator.state == CalibrationState.WAITING
    
    # Check point names
    expected_names = ["Top Left", "Top Right", "Bottom Right", "Bottom Left"]
    actual_names = [point.name for point in calibrator.points]
    assert actual_names == expected_names

def test_screen_calibrator_start():
    """Test calibration start process"""
    from calibration import ScreenCalibrator, CalibrationState
    
    calibrator = ScreenCalibrator()
    calibrator.start_calibration()
    
    assert calibrator.state == CalibrationState.SHOWING_TARGET
    assert calibrator.current_point_index == 0
    
    # All points should be reset
    for point in calibrator.points:
        assert not point.is_captured

def test_screen_calibrator_capture_sequence():
    """Test full calibration capture sequence"""
    from calibration import ScreenCalibrator, CalibrationState
    
    calibrator = ScreenCalibrator()
    calibrator.start_calibration()
    
    # Capture all 4 points
    test_coordinates = [(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)]
    
    for i, (x, y) in enumerate(test_coordinates):
        current_point = calibrator.get_current_target()
        assert current_point is not None
        
        result = calibrator.capture_point(x, y)
        assert result
        assert current_point.is_captured
        assert current_point.camera_x == x
        assert current_point.camera_y == y
        
        if i < 3:
            assert calibrator.state == CalibrationState.SHOWING_TARGET
            assert calibrator.current_point_index == i + 1
        else:
            assert calibrator.state == CalibrationState.COMPLETE
            assert calibrator.is_complete()

def test_screen_calibrator_progress():
    """Test calibration progress tracking"""
    from calibration import ScreenCalibrator
    
    calibrator = ScreenCalibrator()
    calibrator.start_calibration()
    
    # Initial progress
    assert calibrator.get_progress() == 0.0
    
    # Capture points and check progress
    for i in range(4):
        calibrator.capture_point(0.5, 0.5)  # Dummy coordinates
        expected_progress = (i + 1) / 4
        assert calibrator.get_progress() == expected_progress

def test_screen_calibrator_cancel():
    """Test calibration cancellation"""
    from calibration import ScreenCalibrator, CalibrationState
    
    calibrator = ScreenCalibrator()
    calibrator.start_calibration()
    
    calibrator.cancel()
    
    assert calibrator.state == CalibrationState.CANCELLED
    assert calibrator.is_cancelled()

def test_calibration_save_load(temp_dir):
    """Test calibration data save and load"""
    from calibration import ScreenCalibrator
    
    # Create and complete calibration
    calibrator = ScreenCalibrator(1920, 1080)
    calibrator.start_calibration()
    
    test_coordinates = [(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)]
    for x, y in test_coordinates:
        calibrator.capture_point(x, y)
    
    # Save calibration
    calibration_path = os.path.join(temp_dir, 'test_calibration.json')
    result = calibrator.save_calibration(calibration_path)
    assert result
    assert os.path.exists(calibration_path)
    
    # Verify file contents
    with open(calibration_path, 'r') as f:
        data = json.load(f)
    
    assert 'version' in data
    assert 'timestamp' in data
    assert 'screen_resolution' in data
    assert 'points' in data
    assert len(data['points']) == 4
    assert data['screen_resolution'] == [1920, 1080]
    
    # Load into new calibrator
    new_calibrator = ScreenCalibrator()
    result = new_calibrator.load_calibration(calibration_path)
    assert result
    assert new_calibrator.is_complete()
    
    # Verify loaded data matches
    for i, point in enumerate(new_calibrator.points):
        original_point = calibrator.points[i]
        assert point.name == original_point.name
        assert point.screen_x == original_point.screen_x
        assert point.screen_y == original_point.screen_y
        assert point.camera_x == original_point.camera_x
        assert point.camera_y == original_point.camera_y

def test_calibration_save_incomplete():
    """Test that incomplete calibration cannot be saved"""
    from calibration import ScreenCalibrator
    
    calibrator = ScreenCalibrator()
    calibrator.start_calibration()
    
    # Only capture 2 points
    calibrator.capture_point(0.1, 0.1)
    calibrator.capture_point(0.9, 0.1)
    
    # Should fail to save
    result = calibrator.save_calibration('/tmp/incomplete.json')
    assert not result

def test_calibration_load_invalid_file(temp_dir):
    """Test loading invalid calibration file"""
    from calibration import ScreenCalibrator
    
    # Create invalid JSON file
    invalid_path = os.path.join(temp_dir, 'invalid.json')
    with open(invalid_path, 'w') as f:
        f.write('{"invalid": "data"}')
    
    calibrator = ScreenCalibrator()
    result = calibrator.load_calibration(invalid_path)
    assert not result

def test_calibration_load_nonexistent_file():
    """Test loading nonexistent calibration file"""
    from calibration import ScreenCalibrator
    
    calibrator = ScreenCalibrator()
    result = calibrator.load_calibration('/nonexistent/file.json')
    assert not result

def test_calibration_ui_drawing():
    """Test calibration UI drawing (mocked)"""
    from calibration import ScreenCalibrator
    
    calibrator = ScreenCalibrator()
    calibrator.start_calibration()
    
    # Mock frame
    mock_frame = Mock()
    mock_frame.shape = [480, 640]
    
    # Should not crash even if OpenCV not available
    calibrator.draw_calibration_ui(mock_frame)

def test_calibration_current_target():
    """Test get_current_target functionality"""
    from calibration import ScreenCalibrator
    
    calibrator = ScreenCalibrator()
    calibrator.start_calibration()
    
    # Should return first point initially
    current = calibrator.get_current_target()
    assert current is not None
    assert current.name == "Top Left"
    
    # After capturing, should move to next
    calibrator.capture_point(0.1, 0.1)
    current = calibrator.get_current_target()
    assert current is not None
    assert current.name == "Top Right"
    
    # After completing all, should return None
    calibrator.capture_point(0.9, 0.1)  # Top Right
    calibrator.capture_point(0.9, 0.9)  # Bottom Right
    calibrator.capture_point(0.1, 0.9)  # Bottom Left
    
    current = calibrator.get_current_target()
    assert current is None

@patch('calibration.CV2_AVAILABLE', False)
def test_calibration_without_opencv():
    """Test calibration functionality when OpenCV is not available"""
    from calibration import ScreenCalibrator
    
    calibrator = ScreenCalibrator()
    
    # Should still work for basic functionality
    calibrator.start_calibration()
    assert len(calibrator.points) == 4
    
    # UI drawing should not crash
    mock_frame = Mock()
    calibrator.draw_calibration_ui(mock_frame)

def test_calibration_coordinate_validation():
    """Test that calibration validates coordinate ranges"""
    from calibration import ScreenCalibrator
    
    calibrator = ScreenCalibrator()
    calibrator.start_calibration()
    
    # Test valid coordinates
    result = calibrator.capture_point(0.5, 0.5)
    assert result
    
    # Test boundary coordinates  
    calibrator.current_point_index = 1  # Reset for next capture
    result = calibrator.capture_point(0.0, 0.0)
    assert result
    
    calibrator.current_point_index = 2  # Reset for next capture
    result = calibrator.capture_point(1.0, 1.0)
    assert result

def test_run_calibration_tool_without_opencv():
    """Test calibration tool when OpenCV is not available"""
    from calibration import run_calibration_tool
    
    with patch('calibration.CV2_AVAILABLE', False):
        result = run_calibration_tool()
        assert not result  # Should return False when OpenCV not available