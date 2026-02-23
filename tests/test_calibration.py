"""Tests for calibration system"""
import pytest
import json
import os
from unittest.mock import Mock, patch
from calibration import CalibrationPoint, ScreenCalibrator, CalibrationState


def test_point_init():
    p = CalibrationPoint(0.1, 0.2, "Test")
    assert p.screen_x == 0.1
    assert not p.is_captured


def test_point_capture():
    p = CalibrationPoint(0.1, 0.2, "Test")
    p.capture(0.15, 0.22)
    assert p.is_captured
    assert p.camera_x == 0.15


def test_point_serialization():
    p = CalibrationPoint(0.1, 0.2, "Test")
    p.capture(0.15, 0.22)
    d = p.to_dict()
    loaded = CalibrationPoint.from_dict(d)
    assert loaded.camera_x == 0.15
    assert loaded.is_captured


def test_calibrator_init():
    c = ScreenCalibrator(1920, 1080)
    assert len(c.points) == 5  # 4 corners + center
    assert c.state == CalibrationState.WAITING


def test_calibrator_start():
    c = ScreenCalibrator()
    c.start_calibration()
    assert c.state == CalibrationState.SHOWING_TARGET
    assert c.current_point_index == 0


def test_full_calibration_sequence():
    c = ScreenCalibrator()
    c.start_calibration()
    coords = [(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9), (0.5, 0.5)]
    for x, y in coords:
        c.capture_point(x, y)
    assert c.is_complete()
    assert c.get_progress() == 1.0


def test_calibrator_progress():
    c = ScreenCalibrator()
    c.start_calibration()
    assert c.get_progress() == 0.0
    c.capture_point(0.1, 0.1)
    assert c.get_progress() == 1 / 5


def test_calibrator_cancel():
    c = ScreenCalibrator()
    c.start_calibration()
    c.cancel()
    assert c.is_cancelled()


def test_save_load(temp_dir):
    c = ScreenCalibrator(1920, 1080)
    c.start_calibration()
    for x, y in [(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9), (0.5, 0.5)]:
        c.capture_point(x, y)

    path = os.path.join(temp_dir, 'cal.json')
    assert c.save_calibration(path)
    assert os.path.exists(path)

    c2 = ScreenCalibrator()
    assert c2.load_calibration(path)
    assert c2.is_complete()


def test_save_incomplete():
    c = ScreenCalibrator()
    c.start_calibration()
    c.capture_point(0.1, 0.1)
    assert not c.save_calibration('/tmp/incomplete.json')


def test_load_invalid(temp_dir):
    path = os.path.join(temp_dir, 'bad.json')
    with open(path, 'w') as f:
        f.write('{"invalid": true}')
    c = ScreenCalibrator()
    assert not c.load_calibration(path)


def test_load_nonexistent():
    c = ScreenCalibrator()
    assert not c.load_calibration('/nonexistent/file.json')


@pytest.mark.skipif(not __import__('importlib').util.find_spec('cv2'), reason="no cv2")
def test_perspective_transform():
    """After calibration, map_point should use perspective transform."""
    c = ScreenCalibrator(1920, 1080)
    c.start_calibration()
    # Identity-like calibration
    for x, y in [(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9), (0.5, 0.5)]:
        c.capture_point(x, y)

    # Center should map to center
    mx, my = c.map_point(0.5, 0.5)
    assert abs(mx - 0.5) < 0.05
    assert abs(my - 0.5) < 0.05


def test_recalibrate_detection():
    c = ScreenCalibrator()
    c.calibration_hand_size = 0.1
    assert not c.should_recalibrate(0.11, tolerance=0.3)
    assert c.should_recalibrate(0.15, tolerance=0.3)


def test_draw_ui_no_crash():
    c = ScreenCalibrator()
    c.start_calibration()
    mock_frame = Mock()
    mock_frame.shape = [480, 640]
    c.draw_calibration_ui(mock_frame)  # Should not crash
