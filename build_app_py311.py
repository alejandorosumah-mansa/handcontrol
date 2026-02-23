#!/usr/bin/env python3
"""
Build Minority Report as a macOS .app bundle using PyInstaller with Python 3.11.

This script creates a new virtual environment with Python 3.11 to avoid
cv2.abi3.so corruption issues present in Python 3.9.

Usage:
    python build_app_py311.py

Output:
    dist/Minority Report.app
"""
import subprocess
import sys
import os
import shutil
from pathlib import Path


def check_python311():
    """Check if Python 3.11+ is available."""
    python311_paths = [
        "/opt/homebrew/bin/python3.11",
        "/usr/local/bin/python3.11",
        shutil.which("python3.11")
    ]
    
    for path in python311_paths:
        if path and Path(path).exists():
            try:
                result = subprocess.run([path, "--version"], capture_output=True, text=True)
                if result.returncode == 0:
                    version = result.stdout.strip()
                    print(f"Found Python 3.11+: {path} ({version})")
                    return path
            except Exception:
                continue
    
    print("❌ Python 3.11+ not found!")
    print("Install it with: brew install python@3.11")
    return None


def setup_venv(python311_path):
    """Set up virtual environment with Python 3.11."""
    venv_path = Path("venv_py311")
    
    if venv_path.exists():
        print("Removing existing venv_py311...")
        shutil.rmtree(venv_path)
    
    print("Creating virtual environment with Python 3.11...")
    subprocess.run([python311_path, "-m", "venv", str(venv_path)], check=True)
    
    # Install requirements
    pip_path = venv_path / "bin" / "pip"
    print("Installing requirements...")
    subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
    subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], check=True)
    
    return venv_path


def generate_icon():
    """Generate a simple app icon (hand silhouette on blue gradient)."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("Pillow not installed — skipping icon generation")
        return None

    size = 512
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Blue gradient circle background
    for i in range(size // 2, 0, -1):
        ratio = i / (size // 2)
        r = int(0 * ratio + 30 * (1 - ratio))
        g = int(90 * ratio + 144 * (1 - ratio))
        b = int(255 * ratio + 255 * (1 - ratio))
        draw.ellipse(
            [size // 2 - i, size // 2 - i, size // 2 + i, size // 2 + i],
            fill=(r, g, b, 255)
        )

    # Simple hand shape (open palm)
    palm_cx, palm_cy = size // 2, size // 2 + 40
    palm_r = 80
    draw.ellipse(
        [palm_cx - palm_r, palm_cy - palm_r, palm_cx + palm_r, palm_cy + palm_r],
        fill=(255, 255, 255, 230)
    )

    # Fingers
    finger_positions = [
        (palm_cx - 55, palm_cy - 60, 18, 90),   # pinky
        (palm_cx - 22, palm_cy - 80, 18, 110),   # ring
        (palm_cx + 10, palm_cy - 90, 18, 120),   # middle
        (palm_cx + 42, palm_cy - 75, 18, 105),   # index
        (palm_cx + 75, palm_cy - 20, 16, 70),    # thumb (angled)
    ]

    for fx, fy, fw, fh in finger_positions:
        draw.rounded_rectangle(
            [fx - fw, fy - fh, fx + fw, fy],
            radius=fw,
            fill=(255, 255, 255, 230)
        )

    # Save as PNG and convert to ICNS
    icon_path = Path('build_resources')
    icon_path.mkdir(exist_ok=True)

    png_path = icon_path / 'icon.png'
    img.save(str(png_path))

    # Create iconset for macOS
    iconset_path = icon_path / 'MinorityReport.iconset'
    iconset_path.mkdir(exist_ok=True)

    for sz in [16, 32, 64, 128, 256, 512]:
        resized = img.resize((sz, sz), Image.LANCZOS)
        resized.save(str(iconset_path / f'icon_{sz}x{sz}.png'))
        if sz <= 256:
            resized2x = img.resize((sz * 2, sz * 2), Image.LANCZOS)
            resized2x.save(str(iconset_path / f'icon_{sz}x{sz}@2x.png'))

    # Convert to icns
    icns_path = icon_path / 'MinorityReport.icns'
    try:
        subprocess.run(
            ['iconutil', '-c', 'icns', str(iconset_path), '-o', str(icns_path)],
            check=True, capture_output=True
        )
        print(f"Icon generated: {icns_path}")
        return str(icns_path)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("iconutil not available — using PNG icon")
        return str(png_path)


def build_app(venv_path):
    """Build the app using PyInstaller."""
    print("Building Minority Report.app...")

    # Generate icon
    icon_path = generate_icon()

    # Use Python from the venv
    python_path = venv_path / "bin" / "python"

    cmd = [
        str(python_path), '-m', 'PyInstaller',
        '--name', 'Minority Report',
        '--windowed',
        '--onedir',
        '--noconfirm',
        '--clean',
        '--add-data', 'config.py:.',
        '--hidden-import', 'mediapipe',
        '--hidden-import', 'cv2',
        '--hidden-import', 'pyautogui',
        '--hidden-import', 'PIL',
    ]

    if icon_path and icon_path.endswith('.icns'):
        cmd.extend(['--icon', icon_path])

    cmd.append('main.py')

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n✅ Build successful!")
        print("App: dist/Minority Report.app")
        print("\nTo test:")
        print('  "./dist/Minority Report.app/Contents/MacOS/Minority Report" --help')
        print("\nTo create a DMG:")
        print('  hdiutil create -volname "Minority Report" -srcfolder "dist/Minority Report.app" -ov -format UDZO "dist/MinorityReport.dmg"')
        return True
    else:
        print("\n❌ Build failed")
        return False


def main():
    print("HandControl macOS App Builder (Python 3.11)")
    print("=" * 50)

    # Check for Python 3.11
    python311_path = check_python311()
    if not python311_path:
        sys.exit(1)

    try:
        # Set up virtual environment
        venv_path = setup_venv(python311_path)

        # Build the app
        success = build_app(venv_path)

        if success:
            print("\n🎉 Build complete!")
        else:
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()