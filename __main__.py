"""
Minority Report CLI entry point
python -m handcontrol [--calibrate] [--no-preview] [--config PATH]
"""
import sys
import argparse
import os


def create_default_config():
    from config import Config
    config = Config()
    path = "config.yaml"
    config.save_to_file(path)
    print(f"Created default config: {path}")
    return path


def main():
    parser = argparse.ArgumentParser(
        description='Minority Report — Gesture-based cursor control',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--config', type=str, help='Config YAML file')
    parser.add_argument('--calibrate', action='store_true', help='Run calibration')
    parser.add_argument('--no-preview', action='store_true', help='Headless mode')
    parser.add_argument('--create-config', action='store_true', help='Create default config')
    parser.add_argument('--camera', type=int, default=0, help='Camera index')
    parser.add_argument('--version', action='version', version='Minority Report 2.0.0')

    args = parser.parse_args()

    if args.create_config:
        create_default_config()
        return 0

    if args.calibrate:
        try:
            from calibration import run_calibration_tool
            success = run_calibration_tool(camera_index=args.camera)
            return 0 if success else 1
        except Exception as e:
            print(f"Calibration error: {e}")
            return 1

    try:
        from main import HandControlApp
        app = HandControlApp(config_path=args.config, preview=not args.no_preview)
        app.run()
        return 0
    except KeyboardInterrupt:
        return 0
    except ImportError as e:
        print(f"Import error: {e}\nInstall dependencies: pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
