#!/usr/bin/env python3
"""
macOS Screenshot Utility - Main Application
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
    parser.add_argument('--service', action='store_true',
                        help='Run as background service with menu bar icon')
    args = parser.parse_args()
    
    # Start application
    if args.service:
        # If running as service, use the new service-based code
        from src.service_app import run_service
        run_service()
    else:
        # Default UI mode
        app = QApplication(sys.argv)
        screenshot_app = ScreenshotApp(shortcut_key=args.shortcut)
        screenshot_app.show()
        sys.exit(app.exec())

if __name__ == "__main__":
    main()