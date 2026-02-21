"""
Camera capture module for HandControl
Handles webcam access, frame capture, mirroring, and FPS tracking
"""
import time
from typing import Optional, Tuple, List
import numpy as np
from collections import deque

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

class Camera:
    """
    Webcam capture with horizontal mirroring and FPS tracking
    """
    
    def __init__(self, 
                 camera_index: int = 0,
                 width: int = 640, 
                 height: int = 480,
                 fps_target: int = 30,
                 mirror: bool = True,
                 fps_window_size: int = 30):
        """
        Initialize camera capture
        
        Args:
            camera_index: Camera device index (0 for default)
            width: Frame width
            height: Frame height  
            fps_target: Target FPS (for reference, not enforced)
            mirror: Whether to flip frame horizontally (mirror effect)
            fps_window_size: Number of frames for rolling FPS average
        """
        if not CV2_AVAILABLE:
            raise ImportError("OpenCV (cv2) is not available. Please install opencv-python")
            
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps_target = fps_target
        self.mirror = mirror
        self.fps_window_size = fps_window_size
        
        # FPS tracking
        self.frame_times: deque = deque(maxlen=fps_window_size)
        self.last_frame_time = time.time()
        
        # Camera capture object
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_opened = False
        
    def open(self) -> bool:
        """
        Open camera connection
        
        Returns:
            True if camera opened successfully, False otherwise
        """
        if not CV2_AVAILABLE:
            print("Error: OpenCV not available")
            return False
            
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                print(f"Error: Could not open camera {self.camera_index}")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps_target)
            
            # Test frame capture
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Could not read frame from camera")
                self.cap.release()
                return False
            
            self.is_opened = True
            print(f"Camera {self.camera_index} opened successfully ({frame.shape[1]}x{frame.shape[0]})")
            return True
            
        except Exception as e:
            print(f"Error opening camera: {e}")
            if self.cap:
                self.cap.release()
            return False
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read a frame from the camera
        
        Returns:
            Tuple of (success, frame). Frame is None if read failed.
            Frame is horizontally flipped if mirror=True.
        """
        if not self.is_opened or not self.cap:
            return False, None
        
        try:
            ret, frame = self.cap.read()
            
            if not ret:
                return False, None
            
            # Apply horizontal flip (mirror effect)
            if self.mirror:
                frame = cv2.flip(frame, 1)
            
            # Update FPS tracking
            current_time = time.time()
            self.frame_times.append(current_time - self.last_frame_time)
            self.last_frame_time = current_time
            
            return True, frame
            
        except Exception as e:
            print(f"Error reading frame: {e}")
            return False, None
    
    def get_fps(self) -> float:
        """
        Get current FPS (rolling average)
        
        Returns:
            Current FPS, or 0 if no frames captured yet
        """
        if len(self.frame_times) == 0:
            return 0.0
        
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        return 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0
    
    def get_frame_shape(self) -> Optional[Tuple[int, int, int]]:
        """
        Get current frame shape (height, width, channels)
        
        Returns:
            Frame shape tuple or None if camera not opened
        """
        if not self.is_opened or not self.cap:
            return None
        
        ret, frame = self.cap.read()
        if ret:
            return frame.shape
        return None
    
    def close(self) -> None:
        """Close camera connection"""
        if self.cap:
            self.cap.release()
            self.is_opened = False
            print(f"Camera {self.camera_index} closed")
    
    def __enter__(self):
        """Context manager entry"""
        if not self.open():
            raise RuntimeError("Failed to open camera")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    def __del__(self):
        """Destructor - ensure camera is closed"""
        if hasattr(self, 'cap'):
            self.close()

def test_camera(camera_index: int = 0, duration_seconds: int = 10) -> bool:
    """
    Test camera functionality
    
    Args:
        camera_index: Camera device index to test
        duration_seconds: How long to test (seconds)
        
    Returns:
        True if camera test successful, False otherwise
    """
    if not CV2_AVAILABLE:
        print("OpenCV not available - cannot test camera")
        return False
    
    print(f"Testing camera {camera_index} for {duration_seconds} seconds...")
    
    try:
        with Camera(camera_index=camera_index) as camera:
            start_time = time.time()
            frame_count = 0
            
            while time.time() - start_time < duration_seconds:
                ret, frame = camera.read()
                
                if not ret:
                    print("Failed to read frame")
                    return False
                
                frame_count += 1
                
                # Print stats every 30 frames
                if frame_count % 30 == 0:
                    fps = camera.get_fps()
                    print(f"Frame {frame_count}: {frame.shape}, FPS: {fps:.1f}")
            
            # Final stats
            total_time = time.time() - start_time
            avg_fps = frame_count / total_time
            rolling_fps = camera.get_fps()
            
            print(f"\nCamera test completed:")
            print(f"  Total frames: {frame_count}")
            print(f"  Total time: {total_time:.1f}s")
            print(f"  Average FPS: {avg_fps:.1f}")
            print(f"  Rolling FPS: {rolling_fps:.1f}")
            print(f"  Frame shape: {camera.get_frame_shape()}")
            
            # Check if FPS is reasonable
            if rolling_fps >= 15:
                print("✅ Camera test PASSED")
                return True
            else:
                print("❌ Camera test FAILED - FPS too low")
                return False
                
    except Exception as e:
        print(f"Camera test failed with exception: {e}")
        return False

if __name__ == "__main__":
    # Test the camera module
    test_camera()