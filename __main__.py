"""
HandControl CLI entry point
Supports: python -m handcontrol [--calibrate] [--no-preview] [--config CONFIG_PATH]
"""
import sys
import argparse
import os
from pathlib import Path

def create_default_config():
    """Create default config.yaml file"""
    from config import Config
    
    config = Config()
    config_path = "config.yaml"
    config.save_to_file(config_path)
    print(f"📄 Created default configuration: {config_path}")
    return config_path

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='HandControl - Gesture-based cursor control',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m handcontrol                    # Run with default settings
  python -m handcontrol --no-preview      # Run without camera preview
  python -m handcontrol --calibrate       # Run calibration tool
  python -m handcontrol --config my.yaml  # Use custom config file
  python -m handcontrol --create-config   # Create default config.yaml
        """
    )
    
    parser.add_argument(
        '--config', 
        type=str, 
        help='Path to configuration YAML file'
    )
    
    parser.add_argument(
        '--calibrate', 
        action='store_true', 
        help='Run 4-corner screen calibration tool'
    )
    
    parser.add_argument(
        '--no-preview', 
        action='store_true', 
        help='Run without camera preview (headless mode)'
    )
    
    parser.add_argument(
        '--create-config', 
        action='store_true', 
        help='Create default config.yaml file and exit'
    )
    
    parser.add_argument(
        '--camera', 
        type=int, 
        default=0, 
        help='Camera device index (default: 0)'
    )
    
    parser.add_argument(
        '--version', 
        action='version', 
        version='HandControl 1.0.0'
    )
    
    args = parser.parse_args()
    
    # Handle create-config option
    if args.create_config:
        create_default_config()
        return 0
    
    # Handle calibration mode
    if args.calibrate:
        print("🎯 Starting HandControl Calibration Tool")
        
        try:
            from calibration import run_calibration_tool
            success = run_calibration_tool(camera_index=args.camera)
            
            if success:
                print("\n✅ Calibration completed successfully!")
                print("You can now run HandControl with improved accuracy.")
                return 0
            else:
                print("\n❌ Calibration failed or was cancelled.")
                return 1
                
        except ImportError as e:
            print(f"❌ Calibration tool not available: {e}")
            print("Make sure all dependencies are installed.")
            return 1
        except Exception as e:
            print(f"❌ Calibration error: {e}")
            return 1
    
    # Handle normal operation mode
    try:
        print("🎮 Starting HandControl...")
        
        # Check for config file
        config_path = args.config
        if config_path and not os.path.exists(config_path):
            print(f"❌ Configuration file not found: {config_path}")
            print("Use --create-config to create a default configuration.")
            return 1
        
        # Import and run main application
        from main import HandControlApp
        
        app = HandControlApp(
            config_path=config_path,
            preview=not args.no_preview
        )
        
        print("🚀 HandControl running! Use Ctrl+C to quit.")
        app.run()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n👋 HandControl stopped by user.")
        return 0
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"❌ Runtime error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())