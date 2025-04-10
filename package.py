#!/usr/bin/env python3
"""
Script to package the Screenshot Utility as a macOS application
"""
import os
import sys
import shutil
import subprocess
from setuptools import setup

APP_NAME = "Screenshot Utility"
APP_VERSION = "2.0.0"
APP_AUTHOR = "Your Name"
APP_ICON = "appicon.icns"  # Place an icon file in the project root or specify path

def create_app_bundle():
    """Create a macOS .app bundle"""
    try:
        # Make sure we're in the project directory
        project_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(project_dir)
        
        print(f"Packaging {APP_NAME} as a macOS application...")
        
        # Check if we have py2app installed
        try:
            import py2app
        except ImportError:
            print("Installing py2app...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "py2app"])
        
        # Clean build directories if they exist
        if os.path.exists("build"):
            shutil.rmtree("build")
        if os.path.exists("dist"):
            shutil.rmtree("dist")
        
        # First, create a setup.py configuration for py2app
        setup_options = {
            'argv_emulation': True,
            'plist': {
                'CFBundleName': APP_NAME,
                'CFBundleDisplayName': APP_NAME,
                'CFBundleGetInfoString': f"{APP_NAME} {APP_VERSION}",
                'CFBundleIdentifier': f"com.{APP_AUTHOR.lower().replace(' ', '')}.screenshotutil",
                'CFBundleVersion': APP_VERSION,
                'CFBundleShortVersionString': APP_VERSION,
                'NSHumanReadableCopyright': f"© {APP_AUTHOR}",
                'NSRequiresAquaSystemAppearance': False,  # Support dark mode
                'NSCameraUsageDescription': "This app requires camera access for screen recording.",
                'NSMicrophoneUsageDescription': "This app requires microphone access for screen recording.",
                'NSAppleEventsUsageDescription': "This app requires permission to control other apps for screen recording.",
                'LSUIElement': True,  # App is an agent (menu bar app without dock icon)
            },
            'packages': ['rumps', 'PyQt6', 'PIL', 'pynput'],
            'includes': ['src'],
            'resources': [],
        }
        
        # If app icon exists, add it
        if os.path.exists(APP_ICON):
            setup_options['iconfile'] = APP_ICON
        
        # Run py2app
        sys.argv = [sys.argv[0], 'py2app']
        setup(
            name=APP_NAME,
            app=['run.py'],
            version=APP_VERSION,
            options={'py2app': setup_options},
            setup_requires=['py2app'],
        )
        
        print(f"App bundle created at: dist/{APP_NAME}.app")
        
        # Add run with service flag
        app_exec_path = f"dist/{APP_NAME}.app/Contents/MacOS/{APP_NAME.replace(' ', '')}"
        if os.path.exists(app_exec_path):
            # Read existing file
            with open(app_exec_path, 'r') as f:
                content = f.read()
            
            # Add service flag if it doesn't already have it
            if "--service" not in content:
                content = content.replace("if __name__ == '__main__':", "if __name__ == '__main__':\n    sys.argv.append('--service')")
                
                # Write updated file
                with open(app_exec_path, 'w') as f:
                    f.write(content)
                
                print("Updated executable to run in service mode")
        
        print("Packaging completed successfully!")
        print(f"To run the app, open dist/{APP_NAME}.app")
        
        return True
    except Exception as e:
        print(f"Error packaging app: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    create_app_bundle()