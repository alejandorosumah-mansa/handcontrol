#!/usr/bin/env python3
"""
Phase 1: Environment & Dependency Verification
Tests all core dependencies and system components for HandControl
"""
import sys
import os
from typing import Dict, Any

def check_imports() -> Dict[str, Any]:
    """Test all required imports"""
    results = {}
    
    # Test core Python imports
    try:
        import numpy as np
        results['numpy'] = {'status': 'available', 'version': np.__version__}
    except ImportError as e:
        results['numpy'] = {'status': 'missing', 'error': str(e)}
    
    # Test OpenCV
    try:
        import cv2
        results['opencv'] = {'status': 'available', 'version': cv2.__version__}
    except ImportError as e:
        results['opencv'] = {'status': 'missing', 'error': str(e)}
    
    # Test MediaPipe  
    try:
        import mediapipe as mp
        results['mediapipe'] = {'status': 'available', 'version': mp.__version__}
    except ImportError as e:
        results['mediapipe'] = {'status': 'missing', 'error': str(e)}
    
    # Test PyAutoGUI
    try:
        import pyautogui
        # CRITICAL: Always enable failsafe
        pyautogui.FAILSAFE = True
        results['pyautogui'] = {'status': 'available', 'version': pyautogui.__version__, 'failsafe': True}
    except ImportError as e:
        results['pyautogui'] = {'status': 'missing', 'error': str(e)}
    
    # Test PyYAML
    try:
        import yaml
        results['yaml'] = {'status': 'available', 'version': yaml.__version__}
    except ImportError as e:
        results['yaml'] = {'status': 'missing', 'error': str(e)}
    
    # Test pytest
    try:
        import pytest
        results['pytest'] = {'status': 'available', 'version': pytest.__version__}
    except ImportError as e:
        results['pytest'] = {'status': 'missing', 'error': str(e)}
    
    return results

def check_webcam() -> Dict[str, Any]:
    """Test webcam functionality"""
    result = {'status': 'not_tested', 'reason': 'opencv not available'}
    
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                result = {
                    'status': 'working',
                    'frame_shape': frame.shape,
                    'can_capture': True
                }
            else:
                result = {'status': 'cannot_capture', 'can_capture': False}
            cap.release()
        else:
            result = {'status': 'cannot_open', 'can_capture': False}
    except ImportError:
        result = {'status': 'opencv_missing', 'reason': 'opencv not installed'}
    except Exception as e:
        result = {'status': 'error', 'error': str(e)}
    
    return result

def check_mediapipe_hands() -> Dict[str, Any]:
    """Test MediaPipe Hands model initialization"""
    result = {'status': 'not_tested'}
    
    try:
        import mediapipe as mp
        mp_hands = mp.solutions.hands
        hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        result = {'status': 'initialized', 'model': 'MediaPipe Hands'}
        hands.close()
    except ImportError:
        result = {'status': 'mediapipe_missing', 'reason': 'mediapipe not installed'}
    except Exception as e:
        result = {'status': 'error', 'error': str(e)}
    
    return result

def check_pyautogui_cursor() -> Dict[str, Any]:
    """Test pyautogui cursor movement"""
    result = {'status': 'not_tested'}
    
    try:
        import pyautogui
        
        # CRITICAL: Always enable failsafe
        pyautogui.FAILSAFE = True
        
        # Get current position
        original_x, original_y = pyautogui.position()
        
        # Move 10px right
        pyautogui.moveRel(10, 0)
        new_x, new_y = pyautogui.position()
        
        # Move back
        pyautogui.moveRel(-10, 0)
        final_x, final_y = pyautogui.position()
        
        # Check if movement worked
        moved_correctly = (new_x == original_x + 10) and (final_x == original_x)
        
        result = {
            'status': 'working' if moved_correctly else 'movement_failed',
            'original_pos': (original_x, original_y),
            'moved_pos': (new_x, new_y),
            'final_pos': (final_x, final_y),
            'movement_successful': moved_correctly,
            'failsafe_enabled': pyautogui.FAILSAFE
        }
        
    except ImportError:
        result = {'status': 'pyautogui_missing', 'reason': 'pyautogui not installed'}
    except Exception as e:
        result = {'status': 'error', 'error': str(e)}
    
    return result

