"""Tests for hand tracker"""
import pytest
import numpy as np
from hand_tracker import HandLandmark, HandLandmarks, HandTrackingResult


def test_hand_landmark_creation():
    lm = HandLandmark(0.5, 0.3, 0.1)
    assert lm.x == 0.5
    assert lm.y == 0.3


def test_hand_landmarks_validation():
    with pytest.raises(ValueError):
        HandLandmarks([HandLandmark(0, 0, 0)] * 10)


def test_hand_landmarks_21():
    lms = [HandLandmark(i / 21.0, i / 21.0, 0) for i in range(21)]
    h = HandLandmarks(lms)
    assert h[0].x == 0.0
    assert h[20].x == pytest.approx(20 / 21.0)


def test_hand_size():
    lms = [HandLandmark(0.5, 0.5, 0)] * 21
    lms[0] = HandLandmark(0.5, 0.8, 0)   # wrist
    lms[9] = HandLandmark(0.5, 0.6, 0)   # middle MCP
    h = HandLandmarks(lms)
    assert h.get_hand_size() == pytest.approx(0.2, abs=0.01)


def test_handedness():
    lms = [HandLandmark(0.5, 0.5, 0)] * 21
    h = HandLandmarks(lms, handedness="Left")
    assert h.handedness == "Left"


def test_palm_center():
    lms = [HandLandmark(0.5, 0.5, 0)] * 21
    lms[0] = HandLandmark(0.5, 0.7, 0)
    lms[5] = HandLandmark(0.55, 0.6, 0)
    lms[9] = HandLandmark(0.5, 0.6, 0)
    lms[13] = HandLandmark(0.45, 0.6, 0)
    lms[17] = HandLandmark(0.4, 0.6, 0)
    h = HandLandmarks(lms)
    cx, cy = h.get_palm_center()
    assert 0.4 < cx < 0.6
    assert 0.5 < cy < 0.7


def test_pixel_coordinates():
    lms = [HandLandmark(0.5, 0.5, 0)] * 21
    h = HandLandmarks(lms)
    pixels = h.to_pixel_coordinates(640, 480)
    assert len(pixels) == 21
    assert pixels[0] == (320, 240)


def test_tracking_result():
    r = HandTrackingResult()
    assert r.count == 0
    assert r.dominant is None

    lms = [HandLandmark(0.5, 0.5, 0)] * 21
    r.hands.append(HandLandmarks(lms, "Right"))
    assert r.count == 1
    assert r.dominant.handedness == "Right"
    assert r.get_hand("Right") is not None
    assert r.get_hand("Left") is None
