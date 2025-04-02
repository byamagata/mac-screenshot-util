#!/usr/bin/env python3
"""
Runner script for the Screenshot Utility
"""
import sys
import argparse
from PyQt6.QtWidgets import QApplication
from src.screenshot_app import ScreenshotApp

def main():
    """Main application entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='macOS Screenshot Utility')
    parser.add_argument('--shortcut', default='Ctrl+Shift+5', 
                        help='Keyboard shortcut for capturing screenshots (default: Ctrl+Shift+5)')
    args = parser.parse_args()
    
    # Start application
    app = QApplication(sys.argv)
    screenshot_app = ScreenshotApp(shortcut_key=args.shortcut)
    screenshot_app.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()