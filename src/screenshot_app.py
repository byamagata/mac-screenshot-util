#!/usr/bin/env python3
"""
Main Screenshot Application module
"""
from PyQt6.QtWidgets import (
    QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, 
    QWidget, QLabel, QApplication, QMessageBox
)
from PyQt6.QtGui import QKeySequence, QShortcut
import sys
import pyautogui
from PyQt6.QtCore import Qt, QTimer
from src.screen_capture import ScreenCaptureOverlay
from src.annotation_window import AnnotationWindow

class ScreenshotApp(QMainWindow):
    """Main application window for the screenshot utility"""
    
    def __init__(self, shortcut_key=None):
        super().__init__()
        self.shortcut_key = shortcut_key
        self.setWindowTitle("Screenshot Utility")
        self.setMinimumSize(300, 200)
        self.statusBar().showMessage("Ready", 3000)
        
        # Setup UI
        self.setup_ui()
        
        # Setup shortcuts
        self.setup_shortcuts()
        
        # Initialize components
        self.screen_capture = ScreenCaptureOverlay(self)
        self.annotation_window = None
        
    def setup_ui(self):
        """Set up the main window UI elements"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Title label
        title_label = QLabel("Screenshot Utility")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Capture button - update label to show current shortcut if available
        if self.shortcut_key:
            shortcut_display = self.shortcut_key.replace("Ctrl", "⌘" if sys.platform == "darwin" else "Ctrl")
            self.capture_button = QPushButton(f"Capture Screenshot ({shortcut_display})")
        else:
            self.capture_button = QPushButton("Capture Screenshot")
        self.capture_button.clicked.connect(self.start_capture)
        main_layout.addWidget(self.capture_button)
        
        # Button layout
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)
        
        # Help text
        help_text = QLabel("Capture a region of your screen, annotate, and copy to clipboard.")
        help_text.setWordWrap(True)
        help_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(help_text)
        
    def setup_shortcuts(self):
        """Set up keyboard shortcuts"""
        # Use the configurable shortcut if provided
        if self.shortcut_key:
            self.capture_shortcut = QShortcut(QKeySequence(self.shortcut_key), self)
            self.capture_shortcut.activated.connect(self.start_capture)
        
    def start_capture(self):
        """Start the screen capture process"""
        self.hide()  # Hide main window during capture
        
        # Use a slightly longer delay for multi-monitor setups
        # This ensures the application is fully hidden before capture starts
        QTimer.singleShot(300, self._delayed_capture)
    
    def _delayed_capture(self):
        """Start capture after a delay to ensure main window is hidden"""
        # Process any pending events to ensure window is fully hidden
        QApplication.processEvents()
        
        try:
            # For macOS, we might need to check permissions first
            if sys.platform == "darwin":
                # Try a small test screenshot to ensure permissions are granted
                test_screenshot = pyautogui.screenshot(region=(0, 0, 1, 1))
                if test_screenshot:
                    print("Screenshot permissions appear to be granted")
        except Exception as e:
            print(f"Permission check failed: {e}")
            # Show a message about permissions
            QMessageBox.warning(
                self, 
                "Permission Required", 
                "Please grant screen recording permission for this application in System Preferences > Security & Privacy > Privacy > Screen Recording"
            )
            self.show()
            return
            
        # Initialize the screen capture window, which will now handle
        # the multi-monitor setup correctly
        self.screen_capture.start_capture()
        
    def on_capture_complete(self, screenshot):
        """Handle completed screenshot capture"""
        self.show()  # Show main window after capture
        
        if screenshot:
            try:
                # Add debug info about the screenshot
                print(f"Received screenshot for annotation: {type(screenshot)}")
                if hasattr(screenshot, 'width') and hasattr(screenshot, 'height'):
                    print(f"Screenshot dimensions: {screenshot.width}x{screenshot.height}")
                elif hasattr(screenshot, 'size'):
                    print(f"Screenshot size: {screenshot.size()}")
                else:
                    print("Screenshot has no readable dimensions")
                    
                # Ensure it's a PIL Image
                from PIL import Image
                if not isinstance(screenshot, Image.Image):
                    print("Converting screenshot to PIL Image...")
                    if hasattr(screenshot, 'toImage'):
                        qimg = screenshot.toImage()
                        # Convert QImage to PIL Image
                        from PyQt6.QtGui import QImage
                        buffer = qimg.bits().asstring(qimg.sizeInBytes())
                        screenshot = Image.frombuffer("RGBA", (qimg.width(), qimg.height()), buffer, "raw", "RGBA", 0, 1)
                    else:
                        print("Cannot convert screenshot to PIL Image - unknown type")
                
                print(f"Creating annotation window with screenshot: {screenshot}")
                self.annotation_window = AnnotationWindow(screenshot, self)
                self.annotation_window.show()
                
                # Flash the button to indicate success
                original_stylesheet = self.capture_button.styleSheet()
                self.capture_button.setStyleSheet("background-color: #4CAF50; color: white;")
                
                # Use a single-shot timer to revert the style after a brief delay
                QTimer.singleShot(500, lambda: self.capture_button.setStyleSheet(original_stylesheet))
                
            except Exception as e:
                # If there's an error with annotation window
                print(f"Error opening annotation window: {e}")
                import traceback
                traceback.print_exc()
                QMessageBox.warning(self, "Error", f"Failed to open screenshot: {str(e)}")
        else:
            # Indicate canceled or failed capture
            print("\n=== SCREENSHOT FAILED OR CANCELED ===")
            # Print a stack trace to show where the failure happened
            import traceback
            traceback.print_stack()
            print("=== END OF ERROR TRACE ===\n")
            self.statusBar().showMessage("Screenshot canceled or failed", 3000)
        
    def closeEvent(self, event):
        """Handle window close event"""
        # Clean up any resources
        if self.annotation_window:
            self.annotation_window.close()
        event.accept()