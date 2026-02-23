"""Tests for gesture recognition — all gestures with mock landmarks."""
import pytest
import time
from gesture_recognition import GestureRecognizer, GestureType


class TestSingleHandGestures:
    def test_move_gesture(self, move_hand):
        r = GestureRecognizer(stability_frames=1)
        g = r._recognize_single_hand(move_hand)
        assert g.gesture_type == GestureType.MOVE
        assert 'cursor_pos' in g.data

    def test_left_click_pinch(self, pinch_hand):
        r = GestureRecognizer(stability_frames=1)
        g = r._recognize_single_hand(pinch_hand)
        assert g.gesture_type == GestureType.LEFT_CLICK

    def test_all_fingers_starts_keyboard(self, all_fingers_hand):
        r = GestureRecognizer(stability_frames=1, keyboard_hold_time=0.01)
        # First call starts timer
        g1 = r._recognize_single_hand(all_fingers_hand)
        assert g1.gesture_type == GestureType.IDLE
        assert g1.data.get('building_keyboard')
        # After hold time
        time.sleep(0.02)
        g2 = r._recognize_single_hand(all_fingers_hand)
        assert g2.gesture_type == GestureType.KEYBOARD

    def test_fist_is_idle(self, fist_hand):
        r = GestureRecognizer(stability_frames=1)
        g = r._recognize_single_hand(fist_hand)
        # Fist without prior open hand = IDLE (no grab)
        assert g.gesture_type == GestureType.IDLE

    def test_grab_from_open_to_fist(self, all_fingers_hand, fist_hand):
        r = GestureRecognizer(stability_frames=1, keyboard_hold_time=10.0)
        # Open hand first (sets _was_open_hand)
        r._recognize_single_hand(all_fingers_hand)
        # Then fist = GRAB
        g = r._recognize_single_hand(fist_hand)
        assert g.gesture_type == GestureType.GRAB

    def test_stability_mechanism(self, move_hand):
        r = GestureRecognizer(stability_frames=2)
        r.process_landmarks(move_hand)
        result = r.process_landmarks(move_hand)
        assert result is not None
        assert result.gesture_type == GestureType.MOVE

    def test_click_cooldown(self, pinch_hand):
        r = GestureRecognizer(stability_frames=1, cooldown_click_ms=500)
        # First click
        g1 = r.process_landmarks(pinch_hand)
        assert g1 is not None
        # Immediate second should be blocked
        g2 = r.process_landmarks(pinch_hand)
        assert g2 is None

    def test_no_hand_returns_idle(self):
        r = GestureRecognizer()
        g = r.process_landmarks(None)
        assert g.gesture_type == GestureType.IDLE

    def test_reset(self, move_hand):
        r = GestureRecognizer(stability_frames=2)
        r.process_landmarks(move_hand)
        r.reset()
        assert len(r.gesture_history) == 0
        assert r.stable_gesture is None


class TestTwoHandGestures:
    def test_no_two_hand_with_one(self, move_hand):
        from hand_tracker import HandTrackingResult
        r = GestureRecognizer()
        result = HandTrackingResult()
        result.hands.append(move_hand)
        assert r.process_two_hands(result) is None

    def test_two_hand_resize(self):
        """Two hands both pinching should trigger resize."""
        from tests.conftest import MockHandLandmarks, MockLandmark
        from hand_tracker import HandTrackingResult

        def make_pinching_hand(cx, handedness):
            lm = [MockLandmark(cx, 0.5)] * 21
            lm[0] = MockLandmark(cx, 0.7)
            lm[3] = MockLandmark(cx - 0.02, 0.4)
            lm[4] = MockLandmark(cx - 0.005, 0.39)  # thumb tip very close to index
            lm[5] = MockLandmark(cx + 0.05, 0.6)
            lm[6] = MockLandmark(cx + 0.05, 0.5)
            lm[8] = MockLandmark(cx - 0.01, 0.39)  # index tip near thumb
            lm[9] = MockLandmark(cx, 0.6)
            lm[10] = MockLandmark(cx, 0.5)
            lm[12] = MockLandmark(cx, 0.6)
            lm[13] = MockLandmark(cx - 0.05, 0.6)
            lm[14] = MockLandmark(cx - 0.05, 0.5)
            lm[16] = MockLandmark(cx - 0.05, 0.6)
            lm[17] = MockLandmark(cx - 0.1, 0.6)
            lm[18] = MockLandmark(cx - 0.1, 0.5)
            lm[20] = MockLandmark(cx - 0.1, 0.6)
            return MockHandLandmarks(lm, handedness)

        r = GestureRecognizer()
        result = HandTrackingResult()
        result.hands.append(make_pinching_hand(0.3, "Left"))
        result.hands.append(make_pinching_hand(0.7, "Right"))

        g = r.process_two_hands(result)
        assert g is not None
        assert g.gesture_type == GestureType.TWO_HAND_RESIZE
