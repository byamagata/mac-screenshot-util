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
        import os
        import fcntl
        
        # Use a reliable file lock mechanism to prevent multiple instances
        try:
            # Create a lock file in the user's home directory
            lock_file_path = os.path.expanduser("~/.screenshot_util.lock")
            lock_file = open(lock_file_path, 'w')
            
            # Try to acquire an exclusive lock (non-blocking)
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            # Write our PID to the lock file
            lock_file.write(str(os.getpid()))
            lock_file.flush()
            
            # If we reach this point, we got the lock and can continue
            # Keep the lock file open for the duration of the process
            
            # Set up a handler to release the lock on exit
            import atexit
            def cleanup_lock():
                try:
                    fcntl.flock(lock_file, fcntl.LOCK_UN)
                    lock_file.close()
                    os.remove(lock_file_path)
                except:
                    pass
            atexit.register(cleanup_lock)
            
            # If we got here, we have the lock and can start the service
            from src.service_app import run_service
            run_service()
            
        except IOError:
            # Failed to get the lock, which means another instance is running
            print("Another instance of Screenshot Utility is already running")
            print("Please quit the existing instance first")
            sys.exit(1)
        except Exception as e:
            print(f"Error setting up service: {e}")
            sys.exit(1)
    else:
        # Default UI mode
        app = QApplication(sys.argv)
        screenshot_app = ScreenshotApp(shortcut_key=args.shortcut)
        screenshot_app.show()
        sys.exit(app.exec())

if __name__ == "__main__":
    main()