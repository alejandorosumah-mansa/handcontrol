"""
pytest configuration and shared fixtures
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir

@pytest.fixture
def mock_cv2():
    """Mock OpenCV for tests that don't need real camera"""
    with patch('cv2.VideoCapture') as mock_cap:
        mock_instance = Mock()
        mock_instance.isOpened.return_value = True
        mock_instance.read.return_value = (True, Mock())
        mock_cap.return_value = mock_instance
        yield mock_cap

@pytest.fixture
def mock_pyautogui():
    """Mock pyautogui to prevent actual cursor/keyboard actions during tests"""
    with patch('pyautogui.size', return_value=(1920, 1080)), \
         patch('pyautogui.moveTo') as mock_move, \
         patch('pyautogui.click') as mock_click, \
         patch('pyautogui.hotkey') as mock_hotkey, \
         patch('pyautogui.press') as mock_press:
        
        # Ensure FAILSAFE is always set to True in tests
        with patch('pyautogui.FAILSAFE', True):
            yield {
                'move': mock_move,
                'click': mock_click,  
                'hotkey': mock_hotkey,
                'press': mock_press
            }

@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return {
        'camera': {
            'index': 0,
            'width': 640,
            'height': 480,
            'fps_target': 30,
            'mirror': True
        },
        'smoothing': {
            'type': 'one_euro',
            'one_euro_freq': 30,
            'one_euro_mincutoff': 1.0,
            'one_euro_beta': 0.007
        },
        'gestures': {
            'finger_threshold': 0.15,
            'pinch_threshold': 0.08,
            'stability_frames': 3
        }
    }

@pytest.fixture
def mock_hand_landmarks():
    """Mock hand landmarks for testing"""
    class MockLandmarks:
        def __init__(self):
            # Standard MediaPipe hand landmarks (21 points)
            self.landmarks = {
                0: (0.5, 0.8),     # WRIST
                4: (0.3, 0.6),     # THUMB_TIP
                8: (0.4, 0.3),     # INDEX_FINGER_TIP
                12: (0.5, 0.2),    # MIDDLE_FINGER_TIP
                16: (0.6, 0.3),    # RING_FINGER_TIP
                20: (0.7, 0.4),    # PINKY_TIP
                9: (0.4, 0.5),     # INDEX_FINGER_MCP
            }
        
        def get_landmark(self, idx):
            return self.landmarks.get(idx, (0.5, 0.5))
        
        def get_landmarks(self):
            return self.landmarks
    
    return MockLandmarks()

@pytest.fixture(autouse=True)
def set_test_environment():
    """Set up test environment variables"""
    os.environ['TESTING'] = '1'
    yield
    if 'TESTING' in os.environ:
        del os.environ['TESTING']