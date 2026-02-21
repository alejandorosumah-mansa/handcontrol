# HandControl

**Gesture-based cursor control using computer vision**

HandControl is a Python application that allows you to control your computer's cursor and execute actions using hand gestures captured through your webcam. It uses MediaPipe for hand tracking and provides smooth, responsive cursor control with customizable gestures.

## Features

- **Real-time hand tracking** with MediaPipe
- **Smooth cursor control** with One Euro Filter or EMA smoothing
- **Gesture recognition** for mouse actions and keyboard shortcuts
- **4-corner calibration** for improved accuracy
- **Keyboard shortcut mode** with platform-aware shortcuts
- **Configurable settings** via YAML files
- **Headless mode** support for remote operation
- **Cross-platform** support (macOS, Linux, Windows)

## Installation

### Prerequisites

- Python 3.8 or higher
- Webcam/camera access
- On macOS: Accessibility permissions for cursor control

### Install Dependencies

```bash
# Clone the repository
git clone https://github.com/your-username/handcontrol.git
cd handcontrol

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

### macOS Accessibility Permission

On macOS, you need to grant Accessibility permission for cursor control:

1. Open **System Preferences** → **Security & Privacy** → **Accessibility**
2. Click the lock icon and enter your password
3. Add Python (or Terminal app if running from terminal)
4. Restart HandControl

## Usage

### Basic Usage

```bash
# Run with default settings
python -m handcontrol

# Run without preview window (headless mode)
python -m handcontrol --no-preview

# Use custom configuration file
python -m handcontrol --config my_config.yaml

# Create default configuration file
python -m handcontrol --create-config
```

### Calibration

For improved accuracy, run the calibration tool:

```bash
# Run 4-corner calibration
python -m handcontrol --calibrate
```

The calibration process will:
1. Show circles at screen corners
2. Ask you to point your index finger at each circle
3. Press SPACE to capture each point
4. Save calibration data for improved accuracy

## Gesture Reference

### Basic Gestures

| Gesture | Action | Description |
|---------|---------|-------------|
| 👆 **Index Finger Extended** | Cursor Movement | Move cursor by pointing |
| 🤏 **Index + Middle Pinch** | Left Click | Pinch index and middle fingers together |
| 🫴 **Three Finger Pinch** | Right Click | Pinch index, middle, and ring fingers |
| 👌 **Thumb + Index Pinch** | Double Click | Touch thumb and index finger |
| ✌️ **Two Fingers Spread** | Scroll | Extend index and middle, move up/down |
| ✊👍 **Fist + Thumb** | Toggle Drag | Make fist with thumb extended |

### Keyboard Shortcut Mode

Hold all 5 fingers extended for 1 second to enter **Keyboard Mode**:

| Fingers | Shortcut | macOS | Linux/Windows |
|---------|----------|--------|---------------|
| 1️⃣ Index only | Escape | `Esc` | `Esc` |
| 2️⃣ Index + Middle | Enter | `Return` | `Enter` |
| 3️⃣ Index + Middle + Ring | Copy | `⌘C` | `Ctrl+C` |
| 4️⃣ All fingers (no thumb) | Paste | `⌘V` | `Ctrl+V` |
| 👍 Thumb only | App Switch | `⌘Tab` | `Alt+Tab` |

**Note**: Keyboard mode automatically exits after executing a shortcut.

## Configuration

### Configuration File Structure

Create a `config.yaml` file to customize settings:

```yaml
# Camera settings
camera:
  index: 0          # Camera device index
  width: 640        # Frame width
  height: 480       # Frame height
  fps_target: 30    # Target FPS
  mirror: true      # Mirror camera feed

# Gesture recognition settings
gestures:
  finger_threshold: 0.15    # Finger extension threshold (relative to hand size)
  pinch_threshold: 0.08     # Pinch detection threshold
  stability_frames: 3       # Frames required before triggering
  cooldown_click_ms: 300    # Click cooldown (milliseconds)
  cooldown_scroll_ms: 50    # Scroll cooldown
  keyboard_hold_time: 1.0   # Time to hold for keyboard mode

# Cursor control settings
cursor:
  dead_zone: 0.1           # Dead zone margin (10% on each side)
  sensitivity: 1.0         # Cursor movement sensitivity
  acceleration_curve: true # Enable acceleration for large movements

# Smoothing settings
smoothing:
  type: 'one_euro'         # 'one_euro' or 'ema'
  # One Euro Filter settings (adaptive smoothing)
  one_euro_freq: 30
  one_euro_mincutoff: 1.0
  one_euro_beta: 0.007
  # EMA Filter settings (simple smoothing)
  ema_alpha: 0.3

