"""
Configuration management for HandControl
Handles YAML configuration loading and default values
"""
from typing import Dict, Any, Optional
import yaml
import os
from pathlib import Path

class Config:
    """Configuration manager for HandControl"""
    
    DEFAULT_CONFIG = {
        'camera': {
            'index': 0,
            'fps_target': 30,
            'width': 640,
            'height': 480,
            'mirror': True
        },
        'mediapipe': {
            'max_num_hands': 1,
            'min_detection_confidence': 0.7,
            'min_tracking_confidence': 0.5,
            'static_image_mode': False
        },
        'gestures': {
            # All thresholds relative to hand_size (wrist to middle MCP distance)
            'finger_threshold': 0.15,  # Relative to hand_size
            'pinch_threshold': 0.08,   # Relative to hand_size
            'stability_frames': 3,     # Consecutive frames before trigger
            'cooldown_click_ms': 300,  # Click cooldown
            'cooldown_scroll_ms': 50,  # Scroll cooldown
            'keyboard_hold_time': 1.0  # Seconds to hold for keyboard mode
        },
        'smoothing': {
            'type': 'one_euro',  # 'one_euro' or 'ema'
            'ema_alpha': 0.3,
            'one_euro_freq': 30,
            'one_euro_mincutoff': 1.0,
            'one_euro_beta': 0.007,
            'one_euro_dcutoff': 1.0
        },
        'cursor': {
            'dead_zone': 0.1,  # Center 80% maps to 100% screen (10% margins)
            'acceleration_curve': True,
            'sensitivity': 1.0
        },
        'display': {
            'show_preview': True,
            'show_landmarks': True,
            'show_fps': True,
            'preview_scale': 0.5
        },
        'keyboard_shortcuts': {
            'platform': 'auto',  # 'auto', 'macos', 'linux'
            'shortcuts': {
                '1_finger': 'escape',
                '2_fingers': 'return',
                '3_fingers': 'cmd+c',  # Will auto-convert to ctrl+c on Linux
                '4_fingers': 'cmd+v',
                'thumb_only': 'cmd+tab'
            }
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            config_path: Path to config YAML file. If None, uses default config.
        """
        self.config = self.DEFAULT_CONFIG.copy()
        self.config_path = config_path
        
        if config_path and os.path.exists(config_path):
            self.load_from_file(config_path)
        
        # Auto-detect platform for keyboard shortcuts
        if self.config['keyboard_shortcuts']['platform'] == 'auto':
            import sys
            self.config['keyboard_shortcuts']['platform'] = 'macos' if sys.platform == 'darwin' else 'linux'
    
    def load_from_file(self, config_path: str) -> None:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
            
            # Deep merge user config with defaults
            self._deep_merge(self.config, user_config)
            
        except Exception as e:
            print(f"Warning: Could not load config from {config_path}: {e}")
            print("Using default configuration")
    
    def save_to_file(self, config_path: str) -> None:
        """Save current configuration to YAML file"""
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
        except Exception as e:
            print(f"Error saving config to {config_path}: {e}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Args:
            key_path: Dot-separated key path (e.g., 'camera.fps_target')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Set configuration value using dot notation
        
        Args:
            key_path: Dot-separated key path (e.g., 'camera.fps_target') 
            value: Value to set
        """
        keys = key_path.split('.')
        target = self.config
        
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        
        target[keys[-1]] = value
    
    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """Deep merge update dict into base dict"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def create_sample_config(self, output_path: str = "config.yaml") -> None:
        """Create a sample configuration file"""
        self.save_to_file(output_path)
        print(f"Sample configuration saved to {output_path}")

# Global config instance
_global_config: Optional[Config] = None

def get_config(config_path: Optional[str] = None) -> Config:
    """Get global configuration instance"""
    global _global_config
    if _global_config is None:
        _global_config = Config(config_path)
    return _global_config

def load_config(config_path: str) -> Config:
    """Load configuration from file and set as global"""
    global _global_config
    _global_config = Config(config_path)
    return _global_config