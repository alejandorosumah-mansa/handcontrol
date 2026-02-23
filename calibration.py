"""
Calibration system with perspective transform for HandControl.
5-point calibration (4 corners + center) with hand-size normalization.
"""
import time
import json
import os
import math
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum
import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


class CalibrationState(Enum):
    WAITING = "waiting"
    SHOWING_TARGET = "showing_target"
    CAPTURING = "capturing"
    COMPLETE = "complete"
    CANCELLED = "cancelled"


class CalibrationPoint:
    def __init__(self, screen_x: float, screen_y: float, name: str):
        self.screen_x = screen_x
        self.screen_y = screen_y
        self.name = name
        self.camera_x: Optional[float] = None
        self.camera_y: Optional[float] = None
        self.is_captured = False
        self.samples: List[Tuple[float, float]] = []

    def capture(self, camera_x: float, camera_y: float) -> None:
        self.camera_x = camera_x
        self.camera_y = camera_y
        self.is_captured = True

    def add_sample(self, x: float, y: float) -> None:
        self.samples.append((x, y))

    def finalize_from_samples(self) -> None:
        if self.samples:
            avg_x = sum(s[0] for s in self.samples) / len(self.samples)
            avg_y = sum(s[1] for s in self.samples) / len(self.samples)
            self.capture(avg_x, avg_y)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'screen': [self.screen_x, self.screen_y],
            'camera': [self.camera_x, self.camera_y] if self.is_captured else None,
            'captured': self.is_captured,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CalibrationPoint':
        point = cls(data['screen'][0], data['screen'][1], data['name'])
        if data['captured'] and data['camera']:
            point.capture(data['camera'][0], data['camera'][1])
        return point