def check_macos_accessibility() -> Dict[str, Any]:
    """Check macOS Accessibility permissions"""
    result = {'status': 'unknown', 'platform': sys.platform}
    
    if sys.platform == 'darwin':  # macOS
        result.update({
            'message': 'Manual check required',
            'instructions': [
                '1. Go to System Settings → Privacy & Security → Accessibility',
                '2. Make sure Python and/or Terminal have access',
                '3. You may need to run the app first to trigger permission dialog'
            ]
        })
    else:
        result.update({
            'message': 'Not macOS - accessibility permissions not applicable'
        })
    
    return result

def run_verification() -> None:
    """Run all verification tests"""
    print("=" * 60)
    print("HANDCONTROL - PHASE 1 VERIFICATION")  
    print("=" * 60)
    
    print("\n🔍 Testing imports...")
    import_results = check_imports()
    for package, result in import_results.items():
        if result['status'] == 'available':
            print(f"✅ {package}: {result['version']}")
        else:
            print(f"❌ {package}: {result.get('error', 'missing')}")
    
    print("\n📹 Testing webcam...")
    webcam_result = check_webcam()
    if webcam_result['status'] == 'working':
        print(f"✅ Webcam: Working (frame: {webcam_result['frame_shape']})")
    else:
        print(f"❌ Webcam: {webcam_result.get('reason', webcam_result['status'])}")
    
    print("\n🤖 Testing MediaPipe Hands...")
    hands_result = check_mediapipe_hands()
    if hands_result['status'] == 'initialized':
        print(f"✅ MediaPipe Hands: {hands_result['model']}")
    else:
        print(f"❌ MediaPipe Hands: {hands_result.get('reason', hands_result['status'])}")
    
    print("\n🖱️  Testing cursor control...")
    cursor_result = check_pyautogui_cursor()
    if cursor_result['status'] == 'working':
        print(f"✅ PyAutoGUI: Cursor movement works (failsafe: {cursor_result['failsafe_enabled']})")
    else:
        print(f"❌ PyAutoGUI: {cursor_result.get('reason', cursor_result['status'])}")
    
    print("\n🔐 Checking macOS Accessibility...")
    access_result = check_macos_accessibility()
    print(f"ℹ️  Accessibility: {access_result['message']}")
    if 'instructions' in access_result:
        for instruction in access_result['instructions']:
            print(f"   {instruction}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_working = all([
        import_results.get('numpy', {}).get('status') == 'available',
        import_results.get('opencv', {}).get('status') == 'available',
        import_results.get('mediapipe', {}).get('status') == 'available', 
        import_results.get('pyautogui', {}).get('status') == 'available',
        import_results.get('yaml', {}).get('status') == 'available',
        import_results.get('pytest', {}).get('status') == 'available',
        webcam_result['status'] == 'working',
        hands_result['status'] == 'initialized',
        cursor_result['status'] == 'working'
    ])
    
    if all_working:
        print("🎉 ALL TESTS PASSED - Ready for Phase 2!")
    else:
        print("⚠️  SOME TESTS FAILED - Install missing dependencies")
        print("\nTo install dependencies:")
        print("pip install opencv-python mediapipe pyautogui pyyaml numpy pytest")
    
    # Check pyautogui.FAILSAFE
    try:
        import pyautogui
        print(f"\n🚨 CRITICAL: pyautogui.FAILSAFE = {pyautogui.FAILSAFE}")
        if not pyautogui.FAILSAFE:
            print("❌ FAILSAFE IS DISABLED - THIS IS DANGEROUS!")
    except ImportError:
        pass

if __name__ == "__main__":
    run_verification()