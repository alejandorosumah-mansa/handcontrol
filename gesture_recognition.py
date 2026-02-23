"""
Gesture Recognition Engine for HandControl
Two-hand support, grab/resize gestures, relative thresholds.
"""
import time
import math
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
from collections import deque

try:
    from hand_tracker import HandLandmarks, HandTrackingResult
except ImportError:
    pass


class GestureType(Enum):
    IDLE = "idle"
    MOVE = "move"
    LEFT_CLICK = "left_click"
    RIGHT_CLICK = "right_click"
    DOUBLE_CLICK = "double_click"
    SCROLL = "scroll"
    DRAG = "drag"
    KEYBOARD = "keyboard"
    GRAB = "grab"
    WINDOW_MOVE = "window_move"
    WINDOW_MINIMIZE = "window_minimize"
    WINDOW_MAXIMIZE = "window_maximize"
    TWO_HAND_RESIZE = "two_hand_resize"


class GestureState:
    def __init__(self, gesture_type: GestureType, confidence: float = 1.0,
                 data: Optional[Dict[str, Any]] = None):
        self.gesture_type = gesture_type
        self.confidence = confidence
        self.data = data or {}
        self.timestamp = time.time()


class GestureRecognizer:
    """Hand gesture recognition with two-hand and window management support."""

    def __init__(self,
                 finger_threshold: float = 0.15,
                 pinch_threshold: float = 0.08,
                 grab_threshold: float = 0.12,
                 stability_frames: int = 2,
                 cooldown_click_ms: int = 300,
                 cooldown_scroll_ms: int = 50,
                 keyboard_hold_time: float = 1.0,
                 grab_velocity_threshold: float = 0.15,
                 dominant_hand: str = "Right"):
        self.finger_threshold = finger_threshold
        self.pinch_threshold = pinch_threshold
        self.grab_threshold = grab_threshold
        self.stability_frames = stability_frames
        self.cooldown_click_ms = cooldown_click_ms
        self.cooldown_scroll_ms = cooldown_scroll_ms
        self.keyboard_hold_time = keyboard_hold_time
        self.grab_velocity_threshold = grab_velocity_threshold
        self.dominant_hand = dominant_hand

        self.gesture_history: deque = deque(maxlen=stability_frames)
        self.stable_gesture: Optional[GestureState] = None
        self.last_click_time = 0.0
        self.last_scroll_time = 0.0

        # Keyboard mode
        self.keyboard_mode_start: Optional[float] = None
        self.in_keyboard_mode = False

        # Grab/window management state
        self._prev_palm_center: Optional[Tuple[float, float]] = None
        self._grab_started = False
        self._grab_start_pos: Optional[Tuple[float, float]] = None
        self._was_open_hand = False

        # Two-hand resize state
        self._prev_two_hand_distance: Optional[float] = None

        # Scroll tracking
        self._prev_scroll_y: Optional[float] = None

    @staticmethod
    def _euclidean(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)

    def _fingers_extended(self, landmarks: 'HandLandmarks', hand_size: float) -> List[bool]:
        """Check which of the 5 fingers are extended."""
        tips = [4, 8, 12, 16, 20]
        pips = [3, 6, 10, 14, 18]
        threshold = self.finger_threshold * hand_size
        extended = []
        for tip_idx, pip_idx in zip(tips, pips):
            tip = landmarks[tip_idx]
            pip_ = landmarks[pip_idx]
            if tip_idx == 4:  # Thumb
                distance = abs(tip.x - pip_.x)
            else:
                distance = pip_.y - tip.y
            extended.append(distance > threshold)
        return extended

    def _is_fist(self, landmarks: 'HandLandmarks', hand_size: float) -> bool:
        """All fingers curled (fist)."""
        ext = self._fingers_extended(landmarks, hand_size)
        return not any(ext)

    def _detect_pinch(self, landmarks: 'HandLandmarks',
                      idx1: int, idx2: int, hand_size: float) -> bool:
        p1, p2 = landmarks[idx1], landmarks[idx2]
        dist = self._euclidean((p1.x, p1.y), (p2.x, p2.y))
        return dist < self.pinch_threshold * hand_size

    def _recognize_single_hand(self, landmarks: 'HandLandmarks') -> GestureState:
        """Recognize gesture from a single hand."""
        hand_size = landmarks.get_hand_size()
        fingers = self._fingers_extended(landmarks, hand_size)
        thumb, index, middle, ring, pinky = fingers
        ext_count = sum(fingers)

        # KEYBOARD: All 5 fingers open, held for keyboard_hold_time
        if all(fingers):
            self._was_open_hand = True
            if self.keyboard_mode_start is None:
                self.keyboard_mode_start = time.time()
            elif time.time() - self.keyboard_mode_start >= self.keyboard_hold_time:
                return GestureState(GestureType.KEYBOARD, 1.0, {
                    'hand_size': hand_size,
                    'finger_count': 5,
                })
            return GestureState(GestureType.IDLE, 0.5, {'building_keyboard': True})
        else:
            self.keyboard_mode_start = None

        # GRAB: Transition from open hand to fist
        is_fist = self._is_fist(landmarks, hand_size)
        palm = landmarks.get_palm_center()

        if is_fist and self._was_open_hand:
            if not self._grab_started:
                self._grab_started = True
                self._grab_start_pos = palm
                self._was_open_hand = False
                return GestureState(GestureType.GRAB, 1.0, {
                    'palm': palm, 'hand_size': hand_size
                })

        if is_fist and self._grab_started:
            # Window move while grabbed
            delta_y = 0.0
            if self._prev_palm_center:
                delta_y = palm[1] - self._prev_palm_center[1]
            self._prev_palm_center = palm

            # Quick pull down = minimize, push up = maximize
            if self._grab_start_pos:
                total_dy = palm[1] - self._grab_start_pos[1]
                if total_dy > self.grab_velocity_threshold:
                    self._grab_started = False
                    self._was_open_hand = False
                    return GestureState(GestureType.WINDOW_MINIMIZE, 1.0, {
                        'hand_size': hand_size
                    })
                elif total_dy < -self.grab_velocity_threshold:
                    self._grab_started = False
                    self._was_open_hand = False
                    return GestureState(GestureType.WINDOW_MAXIMIZE, 1.0, {
                        'hand_size': hand_size
                    })

            return GestureState(GestureType.WINDOW_MOVE, 1.0, {
                'palm': palm, 'delta_y': delta_y, 'hand_size': hand_size
            })

        if not is_fist:
            self._grab_started = False
            self._grab_start_pos = None
            if ext_count >= 3:
                self._was_open_hand = True

        self._prev_palm_center = palm

        # MOVE: Only index finger extended
        if index and not middle and not ring and not pinky and not thumb:
            pos = landmarks[8]
            return GestureState(GestureType.MOVE, 1.0, {
                'cursor_pos': (pos.x, pos.y), 'hand_size': hand_size
            })

        # LEFT_CLICK: Index + middle pinched
        if index and middle and not ring and not pinky:
            if self._detect_pinch(landmarks, 8, 12, hand_size):
                return GestureState(GestureType.LEFT_CLICK, 1.0, {'hand_size': hand_size})

        # RIGHT_CLICK: Index + middle + ring, index+middle pinched
        if index and middle and ring and not pinky:
            if self._detect_pinch(landmarks, 8, 12, hand_size):
                return GestureState(GestureType.RIGHT_CLICK, 1.0, {'hand_size': hand_size})

        # DOUBLE_CLICK: Thumb-index pinch
        if self._detect_pinch(landmarks, 4, 8, hand_size):
            return GestureState(GestureType.DOUBLE_CLICK, 1.0, {'hand_size': hand_size})

        # SCROLL: Index + middle spread
        if index and middle and not ring and not pinky:
            if not self._detect_pinch(landmarks, 8, 12, hand_size):
                scroll_y = (landmarks[8].y + landmarks[12].y) / 2
                scroll_delta = 0.0
                if self._prev_scroll_y is not None:
                    scroll_delta = (self._prev_scroll_y - scroll_y) * 100
                self._prev_scroll_y = scroll_y
                return GestureState(GestureType.SCROLL, 1.0, {
                    'scroll_y': scroll_y, 'scroll_delta': scroll_delta,
                    'hand_size': hand_size
                })
        else:
            self._prev_scroll_y = None

        # DRAG: Fist with thumb out
        if thumb and not index and not middle and not ring and not pinky:
            return GestureState(GestureType.DRAG, 1.0, {'hand_size': hand_size})

        return GestureState(GestureType.IDLE, 0.0, {'extended_fingers': ext_count})

    def process_two_hands(self, result: 'HandTrackingResult',
                          dominant: str = "Right") -> Optional[GestureState]:
        """
        Process two-hand gestures (like pinch-to-resize).
        Returns a gesture if a two-hand gesture is detected, else None.
        """
        if result.count < 2:
            self._prev_two_hand_distance = None
            return None

        left = result.get_hand("Left")
        right = result.get_hand("Right")
        if not left or not right:
            return None

        # Two-hand resize: both hands pinching, distance between them = size
        left_pinch = self._detect_pinch(left, 4, 8, left.get_hand_size())
        right_pinch = self._detect_pinch(right, 4, 8, right.get_hand_size())

        if left_pinch and right_pinch:
            lc = left.get_palm_center()
            rc = right.get_palm_center()
            dist = self._euclidean(lc, rc)
            delta = 0.0
            if self._prev_two_hand_distance is not None:
                delta = dist - self._prev_two_hand_distance
            self._prev_two_hand_distance = dist
            return GestureState(GestureType.TWO_HAND_RESIZE, 1.0, {
                'distance': dist, 'delta': delta,
                'left_center': lc, 'right_center': rc,
            })

        self._prev_two_hand_distance = None
        return None

    def process_landmarks(self, landmarks: Optional['HandLandmarks']) -> Optional[GestureState]:
        """Process single-hand landmarks and return stable gesture."""
        current_time = time.time()

        if landmarks is None:
            self.gesture_history.clear()
            self.stable_gesture = None
            self.keyboard_mode_start = None
            self._prev_scroll_y = None
            return GestureState(GestureType.IDLE, 0.0)

        current = self._recognize_single_hand(landmarks)
        self.gesture_history.append(current)

        if len(self.gesture_history) < self.stability_frames:
            return None

        types = [g.gesture_type for g in self.gesture_history]
        if len(set(types)) != 1:
            return None

        stable_type = types[0]

        # Check cooldowns
        if stable_type in (GestureType.LEFT_CLICK, GestureType.RIGHT_CLICK,
                           GestureType.DOUBLE_CLICK):
            if current_time - self.last_click_time < self.cooldown_click_ms / 1000.0:
                return None

        if stable_type == GestureType.SCROLL:
            if current_time - self.last_scroll_time < self.cooldown_scroll_ms / 1000.0:
                return None

        self.stable_gesture = current

        if stable_type in (GestureType.LEFT_CLICK, GestureType.RIGHT_CLICK,
                           GestureType.DOUBLE_CLICK):
            self.last_click_time = current_time
        elif stable_type == GestureType.SCROLL:
            self.last_scroll_time = current_time

        return self.stable_gesture

    def reset(self) -> None:
        self.gesture_history.clear()
        self.stable_gesture = None
        self.last_click_time = 0.0
        self.last_scroll_time = 0.0
        self.keyboard_mode_start = None
        self.in_keyboard_mode = False
        self._prev_palm_center = None
        self._grab_started = False
        self._grab_start_pos = None
        self._was_open_hand = False
        self._prev_two_hand_distance = None
        self._prev_scroll_y = None
