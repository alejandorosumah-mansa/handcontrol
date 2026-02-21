"""
Calibration system for HandControl
Provides 4-corner calibration for screen mapping accuracy
"""
import time
import json
import os
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

class CalibrationState(Enum):
    """Calibration states"""
    WAITING = "waiting"
    SHOWING_TARGET = "showing_target"
    CAPTURING = "capturing"
    COMPLETE = "complete"
    CANCELLED = "cancelled"

class CalibrationPoint:
    """A calibration point with screen and camera coordinates"""
    
    def __init__(self, screen_x: float, screen_y: float, name: str):
        """
        Initialize calibration point
        
        Args:
            screen_x: Target screen X coordinate (0.0 to 1.0)
            screen_y: Target screen Y coordinate (0.0 to 1.0) 
            name: Descriptive name for the point
        """
        self.screen_x = screen_x
        self.screen_y = screen_y
        self.name = name
        self.camera_x: Optional[float] = None
        self.camera_y: Optional[float] = None
        self.is_captured = False
    
    def capture(self, camera_x: float, camera_y: float) -> None:
        """Capture camera coordinates for this point"""
        self.camera_x = camera_x
        self.camera_y = camera_y
        self.is_captured = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'screen': [self.screen_x, self.screen_y],
            'camera': [self.camera_x, self.camera_y] if self.is_captured else None,
            'captured': self.is_captured
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CalibrationPoint':
        """Create from dictionary"""
        point = cls(data['screen'][0], data['screen'][1], data['name'])
        if data['captured'] and data['camera']:
            point.capture(data['camera'][0], data['camera'][1])
        return point

