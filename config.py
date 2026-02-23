"""
Configuration management for HandControl / Minority Report
"""
from typing import Dict, Any, Optional
import yaml
import os
import sys
from pathlib import Path


class Config:
    """Configuration manager"""

    DEFAULT_CONFIG: Dict[str, Any] = {
        'app': {
            'name': 'Minority Report',
            'version': '2.0.0',
            'dominant_hand': 'right',  # 'right' or 'left'
            'launch_at_login': False,
        },
        'camera': {
            'index': 0,
            'fps_target': 30,
            'width': 640,
            'height': 480,
            'mirror': True,
            'backend': 'avfoundation',  # macOS optimized
        },
        'mediapipe': {
            'max_num_hands': 2,
            'min_detection_confidence': 0.8,
            'min_tracking_confidence': 0.7,
            'static_image_mode': False,
            'model_complexity': 1,
        },
        'gestures': {
            'finger_threshold': 0.15,
            'pinch_threshold': 0.08,
            'grab_threshold': 0.12,
            'stability_frames': 2,
            'cooldown_click_ms': 300,
            'cooldown_scroll_ms': 50,
            'keyboard_hold_time': 1.0,
            'grab_velocity_threshold': 0.15,  # for minimize/maximize detection
        },
        'smoothing': {
            'type': 'one_euro',
            'one_euro_freq': 60,
            'one_euro_mincutoff': 0.3,   # lower = more smoothing on slow moves
            'one_euro_beta': 0.05,        # higher = faster tracking on fast moves
            'one_euro_dcutoff': 1.0,
        },
        'cursor': {
            'dead_zone': 0.08,
            'acceleration_curve': True,
            'sensitivity': 1.0,
        },
        'calibration': {
            'points': 5,  # 4 corners + center
            'hold_time': 2.0,  # seconds per point
            'auto_recalibrate': True,
            'hand_size_tolerance': 0.3,  # 30% change triggers recalibration hint
            'save_path': '~/.minority_report/calibration.json',
        },
        'display': {
            'show_preview': True,
            'show_landmarks': True,
            'show_fps': True,
        },
        'ui': {
            'floating_indicator': True,
            'indicator_width': 200,
            'indicator_height': 150,
            'indicator_opacity': 0.85,
            'accent_color': '#007AFF',  # Apple blue
        },
        'keyboard_shortcuts': {
            'platform': 'auto',
            'shortcuts': {
                '1_finger': 'escape',
                '2_fingers': 'return',
                '3_fingers': 'cmd+c',
                '4_fingers': 'cmd+v',
                'thumb_only': 'cmd+tab',
            },
        },
    }

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._deep_copy(self.DEFAULT_CONFIG)
        self.config_path = config_path

        if config_path and os.path.exists(config_path):
            self.load_from_file(config_path)

        if self.config['keyboard_shortcuts']['platform'] == 'auto':
            self.config['keyboard_shortcuts']['platform'] = (
                'macos' if sys.platform == 'darwin' else 'linux'
            )

    def _deep_copy(self, d: Dict) -> Dict:
        import copy
        return copy.deepcopy(d)

    def load_from_file(self, config_path: str) -> None:
        try:
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
            if user_config:
                self._deep_merge(self.config, user_config)
        except Exception as e:
            print(f"Warning: Could not load config from {config_path}: {e}")

    def save_to_file(self, config_path: str) -> None:
        try:
            os.makedirs(os.path.dirname(config_path) or '.', exist_ok=True)
            with open(config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
        except Exception as e:
            print(f"Error saving config to {config_path}: {e}")

    def get(self, key_path: str, default: Any = None) -> Any:
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, key_path: str, value: Any) -> None:
        keys = key_path.split('.')
        target = self.config
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        target[keys[-1]] = value

    def _deep_merge(self, base: Dict, update: Dict) -> None:
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value


_global_config: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    global _global_config
    if _global_config is None:
        _global_config = Config(config_path)
    return _global_config


def load_config(config_path: str) -> Config:
    global _global_config
    _global_config = Config(config_path)
    return _global_config
