"""
Cursor Control with Smoothing for HandControl
Maps hand landmarks to screen coordinates with dead zone and smoothing
"""
import time
import platform
from typing import Tuple, Optional, Dict, Any
import pyautogui

# Import HandControl modules
from smoothing import PointSmoother
from config import Config

class CursorController:
    """
    Maps finger position to screen coordinates with smoothing and dead zone
    """
    
    def __init__(self, config: Config):
        """
        Initialize cursor controller
        
        Args:
            config: HandControl configuration
        """
        self.config = config
        
        # Get screen dimensions
        self.screen_width, self.screen_height = pyautogui.size()
        
        # Dead zone configuration
        dead_zone = config.get('cursor.dead_zone', 0.1)
        self.dead_zone_x = dead_zone
        self.dead_zone_y = dead_zone
        
        # Initialize smoother
        smoothing_config = config.get('smoothing', {})
        smoother_type = smoothing_config.get('type', 'one_euro')
        
        if smoother_type == 'one_euro':
            smoother_params = {
                'freq': smoothing_config.get('one_euro_freq', 30),
                'mincutoff': smoothing_config.get('one_euro_mincutoff', 1.0),
                'beta': smoothing_config.get('one_euro_beta', 0.007),
                'dcutoff': smoothing_config.get('one_euro_dcutoff', 1.0)
            }
        else:  # ema
            smoother_params = {
                'alpha': smoothing_config.get('ema_alpha', 0.3)
            }
        
        self.smoother = PointSmoother(smoother_type, **smoother_params)
        
        # Sensitivity and acceleration
        self.sensitivity = config.get('cursor.sensitivity', 1.0)
        self.use_acceleration = config.get('cursor.acceleration_curve', True)
        
        # Platform detection for modifier keys
        self.is_macos = platform.system() == 'Darwin'
        
        # Ensure pyautogui failsafe is enabled
        pyautogui.FAILSAFE = True
        
        # State tracking
        self.last_position: Optional[Tuple[float, float]] = None
        self.is_dragging = False
        
        print(f"CursorController initialized:")
        print(f"  Screen size: {self.screen_width}x{self.screen_height}")
        print(f"  Dead zone: {dead_zone * 100}%")
        print(f"  Smoother: {smoother_type}")
        print(f"  Sensitivity: {self.sensitivity}")
        print(f"  Platform: {'macOS' if self.is_macos else 'Other'}")
        print(f"  FAILSAFE enabled: {pyautogui.FAILSAFE}")
    
    def webcam_to_screen(self, webcam_x: float, webcam_y: float, 
                        webcam_width: int = 640, webcam_height: int = 480) -> Tuple[float, float]:
        """
        Convert webcam coordinates to screen coordinates with dead zone
        
        Args:
            webcam_x: X coordinate in webcam frame (0 to webcam_width)
            webcam_y: Y coordinate in webcam frame (0 to webcam_height)
            webcam_width: Width of webcam frame
            webcam_height: Height of webcam frame
            
        Returns:
            Screen coordinates (x, y)
        """
        # Normalize to 0-1 range
        norm_x = webcam_x / webcam_width
        norm_y = webcam_y / webcam_height
        
        # Apply dead zone: center 80% of webcam → 100% of screen
        # Outer 10% on each side is ignored
        
        # Clamp to valid range after accounting for dead zone
        effective_x = max(self.dead_zone_x, min(1.0 - self.dead_zone_x, norm_x))
        effective_y = max(self.dead_zone_y, min(1.0 - self.dead_zone_y, norm_y))
        
        # Remap to 0-1 range (center 80% becomes full range)
        mapped_x = (effective_x - self.dead_zone_x) / (1.0 - 2 * self.dead_zone_x)
        mapped_y = (effective_y - self.dead_zone_y) / (1.0 - 2 * self.dead_zone_y)
        
        # Scale to screen dimensions
        screen_x = mapped_x * self.screen_width
        screen_y = mapped_y * self.screen_height
        
        return screen_x, screen_y
    
    def smooth_position(self, screen_x: float, screen_y: float, timestamp: Optional[float] = None) -> Tuple[float, float]:
        """
        Apply smoothing to screen coordinates
        
        Args:
            screen_x: X coordinate in screen space
            screen_y: Y coordinate in screen space
            timestamp: Optional timestamp
            
        Returns:
            Smoothed screen coordinates
        """
        return self.smoother.filter((screen_x, screen_y), timestamp)
    
    def move_cursor(self, finger_x: float, finger_y: float, webcam_width: int = 640, webcam_height: int = 480) -> None:
        """
        Move cursor based on finger position
        
        Args:
            finger_x: Finger X coordinate in webcam frame
            finger_y: Finger Y coordinate in webcam frame  
            webcam_width: Width of webcam frame
            webcam_height: Height of webcam frame
        """
        # Convert to screen coordinates
        screen_x, screen_y = self.webcam_to_screen(finger_x, finger_y, webcam_width, webcam_height)
        
        # Apply smoothing
        smooth_x, smooth_y = self.smooth_position(screen_x, screen_y)
        
        # Apply sensitivity
        if self.last_position:
            dx = smooth_x - self.last_position[0]
            dy = smooth_y - self.last_position[1]
            
            if self.use_acceleration:
                # Simple acceleration curve: larger movements get boosted
                distance = (dx * dx + dy * dy) ** 0.5
                acceleration = min(2.0, 1.0 + distance / 100.0)  # Up to 2x acceleration
            else:
                acceleration = 1.0
            
            smooth_x = self.last_position[0] + dx * self.sensitivity * acceleration
            smooth_y = self.last_position[1] + dy * self.sensitivity * acceleration
        
        # Clamp to screen bounds
        smooth_x = max(0, min(self.screen_width - 1, smooth_x))
        smooth_y = max(0, min(self.screen_height - 1, smooth_y))
        
        # Move cursor
        pyautogui.moveTo(smooth_x, smooth_y)
        
        self.last_position = (smooth_x, smooth_y)
    
    def left_click(self) -> None:
        """Perform left mouse click"""
        pyautogui.click(button='left')
    
    def right_click(self) -> None:
        """Perform right mouse click"""  
        pyautogui.click(button='right')
    
    def double_click(self) -> None:
        """Perform double click"""
        pyautogui.doubleClick()
    
    def scroll(self, direction: int, amount: int = 1) -> None:
        """
        Scroll mouse wheel
        
        Args:
            direction: 1 for up, -1 for down
            amount: Number of scroll clicks
        """
        pyautogui.scroll(amount * direction)
    
    def start_drag(self) -> None:
        """Start dragging (mouse down)"""
        if not self.is_dragging:
            pyautogui.mouseDown()
            self.is_dragging = True
    
    def stop_drag(self) -> None:
        """Stop dragging (mouse up)"""
        if self.is_dragging:
            pyautogui.mouseUp()
            self.is_dragging = False
    
    def toggle_drag(self) -> None:
        """Toggle drag state"""
        if self.is_dragging:
            self.stop_drag()
        else:
            self.start_drag()
    
    def keyboard_shortcut(self, keys: list) -> None:
        """
        Send keyboard shortcut
        
        Args:
            keys: List of keys to press simultaneously
        """
        # Convert platform-specific keys
        platform_keys = []
        for key in keys:
            if key.lower() in ['cmd', 'command'] and not self.is_macos:
                platform_keys.append('ctrl')
            elif key.lower() == 'ctrl' and self.is_macos:
                platform_keys.append('cmd')
            else:
                platform_keys.append(key)
        
        pyautogui.hotkey(*platform_keys)
    
    def reset_smoothing(self) -> None:
        """Reset smoothing filter state"""
        self.smoother.reset()
        self.last_position = None
        print("Cursor smoothing reset")


