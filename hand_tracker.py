"""
Hand tracking module using MediaPipe Hands
Wraps MediaPipe for hand landmark detection and drawing
"""
from typing import Optional, List, Tuple, NamedTuple
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
    """Single hand landmark with normalized coordinates"""
    x: float  # Normalized x coordinate (0.0 - 1.0)
    y: float  # Normalized y coordinate (0.0 - 1.0) 
    z: float  # Relative z coordinate (depth)

class HandLandmarks:
    """Collection of 21 hand landmarks with helper methods"""
    
    # MediaPipe hand landmark indices
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
    
    def __init__(self, landmarks: List[HandLandmark]):
        """
        Initialize hand landmarks
        
        Args:
            landmarks: List of 21 HandLandmark objects
        """
        if len(landmarks) != 21:
            raise ValueError(f"Expected 21 landmarks, got {len(landmarks)}")
        
        self.landmarks = landmarks
    
    def __getitem__(self, index: int) -> HandLandmark:
        """Get landmark by index"""
        return self.landmarks[index]
    
    def get_landmark(self, index: int) -> HandLandmark:
        """Get landmark by index with bounds checking"""
        if 0 <= index < len(self.landmarks):
            return self.landmarks[index]
        raise IndexError(f"Landmark index {index} out of range")
    
    def to_pixel_coordinates(self, frame_width: int, frame_height: int) -> List[Tuple[int, int]]:
        """
        Convert normalized coordinates to pixel coordinates
        
        Args:
            frame_width: Frame width in pixels
            frame_height: Frame height in pixels
            
        Returns:
            List of (x, y) pixel coordinates
        """
        pixel_coords = []
        for landmark in self.landmarks:
            x_px = int(landmark.x * frame_width)
            y_px = int(landmark.y * frame_height)
            pixel_coords.append((x_px, y_px))
        return pixel_coords
    
    def get_hand_size(self) -> float:
        """
        Get hand size as distance between wrist and middle MCP
        This is used as reference for relative threshold calculations
        
        Returns:
            Hand size (normalized distance)
        """
        wrist = self.landmarks[self.WRIST]
        middle_mcp = self.landmarks[self.MIDDLE_MCP]
        
        dx = middle_mcp.x - wrist.x
        dy = middle_mcp.y - wrist.y
        
        return np.sqrt(dx * dx + dy * dy)

