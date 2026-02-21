"""
Tests for configuration system
"""
import pytest
import yaml
import os
from pathlib import Path

def test_config_default_initialization():
    """Test default configuration initialization"""
    from config import Config
    
    config = Config()
    
    # Test basic structure
    assert config.get('camera.index') == 0
    assert config.get('camera.width') == 640
    assert config.get('smoothing.type') == 'one_euro'
    assert config.get('gestures.finger_threshold') == 0.15

def test_config_yaml_loading(temp_dir, sample_config):
    """Test loading configuration from YAML file"""
    from config import Config
    
    # Create test config file
    config_path = os.path.join(temp_dir, 'test_config.yaml')
    with open(config_path, 'w') as f:
        yaml.dump(sample_config, f)
    
    # Load config
    config = Config(config_path)
    
    # Verify values were loaded
    assert config.get('camera.index') == 0
    assert config.get('camera.width') == 640
    assert config.get('smoothing.type') == 'one_euro'

def test_config_yaml_saving(temp_dir):
    """Test saving configuration to YAML file"""
    from config import Config
    
    config = Config()
    config_path = os.path.join(temp_dir, 'saved_config.yaml')
    
    # Modify and save
    config.set('camera.index', 1)
    config.set('smoothing.type', 'ema')
    config.save_to_file(config_path)
    
    # Load and verify
    with open(config_path, 'r') as f:
        saved_data = yaml.safe_load(f)
    
    assert saved_data['camera']['index'] == 1
    assert saved_data['smoothing']['type'] == 'ema'

def test_config_dot_notation():
    """Test dot notation get/set operations"""
    from config import Config
    
    config = Config()
    
    # Test get
    assert config.get('camera.index') == 0
    assert config.get('nonexistent.key', 'default') == 'default'
    
    # Test set
    config.set('camera.index', 2)
    config.set('new.nested.value', 'test')
    
    assert config.get('camera.index') == 2
    assert config.get('new.nested.value') == 'test'

def test_config_deep_merge():
    """Test deep merging of configurations"""
    from config import Config
    
    config = Config()
    
    # Create partial config to merge
    partial_config = {
        'camera': {
            'index': 1,  # This should override
            'fps_target': 60  # This should override
            # width/height should remain from defaults
        },
        'new_section': {
            'test_value': 123
        }
    }
    
    config._deep_merge(config.config, partial_config)
    
    # Verify merge results
    assert config.get('camera.index') == 1
    assert config.get('camera.fps_target') == 60
    assert config.get('camera.width') == 640  # Should remain from defaults
    assert config.get('new_section.test_value') == 123

def test_config_invalid_yaml(temp_dir):
    """Test handling of invalid YAML files"""
    from config import Config
    
    # Create invalid YAML file
    config_path = os.path.join(temp_dir, 'invalid.yaml')
    with open(config_path, 'w') as f:
        f.write("invalid: yaml: content: [\n")
    
    # Should fallback to defaults without crashing
    config = Config(config_path)
    assert config.get('camera.index') == 0  # Should have default value

def test_config_missing_file():
    """Test handling of missing config file"""
    from config import Config
    
    # Should fallback to defaults without crashing
    config = Config('nonexistent.yaml')
    assert config.get('camera.index') == 0

def test_config_create_sample(temp_dir):
    """Test sample config creation"""
    from config import Config
    
    config = Config()
    sample_path = os.path.join(temp_dir, 'sample.yaml')
    
    config.create_sample_config(sample_path)
    
    # Verify file was created
    assert os.path.exists(sample_path)
    
    # Verify it's valid YAML
    with open(sample_path, 'r') as f:
        data = yaml.safe_load(f)
    
    assert 'camera' in data
    assert 'gestures' in data
    assert 'smoothing' in data