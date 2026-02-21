"""
Keyboard Shortcut Mode for HandControl
Enhanced keyboard mode with visual feedback and platform-aware shortcuts
"""
import time
import platform
from typing import Dict, Any, Optional, Callable
from enum import Enum
import pyautogui

class KeyboardShortcut(Enum):
    """Keyboard shortcuts mapped to finger combinations"""
    ESCAPE = "escape"
    ENTER = "enter"
    COPY = "copy"
    PASTE = "paste"
    APP_SWITCH = "app_switch"

class KeyboardMode:
    """
    Enhanced keyboard mode with visual feedback and platform detection
    """
    
    def __init__(self, hold_time: float = 1.0, feedback_callback: Optional[Callable] = None):
        """
        Initialize keyboard mode
        
        Args:
            hold_time: Time to hold all fingers to activate keyboard mode (seconds)
            feedback_callback: Optional callback for visual feedback
        """
        self.hold_time = hold_time
        self.feedback_callback = feedback_callback
        
        # State tracking
        self.is_active = False
        self.activation_start_time: Optional[float] = None
        
        # Platform detection
        self.is_macos = platform.system() == 'Darwin'
        self.is_windows = platform.system() == 'Windows'
        self.is_linux = platform.system() == 'Linux'
        
        # Ensure FAILSAFE is always enabled
        pyautogui.FAILSAFE = True
        
        print(f"KeyboardMode initialized:")
        print(f"  Platform: {platform.system()}")
        print(f"  Hold time: {hold_time}s")
        print(f"  FAILSAFE: {pyautogui.FAILSAFE}")
    
    def update(self, all_fingers_extended: bool, finger_data: Dict[str, Any]) -> Optional[KeyboardShortcut]:
        """
        Update keyboard mode state
        
        Args:
            all_fingers_extended: True if all 5 fingers are extended
            finger_data: Dictionary containing finger information
            
        Returns:
            KeyboardShortcut if a shortcut should be executed, None otherwise
        """
        current_time = time.time()
        
        if all_fingers_extended:
            if not self.is_active and self.activation_start_time is None:
                # Start activation sequence
                self.activation_start_time = current_time
                if self.feedback_callback:
                    self.feedback_callback("keyboard_activating", {"remaining": self.hold_time})
                
            elif self.activation_start_time and not self.is_active:
                # Check if held long enough
                held_time = current_time - self.activation_start_time
                remaining = max(0, self.hold_time - held_time)
                
                if self.feedback_callback:
                    self.feedback_callback("keyboard_activating", {"remaining": remaining})
                
                if held_time >= self.hold_time:
                    # Activate keyboard mode
                    self.is_active = True
                    self.activation_start_time = None
                    if self.feedback_callback:
                        self.feedback_callback("keyboard_active", {})
                    print("⌨️ KEYBOARD MODE ACTIVE")
        else:
            # Fingers not all extended
            if self.is_active:
                # Process shortcut based on current finger configuration
                shortcut = self._detect_shortcut(finger_data)
                if shortcut:
                    self._exit_keyboard_mode()
                    return shortcut
            else:
                # Reset activation if not fully extended
                self.activation_start_time = None
                if self.feedback_callback:
                    self.feedback_callback("keyboard_inactive", {})
        
        return None
    
    def _detect_shortcut(self, finger_data: Dict[str, Any]) -> Optional[KeyboardShortcut]:
        """
        Detect keyboard shortcut based on finger configuration
        
        Args:
            finger_data: Dictionary containing finger information
            
        Returns:
            KeyboardShortcut to execute or None
        """
        finger_count = finger_data.get('finger_count', 0)
        thumb_extended = finger_data.get('thumb_extended', False)
        
        print(f"Keyboard gesture detected: {finger_count} fingers, thumb: {thumb_extended}")
        
        if finger_count == 1:  # Index only
            return KeyboardShortcut.ESCAPE
        elif finger_count == 2:  # Index + Middle
            return KeyboardShortcut.ENTER
        elif finger_count == 3:  # Index + Middle + Ring
            return KeyboardShortcut.COPY
        elif finger_count == 4:  # All fingers except thumb
            return KeyboardShortcut.PASTE
        elif finger_count == 0 and thumb_extended:  # Thumb only
            return KeyboardShortcut.APP_SWITCH
        
        return None
    
    def execute_shortcut(self, shortcut: KeyboardShortcut) -> None:
        """
        Execute keyboard shortcut
        
        Args:
            shortcut: Shortcut to execute
        """
        if shortcut == KeyboardShortcut.ESCAPE:
            print("⚡ Escape")
            pyautogui.press('escape')
            
        elif shortcut == KeyboardShortcut.ENTER:
            print("↵ Enter")
            pyautogui.press('enter')
            
        elif shortcut == KeyboardShortcut.COPY:
            if self.is_macos:
                print("📋 Cmd+C (Copy)")
                pyautogui.hotkey('cmd', 'c')
            else:
                print("📋 Ctrl+C (Copy)")
                pyautogui.hotkey('ctrl', 'c')
                
        elif shortcut == KeyboardShortcut.PASTE:
            if self.is_macos:
                print("📄 Cmd+V (Paste)")
                pyautogui.hotkey('cmd', 'v')
            else:
                print("📄 Ctrl+V (Paste)")
                pyautogui.hotkey('ctrl', 'v')
                
        elif shortcut == KeyboardShortcut.APP_SWITCH:
            if self.is_macos:
                print("🔄 Cmd+Tab (App Switch)")
                pyautogui.hotkey('cmd', 'tab')
            else:
                print("🔄 Alt+Tab (App Switch)")
                pyautogui.hotkey('alt', 'tab')
        
        if self.feedback_callback:
            self.feedback_callback("shortcut_executed", {"shortcut": shortcut.value})
    
    def _exit_keyboard_mode(self) -> None:
        """Exit keyboard mode"""
        self.is_active = False
        self.activation_start_time = None
        if self.feedback_callback:
            self.feedback_callback("keyboard_inactive", {})
        print("⌨️ Exiting keyboard mode")
    
    def force_exit(self) -> None:
        """Force exit keyboard mode"""
        self._exit_keyboard_mode()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current keyboard mode status
        
        Returns:
            Status dictionary
        """
        status = {
            'is_active': self.is_active,
            'is_activating': self.activation_start_time is not None,
            'platform': platform.system(),
            'hold_time': self.hold_time
        }
        
        if self.activation_start_time:
            elapsed = time.time() - self.activation_start_time
            status['activation_progress'] = min(1.0, elapsed / self.hold_time)
            status['remaining_time'] = max(0, self.hold_time - elapsed)
        
        return status


class KeyboardModeVisualizer:
    """
    Visual feedback for keyboard mode (requires OpenCV)
    """
    
    def __init__(self):
        """Initialize visualizer"""
        try:
            import cv2
            self.cv2 = cv2
            self.available = True
        except ImportError:
            self.available = False
            print("OpenCV not available - keyboard mode visual feedback disabled")
    
    def draw_keyboard_status(self, frame, status: Dict[str, Any]) -> None:
        """
        Draw keyboard mode status on frame
        
        Args:
            frame: OpenCV frame
            status: Status from KeyboardMode.get_status()
        """
        if not self.available:
            return
        
        h, w = frame.shape[:2]
        
        if status['is_active']:
            # Active keyboard mode
            text = "KEYBOARD MODE ACTIVE"
            color = (0, 255, 0)  # Green
            
            # Draw background
            self.cv2.rectangle(frame, (w//2 - 150, 50), (w//2 + 150, 100), (0, 0, 0), -1)
            self.cv2.rectangle(frame, (w//2 - 150, 50), (w//2 + 150, 100), color, 2)
            
            # Draw text
            text_size = self.cv2.getTextSize(text, self.cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            text_x = w//2 - text_size[0]//2
            self.cv2.putText(frame, text, (text_x, 80), self.cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
        elif status['is_activating']:
            # Activating keyboard mode - show progress
            progress = status['activation_progress']
            remaining = status['remaining_time']
            
            text = f"KEYBOARD MODE {remaining:.1f}s"
            color = (0, 255, 255)  # Yellow
            
            # Draw background
            self.cv2.rectangle(frame, (w//2 - 150, 50), (w//2 + 150, 100), (0, 0, 0), -1)
            
            # Draw progress bar
            bar_width = int(300 * progress)
            if bar_width > 0:
                self.cv2.rectangle(frame, (w//2 - 150, 50), (w//2 - 150 + bar_width, 100), color, -1)
            
            # Draw border
            self.cv2.rectangle(frame, (w//2 - 150, 50), (w//2 + 150, 100), color, 2)
            
            # Draw text
            text_size = self.cv2.getTextSize(text, self.cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            text_x = w//2 - text_size[0]//2
            self.cv2.putText(frame, text, (text_x, 80), self.cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    
    def draw_shortcut_reference(self, frame) -> None:
        """
        Draw keyboard shortcut reference
        
        Args:
            frame: OpenCV frame
        """
        if not self.available:
            return
        
        h, w = frame.shape[:2]
        
        shortcuts = [
            "1 finger → Escape",
            "2 fingers → Enter", 
            "3 fingers → Copy",
            "4 fingers → Paste",
            "Thumb only → App Switch"
        ]
        
        # Draw background
        ref_height = len(shortcuts) * 25 + 20
        self.cv2.rectangle(frame, (10, h - ref_height - 10), (300, h - 10), (0, 0, 0), -1)
        self.cv2.rectangle(frame, (10, h - ref_height - 10), (300, h - 10), (255, 255, 255), 1)
        
        # Draw shortcuts
        for i, shortcut in enumerate(shortcuts):
            y = h - ref_height + i * 25 + 20
            self.cv2.putText(frame, shortcut, (15, y), self.cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)


def test_keyboard_mode() -> bool:
    """Test keyboard mode functionality"""
    print("Testing keyboard mode...")
    
    # Test platform detection
    keyboard_mode = KeyboardMode(hold_time=0.1)  # Short time for testing
    
    expected_platform = platform.system()
    if expected_platform == 'Darwin':
        assert keyboard_mode.is_macos and not keyboard_mode.is_windows and not keyboard_mode.is_linux
    elif expected_platform == 'Windows':
        assert keyboard_mode.is_windows and not keyboard_mode.is_macos and not keyboard_mode.is_linux
    elif expected_platform == 'Linux':
        assert keyboard_mode.is_linux and not keyboard_mode.is_macos and not keyboard_mode.is_windows
    
    print(f"✅ Platform detection: {expected_platform}")
    
    # Test activation sequence
    assert not keyboard_mode.is_active
    assert keyboard_mode.activation_start_time is None
    
    # Start activation
    result = keyboard_mode.update(True, {'finger_count': 5})
    assert result is None  # No shortcut yet
    assert keyboard_mode.activation_start_time is not None
    assert not keyboard_mode.is_active
    
    print("✅ Activation sequence started")
    
    # Wait for activation
    time.sleep(0.11)  # Wait longer than hold_time
    result = keyboard_mode.update(True, {'finger_count': 5})
    assert result is None
    assert keyboard_mode.is_active
    
    print("✅ Keyboard mode activated")
    
    # Test shortcuts
    test_cases = [
        ({'finger_count': 1, 'thumb_extended': False}, KeyboardShortcut.ESCAPE),
        ({'finger_count': 2, 'thumb_extended': False}, KeyboardShortcut.ENTER),
        ({'finger_count': 3, 'thumb_extended': False}, KeyboardShortcut.COPY),
        ({'finger_count': 4, 'thumb_extended': False}, KeyboardShortcut.PASTE),
        ({'finger_count': 0, 'thumb_extended': True}, KeyboardShortcut.APP_SWITCH),
    ]
    
    for finger_data, expected_shortcut in test_cases:
        # Reactivate keyboard mode
        keyboard_mode.is_active = True
        
        result = keyboard_mode.update(False, finger_data)  # Not all fingers extended
        assert result == expected_shortcut
        assert not keyboard_mode.is_active  # Should auto-exit
        
        print(f"✅ Shortcut detection: {finger_data} → {expected_shortcut.value}")
    
    # Test status reporting
    keyboard_mode.activation_start_time = time.time()
    status = keyboard_mode.get_status()
    
    assert 'is_active' in status
    assert 'is_activating' in status
    assert 'platform' in status
    assert 'activation_progress' in status
    assert 'remaining_time' in status
    
    print("✅ Status reporting working")
    
    # Test force exit
    keyboard_mode.is_active = True
    keyboard_mode.force_exit()
    assert not keyboard_mode.is_active
    
    print("✅ Force exit working")
    
    print("🎉 All keyboard mode tests PASSED")
    return True


if __name__ == "__main__":
    success = test_keyboard_mode()
    
    if success:
        print("\n✅ Keyboard Mode ready!")
        print("\nFeatures:")
        print("  🖐️ All 5 fingers held 1 second → Keyboard Mode")
        print("  ⚡ 1 finger → Escape")
        print("  ↵ 2 fingers → Enter")
        print("  📋 3 fingers → Copy (Cmd+C on macOS, Ctrl+C on others)")
        print("  📄 4 fingers → Paste (Cmd+V on macOS, Ctrl+V on others)")
        print("  🔄 Thumb only → App Switch (Cmd+Tab on macOS, Alt+Tab on others)")
        print("  🔄 Auto-exit after shortcut execution")
        print("  🖥️ Platform detection for correct modifier keys")
        print("  👁️ Visual feedback (requires OpenCV)")
    else:
        print("\n❌ Keyboard Mode has issues - needs fixes")