# Display settings
display:
  show_preview: true       # Show camera preview
  show_landmarks: true     # Show hand landmarks
  show_fps: true          # Show FPS counter
```

### Environment Variables

- `TESTING=1`: Enable test mode (disables some features)

## Controls

When running HandControl:

| Key | Action |
|-----|--------|
| `q` | Quit application |
| `p` | Pause/Resume gesture recognition |
| `r` | Reset cursor smoothing |
| `h` | Hide/Show instructions (calibration mode) |

## Troubleshooting

### Common Issues

#### Camera Not Detected
```
❌ Error: Could not open camera 0
```

**Solutions:**
- Check camera permissions
- Try different camera index: `--camera 1`
- Ensure camera isn't used by other applications
- On Linux, user might need to be in `video` group

#### Excessive Cursor Jitter
```
Cursor moves erratically or jitters
```

**Solutions:**
- Run calibration: `python -m handcontrol --calibrate`
- Adjust smoothing in config:
  ```yaml
  smoothing:
    type: 'one_euro'
    one_euro_mincutoff: 0.5  # Lower = more smoothing
  ```
- Ensure good lighting conditions
- Keep hand steady in camera view

#### Poor Gesture Recognition
```
Gestures not detected reliably
```

**Solutions:**
- Ensure good lighting
- Position hand 30-60cm from camera
- Adjust gesture thresholds in config:
  ```yaml
  gestures:
    finger_threshold: 0.12   # Lower = more sensitive
    stability_frames: 2      # Lower = more responsive
  ```

#### Permission Denied (macOS)
```
❌ Error: Operation not permitted
```

**Solutions:**
1. Open **System Preferences** → **Security & Privacy** → **Accessibility**
2. Add Python or Terminal to allowed apps
3. Restart HandControl

#### High CPU Usage
```
Python process using high CPU
```

**Solutions:**
- Reduce camera resolution in config:
  ```yaml
  camera:
    width: 320
    height: 240
  ```
- Use headless mode: `--no-preview`
- Lower target FPS:
  ```yaml
  camera:
    fps_target: 15
  ```

### Performance Optimization

1. **Camera Settings**: Lower resolution/FPS for older hardware
2. **Smoothing**: Use EMA instead of One Euro for better performance
3. **Preview**: Disable preview with `--no-preview` for headless operation
4. **Gesture Stability**: Increase `stability_frames` to reduce false positives

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Development

### Project Structure

```
handcontrol/
├── __init__.py           # Package initialization
├── __main__.py           # CLI entry point
├── main.py               # Main application
├── config.py             # Configuration management
├── camera.py             # Camera capture
├── hand_tracker.py       # MediaPipe hand tracking
├── gesture_recognition.py # Gesture detection
├── cursor_control.py     # Cursor/mouse control
├── keyboard_mode.py      # Keyboard shortcuts
├── calibration.py        # Screen calibration
├── smoothing.py          # Smoothing algorithms
├── tests/                # Test suite
│   ├── __init__.py
│   ├── conftest.py       # Test configuration
│   ├── test_*.py         # Individual test files
└── run_tests.py          # Test runner
```

### Running Tests

```bash
# Run all tests
python run_tests.py

# Run individual test categories
python -c "from run_tests import test_config_system; test_config_system()"
```

### Adding New Gestures

1. Define gesture in `gesture_recognition.py`:
   ```python
   class GestureType(Enum):
       NEW_GESTURE = "new_gesture"
   ```

2. Implement detection logic in `GestureRecognizer.recognize()`

3. Add handling in `main.py` in `_handle_gesture()`

4. Add tests in `tests/test_gesture_recognition.py`

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make changes and add tests
4. Run test suite: `python run_tests.py`
5. Commit changes: `git commit -m 'Add new feature'`
6. Push to branch: `git push origin feature/new-feature`
7. Create Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **MediaPipe** by Google for hand tracking
- **OpenCV** for computer vision utilities
- **PyAutoGUI** for system control
- **One Euro Filter** algorithm for adaptive smoothing

## Changelog

### Version 1.0.0
- Initial release
- Real-time hand tracking and gesture recognition
- Smooth cursor control with multiple algorithms
- 4-corner calibration system
- Keyboard shortcut mode
- Cross-platform support
- Comprehensive configuration system
- Full test suite

---

**Made with ❤️ for hands-free computing**