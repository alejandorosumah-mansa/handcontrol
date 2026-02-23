"""
Hand tracking module using MediaPipe Hands
Supports two-hand tracking with handedness detection.
"""
from typing import Optional, List, Tuple, NamedTuple, Dict
import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False


class HandLandmark(NamedTuple):
    x: float
    y: float
    z: float


class HandLandmarks:
    """Collection of 21 hand landmarks with helper methods"""

    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    INDEX_MCP = 5
    INDEX_PIP = 6
    INDEX_DIP = 7
    INDEX_TIP = 8
    MIDDLE_MCP = 9
    MIDDLE_PIP = 10
    MIDDLE_DIP = 11
    MIDDLE_TIP = 12
    RING_MCP = 13
    RING_PIP = 14
    RING_DIP = 15
    RING_TIP = 16
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20

    def __init__(self, landmarks: List[HandLandmark], handedness: str = "Right"):
        if len(landmarks) != 21:
            raise ValueError(f"Expected 21 landmarks, got {len(landmarks)}")
        self.landmarks = landmarks
        self.handedness = handedness  # "Right" or "Left"

    def __getitem__(self, index: int) -> HandLandmark:
        return self.landmarks[index]

    def get_landmark(self, index: int) -> HandLandmark:
        if 0 <= index < len(self.landmarks):
            return self.landmarks[index]
        raise IndexError(f"Landmark index {index} out of range")

    def to_pixel_coordinates(self, frame_width: int, frame_height: int) -> List[Tuple[int, int]]:
        return [
            (int(lm.x * frame_width), int(lm.y * frame_height))
            for lm in self.landmarks
        ]

    def get_hand_size(self) -> float:
        wrist = self.landmarks[self.WRIST]
        middle_mcp = self.landmarks[self.MIDDLE_MCP]
        dx = middle_mcp.x - wrist.x
        dy = middle_mcp.y - wrist.y
        return np.sqrt(dx * dx + dy * dy)

    def get_palm_center(self) -> Tuple[float, float]:
        """Average of wrist and all MCP joints."""
        indices = [0, 5, 9, 13, 17]
        xs = [self.landmarks[i].x for i in indices]
        ys = [self.landmarks[i].y for i in indices]
        return (sum(xs) / len(xs), sum(ys) / len(ys))


class HandTrackingResult:
    """Result of processing a frame — may contain 0, 1, or 2 hands."""

    def __init__(self):
        self.hands: List[HandLandmarks] = []

    @property
    def dominant(self) -> Optional[HandLandmarks]:
        """Get dominant hand (first matching configured handedness)."""
        return self.hands[0] if self.hands else None

    def get_hand(self, handedness: str) -> Optional[HandLandmarks]:
        for h in self.hands:
            if h.handedness == handedness:
                return h
        return None

    @property
    def count(self) -> int:
        return len(self.hands)


class HandTracker:
    """MediaPipe-based hand tracker with two-hand support."""

    def __init__(self,
                 max_num_hands: int = 2,
                 min_detection_confidence: float = 0.8,
                 min_tracking_confidence: float = 0.7,
                 static_image_mode: bool = False,
                 model_complexity: int = 1):
        if not MEDIAPIPE_AVAILABLE:
            raise ImportError("MediaPipe is not available")
        if not CV2_AVAILABLE:
            raise ImportError("OpenCV is not available")

        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.hands = self.mp_hands.Hands(
            static_image_mode=static_image_mode,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            model_complexity=model_complexity,
        )

    def process_frame(self, frame: np.ndarray) -> HandTrackingResult:
        """Process a frame and return all detected hands with handedness."""
        result = HandTrackingResult()

        # Don't copy — just set writable flag for performance
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        mp_results = self.hands.process(rgb_frame)

        if mp_results.multi_hand_landmarks and mp_results.multi_handedness:
            for hand_lms, hand_info in zip(
                mp_results.multi_hand_landmarks,
                mp_results.multi_handedness
            ):
                # MediaPipe reports handedness from camera's perspective
                # Since we mirror, "Right" in MP = user's right hand
                handedness = hand_info.classification[0].label
                landmarks = [
                    HandLandmark(x=lm.x, y=lm.y, z=lm.z)
                    for lm in hand_lms.landmark
                ]
                result.hands.append(HandLandmarks(landmarks, handedness))

        return result

    def draw_landmarks(self, frame: np.ndarray,
                       hand_landmarks: HandLandmarks,
                       color: Optional[Tuple[int, int, int]] = None) -> np.ndarray:
        """Draw hand landmarks on frame."""
        mp_landmarks = type('MockLandmarks', (), {})()
        mp_landmarks.landmark = []
        for lm in hand_landmarks.landmarks:
            ml = type('MockLandmark', (), {})()
            ml.x, ml.y, ml.z = lm.x, lm.y, lm.z
            mp_landmarks.landmark.append(ml)

        if color:
            landmark_style = self.mp_drawing.DrawingSpec(color=color, thickness=2, circle_radius=2)
            connection_style = self.mp_drawing.DrawingSpec(color=color, thickness=1)
            self.mp_drawing.draw_landmarks(
                frame, mp_landmarks, self.mp_hands.HAND_CONNECTIONS,
                landmark_style, connection_style
            )
        else:
            self.mp_drawing.draw_landmarks(
                frame, mp_landmarks, self.mp_hands.HAND_CONNECTIONS,
                self.mp_drawing_styles.get_default_hand_landmarks_style(),
                self.mp_drawing_styles.get_default_hand_connections_style()
            )
        return frame

    def close(self) -> None:
        if hasattr(self, 'hands') and self.hands:
            self.hands.close()
