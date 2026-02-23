"""
HandControl / Minority Report — Main Application
Threaded pipeline: Camera → MediaPipe → Gestures → Actions
"""
import time
import sys
import platform
import threading
from typing import Optional, Dict, Any
import pyautogui

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from config import Config
from camera import Camera
from hand_tracker import HandTracker, HandTrackingResult
from gesture_recognition import GestureRecognizer, GestureType, GestureState
from cursor_control import CursorController
from calibration import ScreenCalibrator
from keyboard_mode import KeyboardMode, KeyboardModeVisualizer


class HandControlApp:
    """Main application — threaded camera + processing pipeline."""

    def __init__(self, config_path: Optional[str] = None, preview: bool = True):
        self.config = Config(config_path) if config_path else Config()
        self.show_preview = preview and self.config.get('display.show_preview', True)

        # Camera (threaded)
        cam_cfg = self.config.get('camera', {})
        self.camera = Camera(
            camera_index=cam_cfg.get('index', 0),
            width=cam_cfg.get('width', 640),
            height=cam_cfg.get('height', 480),
            fps_target=cam_cfg.get('fps_target', 30),
            mirror=cam_cfg.get('mirror', True),
            use_threading=True,
        )

        # Hand tracker
        mp_cfg = self.config.get('mediapipe', {})
        self.tracker = HandTracker(
            max_num_hands=mp_cfg.get('max_num_hands', 2),
            min_detection_confidence=mp_cfg.get('min_detection_confidence', 0.8),
            min_tracking_confidence=mp_cfg.get('min_tracking_confidence', 0.7),
            model_complexity=mp_cfg.get('model_complexity', 1),
        )

        # Calibrator
        self.calibrator = ScreenCalibrator(*pyautogui.size())
        cal_path = self.config.get('calibration.save_path', '~/.minority_report/calibration.json')
        self.calibrator.load_calibration(cal_path)

        # Gesture recognizer
        g_cfg = self.config.get('gestures', {})
        dominant = self.config.get('app.dominant_hand', 'right').capitalize()
        self.gesture_recognizer = GestureRecognizer(
            finger_threshold=g_cfg.get('finger_threshold', 0.15),
            pinch_threshold=g_cfg.get('pinch_threshold', 0.08),
            grab_threshold=g_cfg.get('grab_threshold', 0.12),
            stability_frames=g_cfg.get('stability_frames', 2),
            cooldown_click_ms=g_cfg.get('cooldown_click_ms', 300),
            cooldown_scroll_ms=g_cfg.get('cooldown_scroll_ms', 50),
            keyboard_hold_time=g_cfg.get('keyboard_hold_time', 1.0),
            grab_velocity_threshold=g_cfg.get('grab_velocity_threshold', 0.15),
            dominant_hand=dominant,
        )

        # Cursor controller
        self.cursor_controller = CursorController(self.config, self.calibrator)

        # Keyboard mode
        self.keyboard_mode = KeyboardMode(
            hold_time=g_cfg.get('keyboard_hold_time', 1.0),
            feedback_callback=self._keyboard_feedback,
        )
        self.keyboard_visualizer = KeyboardModeVisualizer()

        # Open camera
        if not self.camera.open():
            raise RuntimeError("Failed to open camera")

        pyautogui.FAILSAFE = True

        # State
        self.is_paused = False
        self.is_running = False
        self.last_click_time = 0.0
        self.last_scroll_time = 0.0
        self.click_cooldown = g_cfg.get('cooldown_click_ms', 300) / 1000.0
        self.scroll_cooldown = g_cfg.get('cooldown_scroll_ms', 50) / 1000.0
        self.keyboard_feedback_message = ""
        self.is_macos = platform.system() == 'Darwin'

        # FPS tracking
        self._frame_count = 0
        self._fps_time = time.time()
        self._current_fps = 0.0

    def _keyboard_feedback(self, event: str, data: Dict[str, Any]) -> None:
        if event == "keyboard_activating":
            self.keyboard_feedback_message = f"KEYBOARD {data.get('remaining', 0):.1f}s"
        elif event == "keyboard_active":
            self.keyboard_feedback_message = "KEYBOARD MODE"
        elif event == "keyboard_inactive":
            self.keyboard_feedback_message = ""
        elif event == "shortcut_executed":
            self.keyboard_feedback_message = f"EXECUTED: {data.get('shortcut', '').upper()}"

    def _can_click(self) -> bool:
        return time.time() - self.last_click_time > self.click_cooldown

    def _can_scroll(self) -> bool:
        return time.time() - self.last_scroll_time > self.scroll_cooldown

    def _handle_gesture(self, gesture: GestureState, tracking_result: HandTrackingResult) -> None:
        gt = gesture.gesture_type
        data = gesture.data
        now = time.time()

        if gt == GestureType.MOVE:
            pos = data.get('cursor_pos')
            if pos:
                self.cursor_controller.move_cursor(pos[0], pos[1])

        elif gt == GestureType.LEFT_CLICK:
            if self._can_click():
                self.cursor_controller.left_click()
                self.last_click_time = now

        elif gt == GestureType.RIGHT_CLICK:
            if self._can_click():
                self.cursor_controller.right_click()
                self.last_click_time = now

        elif gt == GestureType.DOUBLE_CLICK:
            if self._can_click():
                self.cursor_controller.double_click()
                self.last_click_time = now

        elif gt == GestureType.SCROLL:
            if self._can_scroll():
                delta = data.get('scroll_delta', 0)
                if abs(delta) > 2:
                    direction = 1 if delta > 0 else -1
                    self.cursor_controller.scroll(direction)
                    self.last_scroll_time = now

        elif gt == GestureType.DRAG:
            self.cursor_controller.toggle_drag()

        elif gt == GestureType.KEYBOARD:
            shortcut = self.keyboard_mode.update(True, data)
            if shortcut:
                self.keyboard_mode.execute_shortcut(shortcut)

        elif gt == GestureType.GRAB:
            pass  # Visual feedback only

        elif gt == GestureType.WINDOW_MOVE:
            pass  # Would use pyobjc for actual window management

        elif gt == GestureType.WINDOW_MINIMIZE:
            if self.is_macos:
                pyautogui.hotkey('cmd', 'm')

        elif gt == GestureType.WINDOW_MAXIMIZE:
            if self.is_macos:
                # macOS doesn't have a standard maximize shortcut
                # Use green button via accessibility (placeholder)
                pass

        elif gt == GestureType.TWO_HAND_RESIZE:
            pass  # Needs pyobjc window management

        elif gt == GestureType.IDLE:
            self.keyboard_mode.update(False, {})

    def _update_fps(self) -> None:
        self._frame_count += 1
        elapsed = time.time() - self._fps_time
        if elapsed >= 1.0:
            self._current_fps = self._frame_count / elapsed
            self._frame_count = 0
            self._fps_time = time.time()

    def _draw_status(self, frame, gesture_type: GestureType) -> None:
        if not CV2_AVAILABLE:
            return
        h, w = frame.shape[:2]

        # Status bar
        status = f"{'PAUSED' if self.is_paused else gesture_type.value.upper()}"
        fps_text = f"FPS: {self._current_fps:.0f}"

        cv2.rectangle(frame, (0, 0), (w, 35), (20, 20, 20), -1)
        color = (0, 255, 0) if not self.is_paused else (0, 200, 255)
        cv2.putText(frame, status, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        cv2.putText(frame, fps_text, (w - 100, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        if self.keyboard_feedback_message:
            cv2.putText(frame, self.keyboard_feedback_message, (w // 2 - 80, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

    def run(self) -> None:
        self.is_running = True
        dominant = self.config.get('app.dominant_hand', 'right').capitalize()

        try:
            while self.is_running:
                success, frame = self.camera.read()
                if not success or frame is None:
                    time.sleep(0.001)
                    continue

                self._update_fps()
                current_gesture_type = GestureType.IDLE

                if not self.is_paused:
                    # Process hands
                    result = self.tracker.process_frame(frame)

                    # Check two-hand gestures first
                    two_hand = self.gesture_recognizer.process_two_hands(result, dominant)
                    if two_hand:
                        current_gesture_type = two_hand.gesture_type
                        self._handle_gesture(two_hand, result)
                    else:
                        # Single dominant hand
                        dom_hand = result.get_hand(dominant) or result.dominant
                        gesture = self.gesture_recognizer.process_landmarks(dom_hand)
                        if gesture:
                            current_gesture_type = gesture.gesture_type
                            self._handle_gesture(gesture, result)

                    # Draw landmarks
                    if self.show_preview:
                        for hand in result.hands:
                            color = (0, 255, 0) if hand.handedness == dominant else (255, 165, 0)
                            self.tracker.draw_landmarks(frame, hand, color)

                # Preview
                if self.show_preview and CV2_AVAILABLE:
                    self._draw_status(frame, current_gesture_type)

                    kb_status = self.keyboard_mode.get_status()
                    self.keyboard_visualizer.draw_keyboard_status(frame, kb_status)
                    if kb_status['is_active'] or kb_status.get('is_activating'):
                        self.keyboard_visualizer.draw_shortcut_reference(frame)

                    cv2.imshow('Minority Report', frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break
                    elif key == ord('p'):
                        self.is_paused = not self.is_paused
                    elif key == ord('r'):
                        self.cursor_controller.reset_smoothing()
                    elif key == ord('c'):
                        # Recalibrate
                        pass
                else:
                    time.sleep(0.001)

        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()

    def cleanup(self) -> None:
        if hasattr(self.cursor_controller, 'is_dragging') and self.cursor_controller.is_dragging:
            self.cursor_controller.stop_drag()
        self.camera.close()
        self.tracker.close()
        if self.show_preview and CV2_AVAILABLE:
            cv2.destroyAllWindows()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Minority Report — Gesture Control')
    parser.add_argument('--config', type=str, help='Config file path')
    parser.add_argument('--no-preview', action='store_true')
    args = parser.parse_args()

    app = HandControlApp(config_path=args.config, preview=not args.no_preview)
    app.run()


if __name__ == "__main__":
    main()
