"""
Threaded camera capture for HandControl
Captures frames on a background thread so processing never blocks capture.
Always provides the latest frame (skips old ones).
"""
import time
import threading
from typing import Optional, Tuple
from collections import deque
import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


class Camera:
    """
    Threaded webcam capture with frame skipping.
    The capture thread runs independently — callers always get the latest frame.
    """

    def __init__(self,
                 camera_index: int = 0,
                 width: int = 640,
                 height: int = 480,
                 fps_target: int = 30,
                 mirror: bool = True,
                 use_threading: bool = True,
                 fps_window_size: int = 30):
        if not CV2_AVAILABLE:
            raise ImportError("OpenCV is not available")

        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps_target = fps_target
        self.mirror = mirror
        self.use_threading = use_threading
        self.fps_window_size = fps_window_size

        # FPS tracking
        self.frame_times: deque = deque(maxlen=fps_window_size)
        self.last_frame_time = time.time()

        # Threading state
        self._lock = threading.Lock()
        self._latest_frame: Optional[np.ndarray] = None
        self._frame_ready = threading.Event()
        self._running = False
        self._thread: Optional[threading.Thread] = None

        self.cap: Optional[cv2.VideoCapture] = None
        self.is_opened = False

    def open(self) -> bool:
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                return False

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps_target)
            # Minimize buffer to reduce latency
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            ret, frame = self.cap.read()
            if not ret:
                self.cap.release()
                return False

            self.is_opened = True

            if self.use_threading:
                self._running = True
                self._thread = threading.Thread(target=self._capture_loop, daemon=True)
                self._thread.start()

            return True
        except Exception as e:
            print(f"Error opening camera: {e}")
            if self.cap:
                self.cap.release()
            return False

    def _capture_loop(self) -> None:
        """Background thread: continuously grab the latest frame."""
        while self._running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                continue
            if self.mirror:
                frame = cv2.flip(frame, 1)
            with self._lock:
                self._latest_frame = frame
            self._frame_ready.set()

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        if not self.is_opened or not self.cap:
            return False, None

        if self.use_threading:
            with self._lock:
                frame = self._latest_frame
            if frame is None:
                return False, None
            # Update FPS tracking
            now = time.time()
            self.frame_times.append(now - self.last_frame_time)
            self.last_frame_time = now
            return True, frame.copy()
        else:
            ret, frame = self.cap.read()
            if not ret:
                return False, None
            if self.mirror:
                frame = cv2.flip(frame, 1)
            now = time.time()
            self.frame_times.append(now - self.last_frame_time)
            self.last_frame_time = now
            return True, frame

    def get_fps(self) -> float:
        if len(self.frame_times) == 0:
            return 0.0
        avg = sum(self.frame_times) / len(self.frame_times)
        return 1.0 / avg if avg > 0 else 0.0

    def close(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        if self.cap:
            self.cap.release()
            self.is_opened = False

    def __enter__(self):
        if not self.open():
            raise RuntimeError("Failed to open camera")
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        if hasattr(self, 'cap'):
            self.close()