class HandTracker:
    """
    MediaPipe-based hand tracker with drawing capabilities
    """
    
    def __init__(self,
                 max_num_hands: int = 1,
                 min_detection_confidence: float = 0.7,
                 min_tracking_confidence: float = 0.5,
                 static_image_mode: bool = False):
        """
        Initialize hand tracker
        
        Args:
            max_num_hands: Maximum number of hands to detect
            min_detection_confidence: Minimum detection confidence
            min_tracking_confidence: Minimum tracking confidence  
            static_image_mode: Whether to process each frame independently
        """
        if not MEDIAPIPE_AVAILABLE:
            raise ImportError("MediaPipe is not available. Please install mediapipe")
        
        if not CV2_AVAILABLE:
            raise ImportError("OpenCV is not available. Please install opencv-python")
        
        self.max_num_hands = max_num_hands
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.static_image_mode = static_image_mode
        
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.hands = self.mp_hands.Hands(
            static_image_mode=static_image_mode,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
        print(f"HandTracker initialized (max_hands={max_num_hands}, "
              f"detection_conf={min_detection_confidence}, tracking_conf={min_tracking_confidence})")
    
    def process_frame(self, frame: np.ndarray) -> Optional[HandLandmarks]:
        """
        Process a frame to detect hand landmarks
        
        Args:
            frame: Input frame (BGR format from OpenCV)
            
        Returns:
            HandLandmarks object if hand detected, None otherwise
        """
        # Convert BGR to RGB (MediaPipe expects RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame
        results = self.hands.process(rgb_frame)
        
        if results.multi_hand_landmarks:
            # Return first hand landmarks (since max_num_hands=1)
            hand_landmarks = results.multi_hand_landmarks[0]
            
            # Convert to our format
            landmarks = []
            for landmark in hand_landmarks.landmark:
                landmarks.append(HandLandmark(
                    x=landmark.x,
                    y=landmark.y,
                    z=landmark.z
                ))
            
            return HandLandmarks(landmarks)
        
        return None
    
    def draw_landmarks(self, frame: np.ndarray, hand_landmarks: HandLandmarks) -> np.ndarray:
        """
        Draw hand landmarks on frame
        
        Args:
            frame: Input frame to draw on
            hand_landmarks: Hand landmarks to draw
            
        Returns:
            Frame with landmarks drawn
        """
        # Convert our landmarks back to MediaPipe format for drawing
        mp_landmarks = type('MockLandmarks', (), {})()
        mp_landmarks.landmark = []
        
        for landmark in hand_landmarks.landmarks:
            mp_landmark = type('MockLandmark', (), {})()
            mp_landmark.x = landmark.x
            mp_landmark.y = landmark.y
            mp_landmark.z = landmark.z
            mp_landmarks.landmark.append(mp_landmark)
        
        # Draw landmarks and connections
        self.mp_drawing.draw_landmarks(
            frame,
            mp_landmarks,
            self.mp_hands.HAND_CONNECTIONS,
            self.mp_drawing_styles.get_default_hand_landmarks_style(),
            self.mp_drawing_styles.get_default_hand_connections_style()
        )
        
        return frame
    
    def close(self) -> None:
        """Close the hand tracker and release resources"""
        if hasattr(self, 'hands') and self.hands:
            self.hands.close()
            print("HandTracker closed")

def test_hand_tracker(duration_seconds: int = 10) -> bool:
    """
    Test hand tracker with live camera feed
    
    Args:
        duration_seconds: How long to test (seconds)
        
    Returns:
        True if test successful, False otherwise
    """
    if not CV2_AVAILABLE or not MEDIAPIPE_AVAILABLE:
        print("Missing dependencies for hand tracker test")
        return False
    
    try:
        from camera import Camera
        
        print(f"Testing hand tracker for {duration_seconds} seconds...")
        print("Show your hand to the camera!")
        
        with Camera() as camera:
            tracker = HandTracker()
            
            frame_count = 0
            detection_count = 0
            import time
            start_time = time.time()
            
            try:
                while time.time() - start_time < duration_seconds:
                    ret, frame = camera.read()
                    
                    if not ret:
                        continue
                    
                    # Process frame for hand detection
                    hand_landmarks = tracker.process_frame(frame)
                    
                    frame_count += 1
                    
                    if hand_landmarks:
                        detection_count += 1
                        
                        # Draw landmarks
                        frame = tracker.draw_landmarks(frame, hand_landmarks)
                        
                        # Print hand size for testing
                        if detection_count % 30 == 0:
                            hand_size = hand_landmarks.get_hand_size()
                            print(f"Hand detected! Size: {hand_size:.3f}")
                    
                    # Print stats every 60 frames
                    if frame_count % 60 == 0:
                        detection_rate = detection_count / frame_count * 100
                        fps = camera.get_fps()
                        print(f"Frame {frame_count}: Detection rate: {detection_rate:.1f}%, FPS: {fps:.1f}")
                
                # Final stats
                total_time = time.time() - start_time
                detection_rate = detection_count / frame_count * 100 if frame_count > 0 else 0
                
                print(f"\nHand tracker test completed:")
                print(f"  Total frames: {frame_count}")
                print(f"  Detections: {detection_count}")
                print(f"  Detection rate: {detection_rate:.1f}%")
                print(f"  Average FPS: {camera.get_fps():.1f}")
                
                # Test passes if we processed frames and FPS > 15
                if frame_count > 0 and camera.get_fps() >= 15:
                    print("✅ Hand tracker test PASSED")
                    return True
                else:
                    print("❌ Hand tracker test FAILED")
                    return False
                    
            finally:
                tracker.close()
                
    except Exception as e:
        print(f"Hand tracker test failed: {e}")
        return False

if __name__ == "__main__":
    # Test the hand tracker
    test_hand_tracker()