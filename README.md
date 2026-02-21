# HandControl

Gesture-based computer control using webcam and MediaPipe

## Overview

HandControl replaces mouse/keyboard with hand gestures via webcam. Uses MediaPipe Hands for tracking, pyautogui for OS-level cursor/keyboard control.

## Gesture Definitions

| Gesture | Detection | Action |
|---|---|---|
| IDLE | No hand or unrecognized | Nothing |
| MOVE | Only index finger extended (others curled) | Move cursor |
| LEFT_CLICK | Index + middle extended, then pinch together (fingertip distance below threshold) | Left click |
| RIGHT_CLICK | Index + middle + ring extended, then pinch index + middle | Right click |
| DOUBLE_CLICK | Thumb tip touches index tip (pinch) | Double click |
| SCROLL | Index + middle extended and spread apart, Y-axis movement controls scroll direction | Scroll up/down |
| DRAG | Fist with only thumb out | Toggle drag mode |
| KEYBOARD | All 5 fingers open, held still for 1 second | Enter keyboard shortcut mode |

## Installation

1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
# OR use the setup script:
python3 setup.py
```

3. Verify installation:
```bash
python3 verify_dependencies.py
```

## macOS Accessibility Permissions

On macOS, you need to grant Accessibility permissions:
1. Go to System Settings → Privacy & Security → Accessibility
2. Add Python and/or Terminal to the allowed list
3. You may need to run the app first to trigger the permission dialog

## Development Status

- [x] Phase 1: Environment & Dependency Verification
- [ ] Phase 2: Hand Landmark Detection Pipeline  
- [ ] Phase 3: Gesture Recognition Engine
- [ ] Phase 4: Cursor Control
- [ ] Phase 5: Click & Interaction
- [ ] Phase 6: Scroll & Zoom
- [ ] Phase 7: Keyboard Shortcuts
- [ ] Phase 8: Polish & Config

## Safety

⚠️ **IMPORTANT**: `pyautogui.FAILSAFE = True` is ALWAYS enabled. Move cursor to top-left corner to emergency stop.

## Architecture

- `camera.py`: Webcam capture, horizontal flip, FPS tracking
- `hand_tracker.py`: MediaPipe Hands wrapper, landmark detection
- `gesture_recognition.py`: Hand gesture classification  
- `cursor_control.py`: Cursor movement and smoothing
- `smoothing.py`: One Euro Filter and EMA smoothing
- `config.py`: YAML configuration management
- `calibration.py`: Screen calibration utilities
- `tests/`: Unit test suite