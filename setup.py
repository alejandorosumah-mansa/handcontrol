#!/usr/bin/env python3
"""
Setup script for HandControl
Installs dependencies with proper error handling for limited disk space
"""
import subprocess
import sys
import os

def install_package(package):
    """Install a single package with error handling"""
    print(f"Installing {package}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error installing {package}: {e}")
        return False

def main():
    """Install all dependencies"""
    # Essential packages in order of priority
    packages = [
        "numpy",
        "pyyaml", 
        "pytest",
        "pyautogui",
        "opencv-python==4.8.1.78",
        "mediapipe==0.10.8"
    ]
    
    print("Setting up HandControl dependencies...")
    print("=" * 50)
    
    # Activate virtual environment if it exists
    venv_python = os.path.join("venv", "bin", "python")
    if os.path.exists(venv_python):
        print("Using virtual environment...")
    
    success_count = 0
    for package in packages:
        if install_package(package):
            success_count += 1
        else:
            print(f"Skipping {package} due to installation failure")
    
    print("=" * 50)
    print(f"Installation complete: {success_count}/{len(packages)} packages installed")
    
    if success_count == len(packages):
        print("🎉 All packages installed! Run 'python3 verify_dependencies.py' to test")
    else:
        print("⚠️  Some packages failed. Check disk space and try again.")

if __name__ == "__main__":
    main()