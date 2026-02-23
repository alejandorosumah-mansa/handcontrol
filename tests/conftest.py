"""pytest configuration and shared fixtures"""
import pytest
import tempfile
import os
import math
from unittest.mock import Mock, patch, MagicMock
from typing import List, Tuple


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def mock_pyautogui():
    with patch('pyautogui.size', return_value=(1920, 1080)), \
         patch('pyautogui.moveTo') as mock_move, \
         patch('pyautogui.click') as mock_click, \
         patch('pyautogui.hotkey') as mock_hotkey, \
         patch('pyautogui.press') as mock_press, \
         patch('pyautogui.doubleClick') as mock_dbl, \
         patch('pyautogui.scroll') as mock_scroll, \
         patch('pyautogui.mouseDown') as mock_down, \
         patch('pyautogui.mouseUp') as mock_up:
        pyautogui_mock = MagicMock()
        pyautogui_mock.FAILSAFE = True
        pyautogui_mock.PAUSE = 0
        yield {
            'move': mock_move, 'click': mock_click,
            'hotkey': mock_hotkey, 'press': mock_press,
            'double_click': mock_dbl, 'scroll': mock_scroll,
            'mouse_down': mock_down, 'mouse_up': mock_up,
        }


@pytest.fixture
def sample_config():
    return {
        'camera': {'index': 0, 'width': 640, 'height': 480, 'fps_target': 30, 'mirror': True},
        'smoothing': {'type': 'one_euro', 'one_euro_freq': 60, 'one_euro_mincutoff': 0.3, 'one_euro_beta': 0.05},
        'gestures': {'finger_threshold': 0.15, 'pinch_threshold': 0.08, 'stability_frames': 2},
        'cursor': {'dead_zone': 0.08, 'sensitivity': 1.0, 'acceleration_curve': True},
    }


class MockLandmark:
    def __init__(self, x: float, y: float, z: float = 0.0):
        self.x = x
        self.y = y
        self.z = z


class MockHandLandmarks:
    """Mock HandLandmarks for testing gesture recognition."""
    WRIST = 0; THUMB_TIP = 4; INDEX_TIP = 8; MIDDLE_TIP = 12
    RING_TIP = 16; PINKY_TIP = 20; MIDDLE_MCP = 9

    def __init__(self, landmarks, handedness="Right"):
        self.landmarks = landmarks
        self.handedness = handedness

    def __getitem__(self, index):
        return self.landmarks[index]

    def get_landmark(self, index):
        return self.landmarks[index]

    def get_hand_size(self):
        w = self.landmarks[0]
        m = self.landmarks[9]
        return math.sqrt((m.x - w.x) ** 2 + (m.y - w.y) ** 2)

    def get_palm_center(self):
        indices = [0, 5, 9, 13, 17]
        xs = [self.landmarks[i].x for i in indices]
        ys = [self.landmarks[i].y for i in indices]
        return (sum(xs) / len(xs), sum(ys) / len(ys))


def make_move_hand() -> MockHandLandmarks:
    """Only index finger extended."""
    lm = [MockLandmark(0.5, 0.7)] * 21  # base
    # Wrist
    lm[0] = MockLandmark(0.5, 0.7)
    # Thumb curled
    lm[3] = MockLandmark(0.34, 0.58)
    lm[4] = MockLandmark(0.35, 0.57)
    # Index extended (tip far above PIP)
    lm[5] = MockLandmark(0.55, 0.6)
    lm[6] = MockLandmark(0.58, 0.5)
    lm[8] = MockLandmark(0.62, 0.3)
    # Middle curled
    lm[9] = MockLandmark(0.5, 0.6)
    lm[10] = MockLandmark(0.51, 0.5)
    lm[12] = MockLandmark(0.53, 0.6)
    # Ring curled
    lm[13] = MockLandmark(0.45, 0.6)
    lm[14] = MockLandmark(0.44, 0.5)
    lm[16] = MockLandmark(0.42, 0.6)
    # Pinky curled
    lm[17] = MockLandmark(0.4, 0.6)
    lm[18] = MockLandmark(0.39, 0.5)
    lm[20] = MockLandmark(0.37, 0.6)
    return MockHandLandmarks(lm)