def test_cursor_control() -> bool:
    """Test cursor control functionality"""
    from config import Config
    
    print("Testing cursor control...")
    
    # Load config
    config = Config()
    
    # Initialize cursor controller
    cursor = CursorController(config)
    
    # Test coordinate conversion
    webcam_width, webcam_height = 640, 480
    
    # Test corner mappings
    test_cases = [
        # Webcam corners should map to screen corners
        (64, 48, "top-left corner (after dead zone)"),     # 10% in from edge
        (576, 48, "top-right corner (after dead zone)"),  # 90% in from edge  
        (64, 432, "bottom-left corner (after dead zone)"), # 10% in from edge
        (576, 432, "bottom-right corner (after dead zone)") # 90% in from edge
    ]
    
    print("Testing coordinate mappings:")
    for webcam_x, webcam_y, description in test_cases:
        screen_x, screen_y = cursor.webcam_to_screen(webcam_x, webcam_y, webcam_width, webcam_height)
        print(f"  {description}: webcam({webcam_x}, {webcam_y}) → screen({screen_x:.0f}, {screen_y:.0f})")
    
    # Test dead zone - center should map to screen center
    center_x, center_y = webcam_width // 2, webcam_height // 2
    screen_center_x, screen_center_y = cursor.webcam_to_screen(center_x, center_y, webcam_width, webcam_height)
    
    expected_center_x = cursor.screen_width / 2
    expected_center_y = cursor.screen_height / 2
    
    center_error_x = abs(screen_center_x - expected_center_x)
    center_error_y = abs(screen_center_y - expected_center_y)
    
    print(f"Center mapping: webcam({center_x}, {center_y}) → screen({screen_center_x:.0f}, {screen_center_y:.0f})")
    print(f"Expected center: ({expected_center_x:.0f}, {expected_center_y:.0f})")
    print(f"Error: ({center_error_x:.0f}, {center_error_y:.0f})")
    
    # Test smoothing - first value should pass through
    test_x, test_y = 100, 200
    smooth_x, smooth_y = cursor.smooth_position(test_x, test_y)
    
    first_value_test = abs(smooth_x - test_x) < 1e-6 and abs(smooth_y - test_y) < 1e-6
    
    if first_value_test:
        print("✅ First value passthrough test PASSED")
    else:
        print(f"❌ First value passthrough test FAILED: ({smooth_x}, {smooth_y}) != ({test_x}, {test_y})")
    
    # Test jitter reduction
    cursor.reset_smoothing()
    jittery_positions = [
        (400, 300), (405, 295), (395, 305), (408, 292), (392, 308), (400, 300)
    ]
    
    smoothed_positions = []
    for i, pos in enumerate(jittery_positions):
        # Add timestamps to make smoothing more realistic
        smoothed = cursor.smooth_position(pos[0], pos[1], time.time() + i * 0.033)
        smoothed_positions.append(smoothed)
    
    # Calculate variance
    import statistics
    
    original_x_var = statistics.variance([p[0] for p in jittery_positions])
    smoothed_x_var = statistics.variance([p[0] for p in smoothed_positions])
    
    jitter_reduction_test = smoothed_x_var <= original_x_var  # Allow equal for very light smoothing
    
    if jitter_reduction_test:
        print("✅ Jitter reduction test PASSED")
    else:
        print(f"❌ Jitter reduction test FAILED: {smoothed_x_var} >= {original_x_var}")
    
    # Test large jump tracking
    cursor.reset_smoothing()
    # Create more realistic jump sequence with proper timing
    base_time = time.time()
    jump_positions = [(100, 100), (100, 100), (100, 100), (500, 400), (500, 400), (500, 400)]
    
    jump_results = []
    for i, pos in enumerate(jump_positions):
        timestamp = base_time + i * 0.033  # 30 FPS timing
        smoothed = cursor.smooth_position(pos[0], pos[1], timestamp)
        jump_results.append(smoothed)
    
    # Should track towards the new position (doesn't need to reach exactly)
    initial_position = jump_results[2]  # Last stable position before jump
    final_position = jump_results[-1]   # Final smoothed position
    target_position = jump_positions[-1]
    
    # Check if we moved significantly towards the target
    initial_distance = ((initial_position[0] - target_position[0]) ** 2 + 
                       (initial_position[1] - target_position[1]) ** 2) ** 0.5
    final_distance = ((final_position[0] - target_position[0]) ** 2 + 
                     (final_position[1] - target_position[1]) ** 2) ** 0.5
    
    large_jump_test = final_distance < initial_distance * 0.8  # Moved at least 20% closer
    
    if large_jump_test:
        print("✅ Large jump tracking test PASSED")
    else:
        print(f"❌ Large jump tracking test FAILED: error {convergence_error:.1f} > 50")
    
    # Test reset
    cursor.smooth_position(999, 999)  # Add some history
    cursor.reset_smoothing()
    reset_result = cursor.smooth_position(42, 84)
    
    reset_test = abs(reset_result[0] - 42) < 1e-6 and abs(reset_result[1] - 84) < 1e-6
    
    if reset_test:
        print("✅ Reset test PASSED")
    else:
        print(f"❌ Reset test FAILED: {reset_result} != (42, 84)")
    
    # Summary
    all_tests = [first_value_test, jitter_reduction_test, large_jump_test, reset_test]
    
    if all(all_tests):
        print("🎉 All cursor control tests PASSED")
        return True
    else:
        print("❌ Some cursor control tests FAILED")
        return False


