# Minority Report 🖐️

**Gesture-based cursor control — smooth as a sci-fi movie.**

Control your Mac with hand gestures using your webcam. Two-hand tracking, perspective-calibrated mapping, buttery-smooth cursor movement, and a modern UI.

## Features

- **🎯 Smooth cursor control** — One Euro Filter tuned for zero jitter, elastic responsiveness
- **✌️ Two-hand tracking** — Dominant hand moves cursor, both hands do gestures
- **📐 Perspective calibration** — 5-point calibration with `cv2.getPerspectiveTransform`
- **🤏 Natural gestures** — Click, scroll, drag, grab, resize windows
- **⌨️ Keyboard mode** — Hold all fingers → shortcuts via finger count
- **🖥️ Window management** — Grab to move, pull down to minimize, push up to maximize
- **⚡ Threaded pipeline** — Camera capture never blocks processing, 30+ FPS
- **📦 macOS app** — Package as .app with PyInstaller

## Gestures

| Gesture | Action |
|---------|--------|
| ☝️ Index finger only | Move cursor |
| 🤏 Index + middle pinch | Left click |
| 🤌 3-finger pinch | Right click |
| 👌 Thumb-index pinch | Double click |
| ✌️ 2 fingers spread | Scroll (Y movement) |
| 👍 Thumb only | Toggle drag |
| ✊ Fist (from open) | Grab window |
| ✊↓ Grab + pull down | Minimize |
| ✊↑ Grab + push up | Maximize |
| 🤏🤏 Both hands pinch | Resize window |
| 🖐️ All 5 fingers (1s) | Keyboard mode |

## Install (macOS)

1. **[Download MinorityReport.dmg](https://github.com/alejandorosumah-mansa/handcontrol/releases/latest/download/MinorityReport.dmg)**
2. Open the DMG, drag **Minority Report** to Applications
3. Double-click to run
4. Grant camera + accessibility permissions when prompted

Done. That's it.

> First launch: macOS may say "unidentified developer." Right-click the app → Open → Open to bypass.

## Dev Setup

If you want to run from source or contribute:

```bash
git clone https://github.com/alejandorosumah-mansa/handcontrol.git
cd handcontrol
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Configuration

```bash
python -m handcontrol --create-config  # Creates config.yaml
```

Key settings in `config.yaml`:
- `app.dominant_hand`: `right` or `left`
- `smoothing.one_euro_mincutoff`: Lower = smoother (default 0.3)
- `smoothing.one_euro_beta`: Higher = faster tracking (default 0.05)
- `mediapipe.max_num_hands`: 1 or 2

## Build macOS App

### Recommended: Python 3.11+ (Fixes cv2 corruption)

```bash
# Install Python 3.11 (if not available)
brew install python@3.11

# Build with Python 3.11 (recommended)
make build-py311
# or
./build_app_py311.py

# Output: dist/Minority Report.app
```

### Legacy: Current Python (may fail on Python 3.9)

```bash
python build_app.py  # May fail with cv2.abi3.so corruption on Python 3.9
```

### Build Commands

```bash
make help           # Show all build options
make build-py311    # Build with Python 3.11 (recommended)
make clean          # Clean build artifacts  
make test           # Test the built app
make dmg            # Create DMG installer
```

## Tests

```bash
pytest tests/ -v
```

## Architecture

```
Camera (threaded) → MediaPipe (2 hands) → Gesture Recognition → Cursor/Actions
                                              ↓
                                    One Euro Filter (smooth)
                                              ↓
                                    Perspective Transform (calibrated)
                                              ↓
                                    pyautogui (cursor/keys)
```

## Requirements

- Python 3.8+
- macOS (primary), Linux supported
- Webcam
- Accessibility permissions (for cursor control)