def make_all_fingers_hand() -> MockHandLandmarks:
    """All 5 fingers extended."""
    lm = [MockLandmark(0.5, 0.7)] * 21
    lm[0] = MockLandmark(0.5, 0.7)
    # Thumb extended (big X distance)
    lm[3] = MockLandmark(0.25, 0.55)
    lm[4] = MockLandmark(0.2, 0.5)
    # Index
    lm[5] = MockLandmark(0.55, 0.6)
    lm[6] = MockLandmark(0.58, 0.5)
    lm[8] = MockLandmark(0.62, 0.3)
    # Middle
    lm[9] = MockLandmark(0.5, 0.6)
    lm[10] = MockLandmark(0.51, 0.5)
    lm[12] = MockLandmark(0.53, 0.3)
    # Ring
    lm[13] = MockLandmark(0.45, 0.6)
    lm[14] = MockLandmark(0.44, 0.5)
    lm[16] = MockLandmark(0.42, 0.3)
    # Pinky
    lm[17] = MockLandmark(0.4, 0.6)
    lm[18] = MockLandmark(0.39, 0.5)
    lm[20] = MockLandmark(0.37, 0.3)
    return MockHandLandmarks(lm)


def make_pinch_hand() -> MockHandLandmarks:
    """Index + middle extended and pinched together."""
    lm = [MockLandmark(0.5, 0.7)] * 21
    lm[0] = MockLandmark(0.5, 0.7)
    # Thumb curled
    lm[3] = MockLandmark(0.34, 0.58)
    lm[4] = MockLandmark(0.35, 0.57)
    # Index extended, pinched to middle
    lm[5] = MockLandmark(0.55, 0.6)
    lm[6] = MockLandmark(0.58, 0.5)
    lm[8] = MockLandmark(0.525, 0.3)
    # Middle extended, pinched to index
    lm[9] = MockLandmark(0.5, 0.6)
    lm[10] = MockLandmark(0.51, 0.5)
    lm[12] = MockLandmark(0.526, 0.301)
    # Ring curled
    lm[13] = MockLandmark(0.45, 0.6)
    lm[14] = MockLandmark(0.44, 0.5)
    lm[16] = MockLandmark(0.42, 0.6)
    # Pinky curled
    lm[17] = MockLandmark(0.4, 0.6)
    lm[18] = MockLandmark(0.39, 0.5)
    lm[20] = MockLandmark(0.37, 0.6)
    return MockHandLandmarks(lm)


def make_fist_hand() -> MockHandLandmarks:
    """All fingers curled (fist)."""
    lm = [MockLandmark(0.5, 0.7)] * 21
    lm[0] = MockLandmark(0.5, 0.7)
    # All tips below their PIPs
    lm[3] = MockLandmark(0.44, 0.62)
    lm[4] = MockLandmark(0.45, 0.63)  # thumb curled
    lm[5] = MockLandmark(0.55, 0.6)
    lm[6] = MockLandmark(0.56, 0.5)
    lm[8] = MockLandmark(0.55, 0.6)   # below PIP
    lm[9] = MockLandmark(0.5, 0.6)
    lm[10] = MockLandmark(0.51, 0.5)
    lm[12] = MockLandmark(0.5, 0.6)
    lm[13] = MockLandmark(0.45, 0.6)
    lm[14] = MockLandmark(0.44, 0.5)
    lm[16] = MockLandmark(0.43, 0.6)
    lm[17] = MockLandmark(0.4, 0.6)
    lm[18] = MockLandmark(0.39, 0.5)
    lm[20] = MockLandmark(0.38, 0.6)
    return MockHandLandmarks(lm)


@pytest.fixture
def move_hand():
    return make_move_hand()


@pytest.fixture
def all_fingers_hand():
    return make_all_fingers_hand()


@pytest.fixture
def pinch_hand():
    return make_pinch_hand()


@pytest.fixture
def fist_hand():
    return make_fist_hand()


@pytest.fixture(autouse=True)
def set_test_environment():
    os.environ['TESTING'] = '1'
    yield
    os.environ.pop('TESTING', None)