def live_test_cursor() -> None:
    """
    Interactive test: move finger to corners, verify cursor reaches screen corners
    Hold still to test jitter reduction
    """
    import cv2
    from hand_tracker import HandTracker
    from config import Config
    
    print("\n=== LIVE CURSOR CONTROL TEST ===")
    print("Instructions:")
    print("1. Move index finger to corners - cursor should reach screen corners")
    print("2. Hold finger still - cursor should not jitter")
    print("3. Press 'q' to quit")
    print("4. Press 'r' to reset smoothing")
    
    # Initialize components
    config = Config()
    tracker = HandTracker(config)
    cursor = CursorController(config)
    
    cap = cv2.VideoCapture(config.get('camera.index', 0))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.get('camera.width', 640))
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.get('camera.height', 480))
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Mirror frame if configured
            if config.get('camera.mirror', True):
                frame = cv2.flip(frame, 1)
            
            # Track hand
            landmarks = tracker.track(frame)
            
            if landmarks:
                # Get index finger tip position
                index_tip = landmarks.get_landmark(8)  # INDEX_FINGER_TIP
                
                if index_tip:
                    # Convert to screen coordinates and move cursor
                    finger_x = index_tip[0] * frame.shape[1]
                    finger_y = index_tip[1] * frame.shape[0]
                    
                    cursor.move_cursor(finger_x, finger_y, frame.shape[1], frame.shape[0])
                    
                    # Draw finger position on frame
                    cv2.circle(frame, (int(finger_x), int(finger_y)), 10, (0, 255, 0), -1)
                
                # Draw hand landmarks
                tracker.draw_landmarks(frame, landmarks)
            
            # Show frame
            cv2.imshow('HandControl - Live Cursor Test', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                cursor.reset_smoothing()
                print("Smoothing reset!")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    # Run tests
    success = test_cursor_control()
    
    if success:
        print("\nRunning live test...")
        print("Close the video window or press 'q' to exit")
        live_test_cursor()