class ScreenCalibrator:
    """
    4-corner screen calibration system
    """
    
    def __init__(self, screen_width: int = 1920, screen_height: int = 1080):
        """
        Initialize calibrator
        
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Define 4-corner calibration points (normalized coordinates)
        self.points = [
            CalibrationPoint(0.1, 0.1, "Top Left"),
            CalibrationPoint(0.9, 0.1, "Top Right"), 
            CalibrationPoint(0.9, 0.9, "Bottom Right"),
            CalibrationPoint(0.1, 0.9, "Bottom Left")
        ]
        
        self.current_point_index = 0
        self.state = CalibrationState.WAITING
        self.show_instructions = True
        
        print(f"ScreenCalibrator initialized for {screen_width}x{screen_height}")
    
    def start_calibration(self) -> None:
        """Start the calibration process"""
        self.current_point_index = 0
        self.state = CalibrationState.SHOWING_TARGET
        self.show_instructions = True
        
        # Reset all points
        for point in self.points:
            point.is_captured = False
            point.camera_x = None
            point.camera_y = None
        
        print("🎯 Starting 4-corner calibration")
        print("Instructions:")
        print("  1. Point your index finger at each target circle")
        print("  2. Hold steady and press SPACE to capture")
        print("  3. Press ESC to cancel")
    
    def get_current_target(self) -> Optional[CalibrationPoint]:
        """Get the current calibration target"""
        if 0 <= self.current_point_index < len(self.points):
            return self.points[self.current_point_index]
        return None
    
    def capture_point(self, finger_x: float, finger_y: float) -> bool:
        """
        Capture the current calibration point
        
        Args:
            finger_x: Finger X coordinate (normalized 0.0 to 1.0)
            finger_y: Finger Y coordinate (normalized 0.0 to 1.0)
            
        Returns:
            True if capture successful, False otherwise
        """
        current_point = self.get_current_target()
        if not current_point:
            return False
        
        current_point.capture(finger_x, finger_y)
        print(f"✅ Captured {current_point.name}: finger({finger_x:.3f}, {finger_y:.3f})")
        
        self.current_point_index += 1
        
        if self.current_point_index >= len(self.points):
            self.state = CalibrationState.COMPLETE
            print("🎉 Calibration complete!")
            return True
        else:
            self.state = CalibrationState.SHOWING_TARGET
            next_point = self.get_current_target()
            print(f"📍 Next target: {next_point.name}")
            return True
    
    def is_complete(self) -> bool:
        """Check if calibration is complete"""
        return self.state == CalibrationState.COMPLETE
    
    def is_cancelled(self) -> bool:
        """Check if calibration was cancelled"""
        return self.state == CalibrationState.CANCELLED
    
    def cancel(self) -> None:
        """Cancel the calibration"""
        self.state = CalibrationState.CANCELLED
        print("❌ Calibration cancelled")
    
    def get_progress(self) -> float:
        """Get calibration progress (0.0 to 1.0)"""
        if len(self.points) == 0:
            return 0.0
        return self.current_point_index / len(self.points)
    
    def save_calibration(self, filepath: str) -> bool:
        """
        Save calibration data to JSON file
        
        Args:
            filepath: Path to save calibration file
            
        Returns:
            True if save successful, False otherwise
        """
        if not self.is_complete():
            print("❌ Cannot save incomplete calibration")
            return False
        
        calibration_data = {
            'version': '1.0',
            'timestamp': time.time(),
            'screen_resolution': [self.screen_width, self.screen_height],
            'points': [point.to_dict() for point in self.points]
        }
        
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(calibration_data, f, indent=2)
            
            print(f"💾 Calibration saved to {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save calibration: {e}")
            return False
    
    def load_calibration(self, filepath: str) -> bool:
        """
        Load calibration data from JSON file
        
        Args:
            filepath: Path to calibration file
            
        Returns:
            True if load successful, False otherwise
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            if 'points' not in data or len(data['points']) != 4:
                print("❌ Invalid calibration file format")
                return False
            
            # Load points
            self.points = [CalibrationPoint.from_dict(point_data) for point_data in data['points']]
            
            # Update screen resolution if available
            if 'screen_resolution' in data:
                self.screen_width, self.screen_height = data['screen_resolution']
            
            self.state = CalibrationState.COMPLETE
            print(f"📂 Calibration loaded from {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load calibration: {e}")
            return False
    
    def draw_calibration_ui(self, frame) -> None:
        """
        Draw calibration UI on frame
        
        Args:
            frame: OpenCV frame
        """
        if not CV2_AVAILABLE:
            return
        
        h, w = frame.shape[:2]
        
        # Draw current target
        current_point = self.get_current_target()
        if current_point and self.state == CalibrationState.SHOWING_TARGET:
            # Calculate target position in frame coordinates
            target_x = int(current_point.screen_x * w)
            target_y = int(current_point.screen_y * h)
            
            # Draw target circle
            cv2.circle(frame, (target_x, target_y), 50, (0, 255, 0), 3)
            cv2.circle(frame, (target_x, target_y), 10, (0, 255, 0), -1)
            
            # Draw target label
            label = f"{current_point.name} ({self.current_point_index + 1}/4)"
            text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            label_x = target_x - text_size[0] // 2
            label_y = target_y - 70
            
            # Background for text
            cv2.rectangle(frame, (label_x - 5, label_y - 25), 
                         (label_x + text_size[0] + 5, label_y + 5), (0, 0, 0), -1)
            cv2.putText(frame, label, (label_x, label_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Draw progress bar
        progress = self.get_progress()
        bar_width = int(w * 0.6)
        bar_height = 20
        bar_x = (w - bar_width) // 2
        bar_y = h - 60
        
        # Background
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), 
                     (50, 50, 50), -1)
        
        # Progress
        if progress > 0:
            progress_width = int(bar_width * progress)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + progress_width, bar_y + bar_height),
                         (0, 255, 0), -1)
        
        # Progress text
        progress_text = f"Progress: {int(progress * 100)}%"
        text_size = cv2.getTextSize(progress_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        text_x = (w - text_size[0]) // 2
        cv2.putText(frame, progress_text, (text_x, bar_y - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Instructions
        if self.show_instructions:
            instructions = [
                "Point index finger at green target",
                "Press SPACE to capture point", 
                "Press ESC to cancel",
                "Press 'h' to hide instructions"
            ]
            
            for i, instruction in enumerate(instructions):
                y_pos = 30 + i * 25
                cv2.putText(frame, instruction, (10, y_pos), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)


def run_calibration_tool(camera_index: int = 0) -> bool:
    """
    Run the interactive calibration tool
    
    Args:
        camera_index: Camera device index
        
    Returns:
        True if calibration completed successfully, False otherwise
    """
    if not CV2_AVAILABLE:
        print("❌ OpenCV not available - calibration requires camera preview")
        return False
    
    print("🎯 Starting HandControl Calibration Tool")
    
    # Initialize camera
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"❌ Could not open camera {camera_index}")
        return False
    
    # Get screen dimensions
    import pyautogui
    screen_width, screen_height = pyautogui.size()
    
    # Initialize calibrator and hand tracking
    calibrator = ScreenCalibrator(screen_width, screen_height)
    
    try:
        from hand_tracker import HandTracker
        from config import Config
        
        config = Config()
        tracker = HandTracker(config)
        
    except ImportError:
        print("❌ Hand tracking modules not available")
        cap.release()
        return False
    
    calibrator.start_calibration()
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Failed to read camera frame")
                break
            
            # Mirror frame
            frame = cv2.flip(frame, 1)
            
            # Track hand
            landmarks = tracker.track(frame)
            
            if landmarks:
                # Get index finger tip
                index_tip = landmarks.get_landmark(8)  # INDEX_FINGER_TIP
                if index_tip:
                    # Draw finger position
                    finger_x_px = int(index_tip[0] * frame.shape[1])
                    finger_y_px = int(index_tip[1] * frame.shape[0])
                    cv2.circle(frame, (finger_x_px, finger_y_px), 8, (255, 0, 0), -1)
                
                # Draw hand landmarks
                tracker.draw_landmarks(frame, landmarks)
            
            # Draw calibration UI
            calibrator.draw_calibration_ui(frame)
            
            # Show frame
            cv2.imshow('HandControl Calibration', frame)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord(' '):  # Space - capture point
                if landmarks:
                    index_tip = landmarks.get_landmark(8)
                    if index_tip:
                        calibrator.capture_point(index_tip[0], index_tip[1])
            elif key == 27:  # ESC - cancel
                calibrator.cancel()
                break
            elif key == ord('h'):  # Hide/show instructions
                calibrator.show_instructions = not calibrator.show_instructions
            elif key == ord('q'):  # Quit
                break
            
            # Check if calibration complete
            if calibrator.is_complete():
                # Save calibration
                os.makedirs('calibration', exist_ok=True)
                calibration_file = 'calibration/screen_mapping.json'
                
                if calibrator.save_calibration(calibration_file):
                    print("\n🎉 Calibration completed successfully!")
                    print(f"📁 Calibration data saved to: {calibration_file}")
                    print("You can now use HandControl with improved accuracy!")
                    return True
                else:
                    print("\n❌ Failed to save calibration")
                    return False
            
            elif calibrator.is_cancelled():
                print("\n❌ Calibration cancelled by user")
                return False
    
    except KeyboardInterrupt:
        print("\n❌ Calibration interrupted")
        return False
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
    
    return False


def test_calibration() -> bool:
    """Test calibration functionality"""
    print("Testing calibration system...")
    
    # Test calibrator initialization
    calibrator = ScreenCalibrator(1920, 1080)
    assert len(calibrator.points) == 4
    assert calibrator.current_point_index == 0
    assert calibrator.state == CalibrationState.WAITING
    
    # Test calibration flow
    calibrator.start_calibration()
    assert calibrator.state == CalibrationState.SHOWING_TARGET
    
    # Capture all points
    test_points = [(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)]
    
    for i, (x, y) in enumerate(test_points):
        current_point = calibrator.get_current_target()
        assert current_point is not None
        assert current_point.name in ["Top Left", "Top Right", "Bottom Right", "Bottom Left"]
        
        result = calibrator.capture_point(x, y)
        assert result == True
        assert current_point.is_captured
        assert current_point.camera_x == x
        assert current_point.camera_y == y
    
    # Should be complete now
    assert calibrator.is_complete()
    assert calibrator.get_progress() == 1.0
    
    # Test save/load
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        # Save
        success = calibrator.save_calibration(temp_path)
        assert success
        
        # Load into new calibrator
        new_calibrator = ScreenCalibrator(1920, 1080)
        success = new_calibrator.load_calibration(temp_path)
        assert success
        assert new_calibrator.is_complete()
        
        # Verify points match
        for i, point in enumerate(new_calibrator.points):
            original_point = calibrator.points[i]
            assert point.screen_x == original_point.screen_x
            assert point.screen_y == original_point.screen_y
            assert point.camera_x == original_point.camera_x
            assert point.camera_y == original_point.camera_y
        
    finally:
        os.unlink(temp_path)
    
    print("✅ All calibration tests passed")
    return True


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        # Run tests
        success = test_calibration()
        if not success:
            sys.exit(1)
    else:
        # Run calibration tool
        success = run_calibration_tool()
        if not success:
            sys.exit(1)