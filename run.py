#!/usr/bin/env python3
"""
Runner script for the Screenshot Utility
"""
import sys
import argparse
import time
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import QTimer

def main():
    """Main application entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='macOS Screenshot Utility')
    parser.add_argument('--shortcut', default='Ctrl+Shift+5', 
                        help='Keyboard shortcut for capturing screenshots (default: Ctrl+Shift+5)')
    parser.add_argument('--service', action='store_true',
                        help='Run as background service with menu bar icon')
    parser.add_argument('--direct-capture', action='store_true',
                        help='Launch directly into capture mode without showing main window')
    args = parser.parse_args()
    
    # Start application
    if args.service:
        # If running as service, use the new service-based code
        from src.service_app import run_service
        run_service()
    elif args.direct_capture:
        # Direct capture mode - just show the screen capture overlay without the main window
        from src.screen_capture import ScreenCaptureOverlay
        from src.annotation_window import AnnotationWindow
        
        print("Starting direct capture mode...")
        
        app = QApplication(sys.argv)
        
        # Create a dummy parent class with the necessary on_capture_complete method
        # Make it inherit from QWidget so it can be used as a parent
        class DirectCaptureHandler(QWidget):
            def __init__(self):
                super().__init__()
                
            def on_capture_complete(self, screenshot):
                if screenshot:
                    try:
                        # Create annotation window
                        self.annotation_window = AnnotationWindow(screenshot, None)
                        self.annotation_window.show()
                    except Exception as e:
                        print(f"Error opening annotation window: {e}")
                        import traceback
                        traceback.print_exc()
                # Exit if no screenshot was captured (user canceled)
                else:
                    print("No screenshot captured, exiting")
                    # Use a timer to allow for clean shutdown
                    QTimer.singleShot(500, app.quit)
        
        # Create handler and overlay
        handler = DirectCaptureHandler()
        capture = ScreenCaptureOverlay(handler)
        
        # Wait a moment to make sure everything is initialized
        QTimer.singleShot(300, capture.start_capture)
        
        # Run the application
        sys.exit(app.exec())
    else:
        # Default UI mode
        from src.screenshot_app import ScreenshotApp
        app = QApplication(sys.argv)
        screenshot_app = ScreenshotApp(shortcut_key=args.shortcut)
        screenshot_app.show()
        sys.exit(app.exec())

if __name__ == "__main__":
    main()