class ScreenCalibrator:
    """5-point calibration with perspective transform."""

    def __init__(self, screen_width: int = 1920, screen_height: int = 1080):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # 4 corners for perspective transform + center for validation
        self.points = [
            CalibrationPoint(0.1, 0.1, "Top Left"),
            CalibrationPoint(0.9, 0.1, "Top Right"),
            CalibrationPoint(0.9, 0.9, "Bottom Right"),
            CalibrationPoint(0.1, 0.9, "Bottom Left"),
            CalibrationPoint(0.5, 0.5, "Center"),
        ]

        self.current_point_index = 0
        self.state = CalibrationState.WAITING
        self.show_instructions = True

        # Perspective transform matrix
        self._transform_matrix: Optional[np.ndarray] = None

        # Hand size at calibration time (for auto-recalibration)
        self.calibration_hand_size: Optional[float] = None

    def start_calibration(self) -> None:
        self.current_point_index = 0
        self.state = CalibrationState.SHOWING_TARGET

        for point in self.points:
            point.is_captured = False
            point.camera_x = None
            point.camera_y = None
            point.samples.clear()

        self._transform_matrix = None

    def get_current_target(self) -> Optional[CalibrationPoint]:
        if 0 <= self.current_point_index < len(self.points):
            return self.points[self.current_point_index]
        return None

    def capture_point(self, finger_x: float, finger_y: float) -> bool:
        current = self.get_current_target()
        if not current:
            return False

        current.capture(finger_x, finger_y)
        self.current_point_index += 1

        if self.current_point_index >= len(self.points):
            self.state = CalibrationState.COMPLETE
            self._compute_transform()
            return True

        self.state = CalibrationState.SHOWING_TARGET
        return True

    def _compute_transform(self) -> None:
        """Compute perspective transform from the 4 corner points."""
        if not CV2_AVAILABLE:
            return

        # Source points (camera space)
        src = np.float32([
            [self.points[i].camera_x, self.points[i].camera_y]
            for i in range(4)
        ])

        # Destination points (screen normalized space)
        dst = np.float32([
            [self.points[i].screen_x, self.points[i].screen_y]
            for i in range(4)
        ])

        self._transform_matrix = cv2.getPerspectiveTransform(src, dst)

    def map_point(self, camera_x: float, camera_y: float) -> Tuple[float, float]:
        """Map camera coordinates to screen coordinates using perspective transform."""
        if self._transform_matrix is not None:
            pt = np.float32([[[camera_x, camera_y]]])
            mapped = cv2.perspectiveTransform(pt, self._transform_matrix)
            return float(mapped[0][0][0]), float(mapped[0][0][1])
        # Fallback: identity
        return camera_x, camera_y

    def should_recalibrate(self, current_hand_size: float, tolerance: float = 0.3) -> bool:
        """Check if hand size changed enough to warrant recalibration."""
        if self.calibration_hand_size is None:
            return False
        ratio = abs(current_hand_size - self.calibration_hand_size) / self.calibration_hand_size
        return ratio > tolerance

    def is_complete(self) -> bool:
        return self.state == CalibrationState.COMPLETE

    def is_cancelled(self) -> bool:
        return self.state == CalibrationState.CANCELLED

    def cancel(self) -> None:
        self.state = CalibrationState.CANCELLED

    def get_progress(self) -> float:
        if len(self.points) == 0:
            return 0.0
        return self.current_point_index / len(self.points)

    def save_calibration(self, filepath: str) -> bool:
        if not self.is_complete():
            return False

        data = {
            'version': '2.0',
            'timestamp': time.time(),
            'screen_resolution': [self.screen_width, self.screen_height],
            'points': [p.to_dict() for p in self.points],
            'hand_size': self.calibration_hand_size,
        }

        try:
            filepath = os.path.expanduser(filepath)
            os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception:
            return False

    def load_calibration(self, filepath: str) -> bool:
        try:
            filepath = os.path.expanduser(filepath)
            with open(filepath, 'r') as f:
                data = json.load(f)

            if 'points' not in data:
                return False

            points_data = data['points']
            if len(points_data) < 4:
                return False

            self.points = [CalibrationPoint.from_dict(pd) for pd in points_data]
            # Pad to 5 if old format had only 4
            while len(self.points) < 5:
                self.points.append(CalibrationPoint(0.5, 0.5, "Center"))

            if 'screen_resolution' in data:
                self.screen_width, self.screen_height = data['screen_resolution']

            self.calibration_hand_size = data.get('hand_size')
            self.state = CalibrationState.COMPLETE
            self._compute_transform()
            return True
        except Exception:
            return False

    def draw_calibration_ui(self, frame) -> None:
        if not CV2_AVAILABLE:
            return

        h, w = frame.shape[:2]
        current = self.get_current_target()

        if current and self.state == CalibrationState.SHOWING_TARGET:
            tx = int(current.screen_x * w)
            ty = int(current.screen_y * h)

            # Animated circle
            t = time.time()
            pulse = int(5 * math.sin(t * 4))

            # Outer ring
            cv2.circle(frame, (tx, ty), 50 + pulse, (255, 255, 255), 2)
            # Inner dot
            cv2.circle(frame, (tx, ty), 8, (0, 122, 255), -1)
            # Crosshair
            cv2.line(frame, (tx - 20, ty), (tx + 20, ty), (255, 255, 255), 1)
            cv2.line(frame, (tx, ty - 20), (tx, ty + 20), (255, 255, 255), 1)

            label = f"{current.name} ({self.current_point_index + 1}/{len(self.points)})"
            cv2.putText(frame, label, (tx - 60, ty - 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Progress
        progress = self.get_progress()
        bar_w = int(w * 0.4)
        bar_x = (w - bar_w) // 2
        bar_y = h - 40
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + 12), (60, 60, 60), -1)
        if progress > 0:
            cv2.rectangle(frame, (bar_x, bar_y),
                          (bar_x + int(bar_w * progress), bar_y + 12), (0, 122, 255), -1)


def run_calibration_tool(camera_index: int = 0) -> bool:
    if not CV2_AVAILABLE:
        return False
    # Placeholder — real calibration happens in UI module
    return False
