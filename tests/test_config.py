"""Tests for configuration"""
import pytest
import os
import yaml
from config import Config


def test_default_config():
    c = Config()
    assert c.get('app.version') == '2.0.0'
    assert c.get('mediapipe.max_num_hands') == 2
    assert c.get('smoothing.one_euro_mincutoff') == 0.3


def test_get_nested():
    c = Config()
    assert c.get('camera.fps_target') == 30
    assert c.get('nonexistent.key', 'default') == 'default'


def test_set():
    c = Config()
    c.set('camera.fps_target', 60)
    assert c.get('camera.fps_target') == 60


def test_save_load(temp_dir):
    c = Config()
    path = os.path.join(temp_dir, 'test.yaml')
    c.save_to_file(path)
    assert os.path.exists(path)

    c2 = Config(path)
    assert c2.get('app.version') == '2.0.0'


def test_load_override(temp_dir):
    override = {'camera': {'fps_target': 120}}
    path = os.path.join(temp_dir, 'override.yaml')
    with open(path, 'w') as f:
        yaml.dump(override, f)

    c = Config(path)
    assert c.get('camera.fps_target') == 120
    # Other defaults preserved
    assert c.get('camera.width') == 640


def test_platform_auto():
    import sys
    c = Config()
    expected = 'macos' if sys.platform == 'darwin' else 'linux'
    assert c.get('keyboard_shortcuts.platform') == expected
