"""
HandControl Main Application Loop
Integrates camera, hand tracking, gesture recognition, and cursor control
"""
import time
import sys
import platform
from typing import Optional, Dict, Any
import pyautogui

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: OpenCV not available. Preview functionality will be limited.")

# Import HandControl modules
from config import Config
from camera import Camera
from hand_tracker import HandTracker
from gesture_recognition import GestureRecognizer, GestureType
from cursor_control import CursorController
from keyboard_mode import KeyboardMode, KeyboardModeVisualizer

class HandControlApp:
    """
    Main HandControl application
    Handles the complete pipeline: Camera → landmarks → gesture → cursor action
    """
    
    def __init__(self, config_path: Optional[str] = None, preview: bool = True):
        """
        Initialize HandControl application
        
        Args:
            config_path: Path to config file (uses default if None)
            preview: Show preview window
        """
        # Load configuration
        self.config = Config(config_path) if config_path else Config()
        self.show_preview = preview and self.config.get('display.show_preview', True)
        
        # Initialize components
        print("Initializing HandControl...")
        
        # Initialize camera with config parameters
        camera_config = self.config.get('camera', {})
        self.camera = Camera(
            camera_index=camera_config.get('index', 0),
            width=camera_config.get('width', 640),
            height=camera_config.get('height', 480),
            fps_target=camera_config.get('fps_target', 30),
            mirror=camera_config.get('mirror', True)
        )
        
        self.tracker = HandTracker(self.config) 
        self.gesture_recognizer = GestureRecognizer(**self._get_gesture_config())
        self.cursor_controller = CursorController(self.config)
        
        # Initialize enhanced keyboard mode
        keyboard_hold_time = self.config.get('gestures.keyboard_hold_time', 1.0)
        self.keyboard_mode = KeyboardMode(hold_time=keyboard_hold_time, feedback_callback=self._keyboard_feedback)
        self.keyboard_visualizer = KeyboardModeVisualizer()
        
        # Open camera connection
        if not self.camera.open():
            raise RuntimeError("Failed to open camera")
        
        # Ensure pyautogui FAILSAFE is always enabled
        pyautogui.FAILSAFE = True
        
        # Application state
        self.is_paused = False
        self.is_running = False
        
        # Gesture cooldowns (in seconds) 
        self.last_click_time = 0.0
        self.last_scroll_time = 0.0
        self.click_cooldown = self.config.get('gestures.cooldown_click_ms', 300) / 1000.0
        self.scroll_cooldown = self.config.get('gestures.cooldown_scroll_ms', 50) / 1000.0
        
        # Keyboard mode feedback state
        self.keyboard_feedback_message = ""
        
        # Platform detection for keyboard shortcuts
        self.is_macos = platform.system() == 'Darwin'
        
        print("🎮 HandControl initialized!")
        print("Controls:")
        print("  p = pause/resume")
        print("  q = quit") 
        print("  r = reset smoothing")
        print("") 
        print("Gestures:")
        print("  👆 MOVE → cursor follows index finger")
        print("  🤏 LEFT_CLICK → pinch index+middle")
        print("  🫴 RIGHT_CLICK → 3 finger pinch")
        print("  👌 DOUBLE_CLICK → thumb-index pinch")  
        print("  ✌️ SCROLL → 2 fingers spread, Y movement")
        print("  ✊👍 DRAG → fist+thumb → toggle drag")
        print("  🖐️ KEYBOARD → all 5 fingers held 1 second")
        print("")
    
    def _get_gesture_config(self) -> Dict[str, Any]:
        """Get gesture recognition configuration"""
        gestures = self.config.get('gestures', {})
        return {
            'finger_threshold': gestures.get('finger_threshold', 0.15),
            'pinch_threshold': gestures.get('pinch_threshold', 0.08),
            'stability_frames': gestures.get('stability_frames', 3),
            'cooldown_click_ms': gestures.get('cooldown_click_ms', 300),
            'cooldown_scroll_ms': gestures.get('cooldown_scroll_ms', 50),
            'keyboard_hold_time': gestures.get('keyboard_hold_time', 1.0)
        }
    
    def _keyboard_feedback(self, event: str, data: Dict[str, Any]) -> None:
        """
        Handle keyboard mode feedback
        
        Args:
            event: Feedback event type
            data: Event data
        """
        if event == "keyboard_activating":
            remaining = data.get('remaining', 0)
            self.keyboard_feedback_message = f"KEYBOARD {remaining:.1f}s"
        elif event == "keyboard_active":
            self.keyboard_feedback_message = "KEYBOARD MODE"
        elif event == "keyboard_inactive":
            self.keyboard_feedback_message = ""
        elif event == "shortcut_executed":
            shortcut = data.get('shortcut', '')
            self.keyboard_feedback_message = f"EXECUTED: {shortcut.upper()}"
    
    def _can_click(self) -> bool:
        """Check if enough time has passed since last click"""
        return time.time() - self.last_click_time > self.click_cooldown
    
    def _can_scroll(self) -> bool:
        """Check if enough time has passed since last scroll"""
        return time.time() - self.last_scroll_time > self.scroll_cooldown
    
    def _handle_gesture(self, gesture_type: GestureType, gesture_data: Dict[str, Any], landmarks) -> None:
        """
        Handle detected gesture
        
        Args:
            gesture_type: Detected gesture
            gesture_data: Additional gesture data
            landmarks: Hand landmarks for position data
        """
        current_time = time.time()
        
        if gesture_type == GestureType.MOVE:
            # Move cursor to index finger position
            if landmarks:
                index_tip = landmarks.get_landmark(8)  # INDEX_FINGER_TIP
                if index_tip:
                    # Convert normalized coordinates to pixel coordinates
                    frame_height, frame_width = frame.shape[:2]
                    
                    finger_x = index_tip[0] * frame_width
                    finger_y = index_tip[1] * frame_height
                    
                    self.cursor_controller.move_cursor(finger_x, finger_y, frame_width, frame_height)
        
        elif gesture_type == GestureType.LEFT_CLICK:
            if self._can_click():
                print("👆 Left Click")
                self.cursor_controller.left_click()
                self.last_click_time = current_time
        
        elif gesture_type == GestureType.RIGHT_CLICK:
            if self._can_click():
                print("🫴 Right Click")
                self.cursor_controller.right_click()
                self.last_click_time = current_time
        
        elif gesture_type == GestureType.DOUBLE_CLICK:
            if self._can_click():
                print("👌 Double Click")
                self.cursor_controller.double_click()
                self.last_click_time = current_time
        
        elif gesture_type == GestureType.SCROLL:
            if self._can_scroll():
                # Get scroll direction from gesture data
                scroll_delta = gesture_data.get('scroll_delta', 0)
                if abs(scroll_delta) > 5:  # Minimum movement threshold
                    direction = 1 if scroll_delta > 0 else -1
                    print(f"✌️ Scroll {'Up' if direction > 0 else 'Down'}")
                    self.cursor_controller.scroll(direction)
                    self.last_scroll_time = current_time
        
        elif gesture_type == GestureType.DRAG:
            print("✊👍 Toggle Drag")
            self.cursor_controller.toggle_drag()
        
        elif gesture_type == GestureType.KEYBOARD:
            # Use enhanced keyboard mode
            all_fingers_extended = gesture_data.get('finger_count', 0) == 5
            shortcut = self.keyboard_mode.update(all_fingers_extended, gesture_data)
            
            if shortcut:
                self.keyboard_mode.execute_shortcut(shortcut)
        
        else:  # IDLE or other
            # Update keyboard mode with current finger state
            if gesture_type == GestureType.IDLE:
                # Reset keyboard mode if idle
                self.keyboard_mode.update(False, {})
    
    def _legacy_keyboard_mode_removed(self) -> None:
        """Legacy method - replaced by KeyboardMode class"""
        pass
    
    def _draw_status(self, frame, gesture_type: GestureType) -> None:
        """
        Draw status information on frame
        
        Args:
            frame: OpenCV frame
            gesture_type: Current gesture
        """
        if not CV2_AVAILABLE:
            return
            
        h, w = frame.shape[:2]
        
        # Status text
        status_text = f"{'PAUSED' if self.is_paused else 'ACTIVE'} | {gesture_type.value.upper()}"
        if self.keyboard_feedback_message:
            status_text += f" | {self.keyboard_feedback_message}"
        
        # Draw background rectangle
        text_size = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        cv2.rectangle(frame, (10, 10), (text_size[0] + 20, 50), (0, 0, 0), -1)
        
        # Draw text
        color = (0, 255, 0) if not self.is_paused else (0, 255, 255)
        cv2.putText(frame, status_text, (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Draw controls
        controls = "p=pause | q=quit | r=reset"
        cv2.putText(frame, controls, (15, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def run(self) -> None:
        """Run the main application loop"""
        print("🚀 Starting HandControl...")
        self.is_running = True
        
        try:
            while self.is_running:
                # Capture frame
                success, frame = self.camera.read()
                if not success or frame is None:
                    print("❌ Failed to get camera frame")
                    break
                
                current_gesture = GestureType.IDLE
                gesture_data = {}
                
                if not self.is_paused:
                    # Track hand
                    landmarks = self.tracker.track(frame)
                    
                    if landmarks:
                        # Recognize gesture
                        gesture_state = self.gesture_recognizer.recognize(landmarks)
                        
                        if gesture_state:
                            current_gesture = gesture_state.gesture_type
                            gesture_data = gesture_state.data
                            
                            # Handle the gesture
                            self._handle_gesture(current_gesture, gesture_data, landmarks)
                        
                        # Draw landmarks on preview
                        if self.show_preview:
                            self.tracker.draw_landmarks(frame, landmarks)
                
                # Show preview window
                if self.show_preview and CV2_AVAILABLE:
                    self._draw_status(frame, current_gesture)
                    
                    # Draw keyboard mode visual feedback
                    keyboard_status = self.keyboard_mode.get_status()
                    self.keyboard_visualizer.draw_keyboard_status(frame, keyboard_status)
                    
                    if keyboard_status['is_active'] or keyboard_status['is_activating']:
                        self.keyboard_visualizer.draw_shortcut_reference(frame)
                    
                    cv2.imshow('HandControl', frame)
                    
                    # Handle keyboard input
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        print("👋 Quitting...")
                        break
                    elif key == ord('p'):
                        self.is_paused = not self.is_paused
                        print(f"⏸️ {'Paused' if self.is_paused else 'Resumed'}")
                    elif key == ord('r'):
                        self.cursor_controller.reset_smoothing()
                        print("🔄 Smoothing reset")
                else:
                    # Small delay to prevent excessive CPU usage in headless mode
                    time.sleep(0.001)
        
        except KeyboardInterrupt:
            print("\n👋 Interrupted by user")
        
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.cleanup()
    
    def cleanup(self) -> None:
        """Clean up resources"""
        print("🧹 Cleaning up...")
        
        # Stop any ongoing drag
        if hasattr(self.cursor_controller, 'is_dragging') and self.cursor_controller.is_dragging:
            self.cursor_controller.stop_drag()
        
        # Release camera
        self.camera.close()
        
        # Close windows
        if self.show_preview and CV2_AVAILABLE:
            cv2.destroyAllWindows()
        
        print("✅ Cleanup complete")


def main():
    """Entry point for HandControl application"""
    import argparse
    
    parser = argparse.ArgumentParser(description='HandControl - Gesture-based cursor control')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--no-preview', action='store_true', help='Run without preview window')
    
    args = parser.parse_args()
    
    # Create and run application
    app = HandControlApp(
        config_path=args.config,
        preview=not args.no_preview
    )
    
    app.run()


if __name__ == "__main__":
    main()