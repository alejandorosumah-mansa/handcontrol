"""
Gesture Recognition Engine for HandControl
Implements EXACT gesture specifications with relative thresholds
"""
import time
import math
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
from collections import deque

try:
    from hand_tracker import HandLandmarks
    HAND_TRACKER_AVAILABLE = True
except ImportError:
    HAND_TRACKER_AVAILABLE = False

class GestureType(Enum):
    """Enumeration of all supported gestures"""
    IDLE = "idle"
    MOVE = "move"
    LEFT_CLICK = "left_click"
    RIGHT_CLICK = "right_click"
    DOUBLE_CLICK = "double_click"
    SCROLL = "scroll"
    DRAG = "drag"
    KEYBOARD = "keyboard"

class GestureState:
    """Represents current gesture state with timing and stability"""
    
    def __init__(self, 
                 gesture_type: GestureType,
                 confidence: float = 1.0,
                 data: Optional[Dict[str, Any]] = None):
        """
        Initialize gesture state
        
        Args:
            gesture_type: The detected gesture
            confidence: Confidence level (0.0 - 1.0)
            data: Additional gesture-specific data
        """
        self.gesture_type = gesture_type
        self.confidence = confidence
        self.data = data or {}
        self.timestamp = time.time()

class GestureRecognizer:
    """
    Hand gesture recognition with stability and cooldown management
    Implements EXACT gesture specifications with relative thresholds
    """
    
    def __init__(self,
                 finger_threshold: float = 0.15,      # Relative to hand_size
                 pinch_threshold: float = 0.08,       # Relative to hand_size  
                 stability_frames: int = 3,           # Consecutive frames before trigger
                 cooldown_click_ms: int = 300,        # Click cooldown
                 cooldown_scroll_ms: int = 50,        # Scroll cooldown
                 keyboard_hold_time: float = 1.0):    # Seconds for keyboard mode
        """
        Initialize gesture recognizer
        
        Args:
            finger_threshold: Threshold for finger extension (relative to hand_size)
            pinch_threshold: Threshold for pinch detection (relative to hand_size)
            stability_frames: Frames required before triggering gesture
            cooldown_click_ms: Cooldown between clicks (ms)
            cooldown_scroll_ms: Cooldown between scrolls (ms)
            keyboard_hold_time: Time to hold all fingers for keyboard mode (seconds)
        """
        self.finger_threshold = finger_threshold
        self.pinch_threshold = pinch_threshold
        self.stability_frames = stability_frames
        self.cooldown_click_ms = cooldown_click_ms
        self.cooldown_scroll_ms = cooldown_scroll_ms
        self.keyboard_hold_time = keyboard_hold_time
        
        # Gesture stability tracking
        self.gesture_history: deque = deque(maxlen=stability_frames)
        self.stable_gesture: Optional[GestureState] = None
        
        # Cooldown tracking
        self.last_click_time = 0.0
        self.last_scroll_time = 0.0
        
        # Keyboard mode tracking
        self.keyboard_mode_start: Optional[float] = None
        self.in_keyboard_mode = False
        
        print(f"GestureRecognizer initialized:")
        print(f"  Finger threshold: {finger_threshold} (relative)")
        print(f"  Pinch threshold: {pinch_threshold} (relative)")  
        print(f"  Stability frames: {stability_frames}")
        print(f"  Click cooldown: {cooldown_click_ms}ms")
        print(f"  Scroll cooldown: {cooldown_scroll_ms}ms")
    
    def _euclidean_distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two points"""
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        return math.sqrt(dx * dx + dy * dy)
    
    def _finger_is_extended(self, 
                           landmarks: HandLandmarks, 
                           finger_tips: List[int],
                           finger_pips: List[int],
                           hand_size: float,
                           debug: bool = False) -> List[bool]:
        """
        Check which fingers are extended
        
        Args:
            landmarks: Hand landmarks
            finger_tips: List of tip landmark indices
            finger_pips: List of PIP joint landmark indices  
            hand_size: Hand size for relative thresholding
            debug: Whether to print debug information
            
        Returns:
            List of boolean values indicating if each finger is extended
        """
        extended = []
        threshold = self.finger_threshold * hand_size
        
        if debug:
            print(f"  Hand size: {hand_size:.3f}, Threshold: {threshold:.3f}")
        
        finger_names = ['thumb', 'index', 'middle', 'ring', 'pinky']
        
        for i, (tip_idx, pip_idx) in enumerate(zip(finger_tips, finger_pips)):
            tip = landmarks[tip_idx]
            pip = landmarks[pip_idx]
            
            # For fingers (not thumb), check Y distance (tip should be above PIP)
            if tip_idx != 4:  # Not THUMB_TIP (index 4)
                distance = pip.y - tip.y  # Positive if tip is above PIP
                is_extended = distance > threshold
            else:
                # For thumb, use X distance (thumb extends horizontally)
                distance = abs(tip.x - pip.x)
                is_extended = distance > threshold
            
            if debug:
                print(f"    {finger_names[i]}: tip=({tip.x:.3f},{tip.y:.3f}), pip=({pip.x:.3f},{pip.y:.3f}), dist={distance:.3f}, extended={is_extended}")
            
            extended.append(is_extended)
        
        return extended
    
    def _detect_pinch(self, 
                     landmarks: HandLandmarks,
                     point1_idx: int, 
                     point2_idx: int,
                     hand_size: float) -> bool:
        """
        Detect if two points are pinched together
        
        Args:
            landmarks: Hand landmarks
            point1_idx: First point landmark index
            point2_idx: Second point landmark index
            hand_size: Hand size for relative thresholding
            
        Returns:
            True if points are pinched together
        """
        p1 = landmarks[point1_idx]
        p2 = landmarks[point2_idx]
        
        distance = self._euclidean_distance((p1.x, p1.y), (p2.x, p2.y))
        threshold = self.pinch_threshold * hand_size
        
        return distance < threshold
    
    def _recognize_gesture(self, landmarks: HandLandmarks) -> GestureState:
        """
        Recognize gesture from hand landmarks
        
        Args:
            landmarks: Hand landmarks to analyze
            
        Returns:
            GestureState with detected gesture
        """
        # Calculate hand size for relative thresholds
        hand_size = landmarks.get_hand_size()
        
        # Define finger indices (using raw numbers for compatibility with mock)
        finger_tips = [4, 8, 12, 16, 20]    # THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP
        finger_pips = [3, 6, 10, 14, 18]    # THUMB_IP, INDEX_PIP, MIDDLE_PIP, RING_PIP, PINKY_PIP
        
        # Check which fingers are extended
        fingers_extended = self._finger_is_extended(landmarks, finger_tips, finger_pips, hand_size)
        thumb_ext, index_ext, middle_ext, ring_ext, pinky_ext = fingers_extended
        
        # Count extended fingers
        extended_count = sum(fingers_extended)
        
        # GESTURE RECOGNITION (EXACT SPEC):
        
        # KEYBOARD: All 5 fingers open, held still for 1 second
        if all(fingers_extended):
            if self.keyboard_mode_start is None:
                self.keyboard_mode_start = time.time()
            elif time.time() - self.keyboard_mode_start >= self.keyboard_hold_time:
                return GestureState(GestureType.KEYBOARD, 1.0, {'hand_size': hand_size})
            # Still building up to keyboard mode
            return GestureState(GestureType.IDLE, 0.5, {'building_keyboard': True})
        else:
            self.keyboard_mode_start = None
        
        # MOVE: Only index finger extended (others curled)
        if index_ext and not middle_ext and not ring_ext and not pinky_ext and not thumb_ext:
            index_pos = landmarks[8]  # INDEX_TIP
            return GestureState(GestureType.MOVE, 1.0, {
                'cursor_pos': (index_pos.x, index_pos.y),
                'hand_size': hand_size
            })
        
        # LEFT_CLICK: Index + middle extended, then pinch together
        if index_ext and middle_ext and not ring_ext and not pinky_ext:
            is_pinched = self._detect_pinch(landmarks, 8, 12, hand_size)  # INDEX_TIP, MIDDLE_TIP
            if is_pinched:
                return GestureState(GestureType.LEFT_CLICK, 1.0, {'hand_size': hand_size})
        
        # RIGHT_CLICK: Index + middle + ring extended, then pinch index + middle
        if index_ext and middle_ext and ring_ext and not pinky_ext:
            is_pinched = self._detect_pinch(landmarks, 8, 12, hand_size)  # INDEX_TIP, MIDDLE_TIP
            if is_pinched:
                return GestureState(GestureType.RIGHT_CLICK, 1.0, {'hand_size': hand_size})
        
        # DOUBLE_CLICK: Thumb tip touches index tip (pinch)
        if self._detect_pinch(landmarks, 4, 8, hand_size):  # THUMB_TIP, INDEX_TIP
            return GestureState(GestureType.DOUBLE_CLICK, 1.0, {'hand_size': hand_size})
        
        # SCROLL: Index + middle extended and spread apart, Y-axis movement
        if index_ext and middle_ext and not ring_ext and not pinky_ext:
            # Check if fingers are spread apart (not pinched)
            is_spread = not self._detect_pinch(landmarks, 8, 12, hand_size)  # INDEX_TIP, MIDDLE_TIP
            if is_spread:
                # Use middle of the two fingers for scroll reference
                index_pos = landmarks[8]   # INDEX_TIP
                middle_pos = landmarks[12]  # MIDDLE_TIP
                scroll_center_y = (index_pos.y + middle_pos.y) / 2
                
                return GestureState(GestureType.SCROLL, 1.0, {
                    'scroll_y': scroll_center_y,
                    'hand_size': hand_size
                })
        
        # DRAG: Fist with only thumb out
        if thumb_ext and not index_ext and not middle_ext and not ring_ext and not pinky_ext:
            return GestureState(GestureType.DRAG, 1.0, {'hand_size': hand_size})
        
        # Default: IDLE (no recognized gesture)
        return GestureState(GestureType.IDLE, 0.0, {'extended_fingers': extended_count})
    
    def process_landmarks(self, landmarks: Optional[HandLandmarks]) -> Optional[GestureState]:
        """
        Process hand landmarks and return stable gesture
        
        Args:
            landmarks: Hand landmarks to process (None if no hand detected)
            
        Returns:
            Stable gesture state if available, None otherwise
        """
        current_time = time.time()
        
        # No hand detected
        if landmarks is None:
            self.gesture_history.clear()
            self.stable_gesture = None
            self.keyboard_mode_start = None
            return GestureState(GestureType.IDLE, 0.0)
        
        # Recognize current gesture
        current_gesture = self._recognize_gesture(landmarks)
        
        # Add to history
        self.gesture_history.append(current_gesture)
        
        # Check if we have enough frames for stability
        if len(self.gesture_history) < self.stability_frames:
            return None  # Not enough history yet
        
        # Check if all recent gestures are the same type
        recent_gestures = list(self.gesture_history)
        gesture_types = [g.gesture_type for g in recent_gestures]
        
        if len(set(gesture_types)) == 1:  # All the same
            stable_type = gesture_types[0]
            
            # Check cooldowns for click gestures
            if stable_type in [GestureType.LEFT_CLICK, GestureType.RIGHT_CLICK, 
                             GestureType.DOUBLE_CLICK]:
                if current_time - self.last_click_time < (self.cooldown_click_ms / 1000.0):
                    return None  # Still in cooldown
            
            # Check cooldown for scroll
            if stable_type == GestureType.SCROLL:
                if current_time - self.last_scroll_time < (self.cooldown_scroll_ms / 1000.0):
                    return None  # Still in cooldown
            
            # Update stable gesture
            self.stable_gesture = current_gesture
            
            # Update cooldown timers
            if stable_type in [GestureType.LEFT_CLICK, GestureType.RIGHT_CLICK,
                             GestureType.DOUBLE_CLICK]:
                self.last_click_time = current_time
            elif stable_type == GestureType.SCROLL:
                self.last_scroll_time = current_time
            
            return self.stable_gesture
        
        return None  # Not stable yet
    
    def reset(self) -> None:
        """Reset gesture recognizer state"""
        self.gesture_history.clear()
        self.stable_gesture = None
        self.last_click_time = 0.0
        self.last_scroll_time = 0.0
        self.keyboard_mode_start = None
        self.in_keyboard_mode = False
        print("GestureRecognizer reset")

def test_gesture_recognition() -> bool:
    """Test gesture recognition with mock landmark data"""
    print("🖐️ Testing gesture recognition...")
    
    if not HAND_TRACKER_AVAILABLE:
        print("❌ HandTracker not available - creating mock landmarks")
    
    # Mock HandLandmark class for testing
    class MockLandmark:
        def __init__(self, x: float, y: float, z: float = 0.0):
            self.x = x
            self.y = y
            self.z = z
    
    # Mock HandLandmarks class for testing
    class MockHandLandmarks:
        def __init__(self, landmarks):
            self.landmarks = landmarks
        
        def __getitem__(self, index):
            return self.landmarks[index]
        
        def get_hand_size(self):
            # Mock hand size calculation
            wrist = self.landmarks[0]  # WRIST = 0
            middle_mcp = self.landmarks[9]  # MIDDLE_MCP = 9
            dx = middle_mcp.x - wrist.x
            dy = middle_mcp.y - wrist.y
            return math.sqrt(dx * dx + dy * dy)
    
    # Create mock landmarks for different gestures
    def create_mock_landmarks(gesture_type: str) -> MockHandLandmarks:
        """Create mock landmarks for testing specific gestures"""
        # Base landmarks (21 points) - representing a neutral hand
        landmarks = []
        
        if gesture_type == "move":
            # Only index finger extended
            # Wrist
            landmarks.append(MockLandmark(0.5, 0.7, 0))  # 0: WRIST
            
            # Thumb (curled) - tip closer to palm in X
            landmarks.extend([
                MockLandmark(0.4, 0.65, 0),   # 1: THUMB_CMC
                MockLandmark(0.35, 0.6, 0),   # 2: THUMB_MCP  
                MockLandmark(0.34, 0.58, 0),  # 3: THUMB_IP
                MockLandmark(0.35, 0.57, 0)   # 4: THUMB_TIP (curled - X distance small)
            ])
            
            # Index (extended)
            landmarks.extend([
                MockLandmark(0.55, 0.6, 0),   # 5: INDEX_MCP
                MockLandmark(0.58, 0.5, 0),   # 6: INDEX_PIP
                MockLandmark(0.6, 0.4, 0),    # 7: INDEX_DIP
                MockLandmark(0.62, 0.3, 0)    # 8: INDEX_TIP (extended up)
            ])
            
            # Middle (curled) - tip BELOW PIP (higher Y value)
            landmarks.extend([
                MockLandmark(0.5, 0.6, 0),    # 9: MIDDLE_MCP
                MockLandmark(0.51, 0.5, 0),   # 10: MIDDLE_PIP
                MockLandmark(0.52, 0.55, 0),  # 11: MIDDLE_DIP  
                MockLandmark(0.53, 0.6, 0)    # 12: MIDDLE_TIP (curled - higher Y than PIP)
            ])
            
            # Ring (curled) - tip BELOW PIP 
            landmarks.extend([
                MockLandmark(0.45, 0.6, 0),   # 13: RING_MCP
                MockLandmark(0.44, 0.5, 0),   # 14: RING_PIP
                MockLandmark(0.43, 0.55, 0),  # 15: RING_DIP
                MockLandmark(0.42, 0.6, 0)    # 16: RING_TIP (curled - higher Y than PIP)
            ])
            
            # Pinky (curled) - tip BELOW PIP
            landmarks.extend([
                MockLandmark(0.4, 0.6, 0),    # 17: PINKY_MCP
                MockLandmark(0.39, 0.5, 0),   # 18: PINKY_PIP
                MockLandmark(0.38, 0.55, 0),  # 19: PINKY_DIP
                MockLandmark(0.37, 0.6, 0)    # 20: PINKY_TIP (curled - higher Y than PIP)
            ])
            
        elif gesture_type == "left_click_pinched":
            # Index + middle extended and pinched together
            landmarks.append(MockLandmark(0.5, 0.7, 0))  # WRIST
            
            # Thumb (curled) - X distance small
            landmarks.extend([
                MockLandmark(0.4, 0.65, 0),   # THUMB_CMC
                MockLandmark(0.35, 0.6, 0),   # THUMB_MCP
                MockLandmark(0.34, 0.58, 0),  # THUMB_IP  
                MockLandmark(0.35, 0.57, 0)   # THUMB_TIP (curled)
            ])
            
            # Index (extended and pinched to middle)
            landmarks.extend([
                MockLandmark(0.55, 0.6, 0),   # INDEX_MCP
                MockLandmark(0.58, 0.5, 0),   # INDEX_PIP
                MockLandmark(0.6, 0.4, 0),    # INDEX_DIP
                MockLandmark(0.525, 0.3, 0)   # INDEX_TIP (touching middle)
            ])
            
            # Middle (extended and pinched to index)
            landmarks.extend([
                MockLandmark(0.5, 0.6, 0),    # MIDDLE_MCP
                MockLandmark(0.51, 0.5, 0),   # MIDDLE_PIP
                MockLandmark(0.52, 0.4, 0),   # MIDDLE_DIP
                MockLandmark(0.526, 0.301, 0)  # MIDDLE_TIP (touching index)
            ])
            
            # Ring (curled) - tip BELOW PIP
            landmarks.extend([
                MockLandmark(0.45, 0.6, 0),   # RING_MCP
                MockLandmark(0.44, 0.5, 0),   # RING_PIP
                MockLandmark(0.43, 0.55, 0),  # RING_DIP
                MockLandmark(0.42, 0.6, 0)    # RING_TIP (curled)
            ])
            
            # Pinky (curled) - tip BELOW PIP
            landmarks.extend([
                MockLandmark(0.4, 0.6, 0),    # PINKY_MCP
                MockLandmark(0.39, 0.5, 0),   # PINKY_PIP
                MockLandmark(0.38, 0.55, 0),  # PINKY_DIP
                MockLandmark(0.37, 0.6, 0)    # PINKY_TIP (curled)
            ])
            
        elif gesture_type == "all_fingers":
            # All fingers extended for keyboard mode
            landmarks.append(MockLandmark(0.5, 0.7, 0))  # WRIST
            
            # All fingers extended
            landmarks.extend([
                MockLandmark(0.4, 0.65, 0),   # THUMB_CMC
                MockLandmark(0.3, 0.6, 0),    # THUMB_MCP
                MockLandmark(0.25, 0.55, 0),  # THUMB_IP
                MockLandmark(0.2, 0.5, 0)     # THUMB_TIP (extended)
            ])
            
            # Index extended
            landmarks.extend([
                MockLandmark(0.55, 0.6, 0),   # INDEX_MCP
                MockLandmark(0.58, 0.5, 0),   # INDEX_PIP
                MockLandmark(0.6, 0.4, 0),    # INDEX_DIP
                MockLandmark(0.62, 0.3, 0)    # INDEX_TIP
            ])
            
            # Middle extended
            landmarks.extend([
                MockLandmark(0.5, 0.6, 0),    # MIDDLE_MCP
                MockLandmark(0.51, 0.5, 0),   # MIDDLE_PIP
                MockLandmark(0.52, 0.4, 0),   # MIDDLE_DIP
                MockLandmark(0.53, 0.3, 0)    # MIDDLE_TIP
            ])
            
            # Ring extended
            landmarks.extend([
                MockLandmark(0.45, 0.6, 0),   # RING_MCP
                MockLandmark(0.44, 0.5, 0),   # RING_PIP
                MockLandmark(0.43, 0.4, 0),   # RING_DIP
                MockLandmark(0.42, 0.3, 0)    # RING_TIP
            ])
            
            # Pinky extended  
            landmarks.extend([
                MockLandmark(0.4, 0.6, 0),    # PINKY_MCP
                MockLandmark(0.39, 0.5, 0),   # PINKY_PIP
                MockLandmark(0.38, 0.4, 0),   # PINKY_DIP
                MockLandmark(0.37, 0.3, 0)    # PINKY_TIP
            ])
        
        else:  # idle/default
            # All fingers curled
            landmarks.append(MockLandmark(0.5, 0.7, 0))
            
            for i in range(20):  # 20 remaining landmarks
                landmarks.append(MockLandmark(0.4 + i*0.01, 0.6, 0))
        
        return MockHandLandmarks(landmarks)
    
    try:
        recognizer = GestureRecognizer(
            finger_threshold=0.15,
            pinch_threshold=0.08,
            stability_frames=2,  # Reduced for testing
            cooldown_click_ms=100,  # Reduced for testing
            cooldown_scroll_ms=50
        )
        
        # Test MOVE gesture
        print("\nTesting MOVE gesture:")
        move_landmarks = create_mock_landmarks("move")
        
        # Debug finger detection
        finger_tips = [4, 8, 12, 16, 20] 
        finger_pips = [3, 6, 10, 14, 18]
        hand_size = move_landmarks.get_hand_size()
        fingers_extended = recognizer._finger_is_extended(move_landmarks, finger_tips, finger_pips, hand_size, debug=True)
        
        move_gesture = recognizer._recognize_gesture(move_landmarks)
        
        if move_gesture.gesture_type == GestureType.MOVE:
            print("✅ MOVE gesture detected correctly")
            move_test_passed = True
        else:
            print(f"❌ MOVE gesture failed: got {move_gesture.gesture_type}")
            move_test_passed = False
        
        # Test LEFT_CLICK gesture
        print("\nTesting LEFT_CLICK gesture:")
        click_landmarks = create_mock_landmarks("left_click_pinched")
        
        # Debug finger detection
        fingers_extended = recognizer._finger_is_extended(click_landmarks, finger_tips, finger_pips, click_landmarks.get_hand_size(), debug=True)
        
        # Debug pinch distance
        index_tip = click_landmarks[8]
        middle_tip = click_landmarks[12]
        pinch_distance = recognizer._euclidean_distance((index_tip.x, index_tip.y), (middle_tip.x, middle_tip.y))
        pinch_threshold = recognizer.pinch_threshold * click_landmarks.get_hand_size()
        print(f"  Pinch distance: {pinch_distance:.3f}, threshold: {pinch_threshold:.3f}, pinched: {pinch_distance < pinch_threshold}")
        
        click_gesture = recognizer._recognize_gesture(click_landmarks)
        
        if click_gesture.gesture_type == GestureType.LEFT_CLICK:
            print("✅ LEFT_CLICK gesture detected correctly")
            click_test_passed = True
        else:
            print(f"❌ LEFT_CLICK gesture failed: got {click_gesture.gesture_type}")
            click_test_passed = False
        
        # Test stability mechanism
        recognizer.reset()
        
        # Send same gesture multiple times
        for i in range(3):
            result = recognizer.process_landmarks(move_landmarks)
        
        if result and result.gesture_type == GestureType.MOVE:
            print("✅ Gesture stability mechanism working")
            stability_test_passed = True
        else:
            print(f"❌ Stability mechanism failed: {result}")
            stability_test_passed = False
        
        # Test cooldown mechanism
        recognizer.reset()
        
        # Process click gesture multiple times quickly
        for i in range(3):
            result = recognizer.process_landmarks(click_landmarks)
        
        # Should only trigger once due to cooldown
        second_result = recognizer.process_landmarks(click_landmarks)
        
        if second_result is None:  # Should be in cooldown
            print("✅ Cooldown mechanism working")
            cooldown_test_passed = True
        else:
            print("❌ Cooldown mechanism failed")
            cooldown_test_passed = False
        
        # Test KEYBOARD gesture (all fingers)
        keyboard_landmarks = create_mock_landmarks("all_fingers")
        keyboard_gesture = recognizer._recognize_gesture(keyboard_landmarks)
        
        # Should detect building toward keyboard mode  
        if keyboard_gesture.gesture_type == GestureType.IDLE and keyboard_gesture.data.get('building_keyboard'):
            print("✅ KEYBOARD gesture building detection working")
            keyboard_test_passed = True
        else:
            print(f"❌ KEYBOARD gesture detection failed: {keyboard_gesture.gesture_type}")
            keyboard_test_passed = False
        
        # Test reset functionality
        recognizer.reset()
        if len(recognizer.gesture_history) == 0 and recognizer.stable_gesture is None:
            print("✅ Reset functionality working")
            reset_test_passed = True
        else:
            print("❌ Reset functionality failed")
            reset_test_passed = False
        
        all_tests_passed = all([
            move_test_passed,
            click_test_passed,
            stability_test_passed,
            cooldown_test_passed,
            keyboard_test_passed,
            reset_test_passed
        ])
        
        if all_tests_passed:
            print("🎉 All gesture recognition tests PASSED")
        else:
            print("❌ Some gesture recognition tests FAILED")
        
        return all_tests_passed
        
    except Exception as e:
        print(f"❌ Gesture recognition test failed: {e}")
        return False

if __name__ == "__main__":
    test_gesture_recognition()