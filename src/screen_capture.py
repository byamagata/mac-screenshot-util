#!/usr/bin/env python3
"""
Screen Capture Overlay Module for selecting screen regions
"""
import sys
import os
import time
import io
import tempfile
import pyautogui
import subprocess
from PIL import Image
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtGui import QPainter, QPen, QColor, QGuiApplication, QScreen, QPixmap
from PyQt6.QtCore import Qt, QPoint, QRect, QTimer, QSize, QBuffer, QByteArray
from PyQt6.QtCore import Qt, QPoint, QRect
import platform

class ScreenCaptureOverlay(QWidget):
    """Transparent overlay for selecting screen regions to capture"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        
        # Initialize variables
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.is_capturing = False
        self.status_text = "Click and drag to select a region. Press ESC to cancel."
        
        # For macOS, we need to handle screen capture differently
        self.is_macos = sys.platform == "darwin"
        
        # Configure widget for capture
        # Important: For macOS we need different flags than for other platforms
        if self.is_macos:
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint | 
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.Tool  # macOS-specific flag
            )
        else:
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint | 
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.BypassWindowManagerHint
            )
            
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Get information about all available screens
        self.screens = QGuiApplication.screens()
        self.screen_geometries = []
        self.total_geometry = QRect()
        
        # Find combined geometry of all screens
        for screen in self.screens:
            geometry = screen.geometry()
            self.screen_geometries.append(geometry)
            self.total_geometry = self.total_geometry.united(geometry)
        
        self.screen_geometry = self.total_geometry
        print(f"Total detected screen geometry: {self.total_geometry.width()}x{self.total_geometry.height()}")
        
        # Store background screenshot for macOS workaround
        self.background_image = None
    
    def start_capture(self):
        """Begin the screen capture process"""
        # Take a full-screen screenshot BEFORE showing our overlay
        # This is crucial so we can see the actual screen content
        self.background_image = None
        try:
            print("Taking full screenshot of all screens...")
            # Try different methods to capture screenshot
            if self.is_macos:
                # First attempt: use macOS native screencapture
                print("Attempting macOS native screenshot...")
                self.background_image = self.take_full_screenshot()
                
                # If that fails, try PyQt
                if not self.background_image:
                    print("Native screenshot failed, trying PyQt method...")
                    try:
                        self.background_image = self.take_pyqt_screenshot()
                        if self.background_image:
                            print(f"PyQt screenshot captured: {self.background_image.width}x{self.background_image.height}")
                    except Exception as e:
                        print(f"PyQt screenshot method failed: {e}")
                        
                # If that also fails, try pyautogui
                if not self.background_image:
                    print("PyQt screenshot failed, trying pyautogui...")
                    try:
                        self.background_image = pyautogui.screenshot()
                        if self.background_image:
                            print(f"PyAutoGUI screenshot captured: {self.background_image.width}x{self.background_image.height}")
                    except Exception as e:
                        print(f"PyAutoGUI screenshot failed: {e}")
            else:
                # For other platforms try PyQt first, then pyautogui
                try:
                    self.background_image = self.take_pyqt_screenshot()
                    if self.background_image:
                        print(f"PyQt screenshot captured: {self.background_image.width}x{self.background_image.height}")
                except Exception:
                    print("PyQt screenshot failed, falling back to PyAutoGUI")
                    
                # Fallback to PyAutoGUI if PyQt fails
                if not self.background_image:
                    self.background_image = pyautogui.screenshot()
                    if self.background_image:
                        print(f"PyAutoGUI screenshot captured: {self.background_image.width}x{self.background_image.height}")
            
            # Final check - if we still don't have a background image, abort
            if not self.background_image:
                print("All screenshot methods failed")
                self.parent_app.show()
                self.parent_app.on_capture_complete(None)
                return
                
        except Exception as e:
            print(f"Error capturing background: {e}")
            import traceback
            traceback.print_exc()
            self.parent_app.show()
            self.parent_app.on_capture_complete(None)
            return
        
        # Update screen information in case setup changed
        self.screens = QGuiApplication.screens()
        self.screen_geometries = []
        self.total_geometry = QRect()
        
        # Find combined geometry of all screens
        for screen in self.screens:
            geometry = screen.geometry()
            self.screen_geometries.append(geometry)
            self.total_geometry = self.total_geometry.united(geometry)
        
        self.screen_geometry = self.total_geometry
        print(f"Updated screen geometry: {self.screen_geometry.width()}x{self.screen_geometry.height()}")
        
        # Reset selection points
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.is_capturing = False
        
        # Prepare window
        if self.is_macos:
            # For macOS, we need special handling
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint | 
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.Tool
            )
        else:
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint | 
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.BypassWindowManagerHint
            )
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(self.screen_geometry)
        self.setMouseTracking(True)
        
        # Show the overlay - but differently based on platform
        if self.is_macos:
            # On macOS, avoid showFullScreen as it can capture only itself
            print("Using non-fullscreen mode for macOS")
            self.setWindowOpacity(0.5)  # More transparent on macOS
            self.show()
            # Special flag for macOS to keep window on top of all screens
            try:
                self.windowHandle().setLevel(5)  # Qt.WindowStaysOnTopHint level
            except Exception as e:
                print(f"Failed to set window level: {e}")
        else:
            # Use full screen for other platforms
            print("Using fullscreen mode for non-macOS")
            self.showFullScreen()
        
        # Make sure window is visible and active
        self.raise_()
        self.activateWindow() 
        self.setCursor(Qt.CursorShape.CrossCursor)
        
        # Process events to ensure window is shown properly
        QApplication.processEvents()
        
        # Force the window to be active and on top
        QTimer.singleShot(100, lambda: self.activateWindow())
        QTimer.singleShot(100, lambda: self.raise_())
    
    def take_full_screenshot(self):
        """Take a full screenshot of all screens using macOS native command"""
        try:
            # Create a temporary file
            temp_file = f"/tmp/screenshot_temp_{int(time.time())}.png"
            print(f"Taking full screenshot to temp file: {temp_file}")
            
            # Use macOS native screencapture command
            # Use -x flag to disable sound
            # Use -C flag to capture cursor
            command = ['screencapture', '-x', temp_file]
            print(f"Running command: {' '.join(command)}")
            
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            
            if result.returncode != 0:
                print(f"screencapture failed with return code {result.returncode}")
                print(f"stderr: {result.stderr}")
                print(f"stdout: {result.stdout}")
                return None
                
            # Check if file exists
            if not os.path.exists(temp_file):
                print(f"Screenshot file not created: {temp_file}")
                return None
                
            # Get file size
            file_size = os.path.getsize(temp_file)
            print(f"Screenshot file created: {temp_file}, size: {file_size} bytes")
            
            if file_size == 0:
                print("Screenshot file is empty")
                return None
                
            # Open the image file
            try:
                img = Image.open(temp_file)
                img.load()  # Make sure the image data is loaded
                print(f"Screenshot loaded as PIL Image: {img.width}x{img.height}, mode: {img.mode}")
                
                # Keep a copy for debugging
                debug_file = f"/tmp/screenshot_debug_{int(time.time())}.png"
                img.save(debug_file)
                print(f"Debug copy saved to: {debug_file}")
                
            except Exception as e:
                print(f"Error loading screenshot file: {e}")
                import traceback
                traceback.print_exc()
                return None
            
            # Clean up the temp file
            try:
                os.remove(temp_file)
                print(f"Temporary file {temp_file} removed")
            except Exception as e:
                print(f"Failed to remove temp file: {e}")
                
            return img
        except Exception as e:
            print(f"Error taking full screenshot: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def paintEvent(self, event):
        """Handle paint events to draw selection rectangle"""
        painter = QPainter(self)
        
        # Draw darker semi-transparent overlay (increased opacity to 150)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 150))
        
        # Draw instruction text at the top
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        font = painter.font()
        font.setPointSize(16)  # Larger text
        font.setBold(True)  # Make text bold
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        text_rect = self.rect()
        text_rect.setHeight(70)  # Larger text area
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.status_text)
        
        # Draw selection rectangle if we're capturing
        if self.is_capturing and not self.start_point.isNull() and not self.end_point.isNull():
            selection_rect = QRect(self.start_point, self.end_point).normalized()
            
            # Clear the selected area to make it transparent
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(selection_rect, Qt.GlobalColor.white)
            
            # Draw selection rectangle border with a more visible blue color
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            pen = QPen(QColor(0, 174, 255), 3)  # Thicker border
            painter.setPen(pen)
            painter.drawRect(selection_rect)
            
            # Draw corner markers to make them more visible
            corner_size = 6
            corner_color = QColor(0, 174, 255)
            
            # Draw corner squares at each corner - using integers to avoid type errors
            painter.fillRect(QRect(int(selection_rect.topLeft().x() - corner_size/2), 
                                  int(selection_rect.topLeft().y() - corner_size/2), 
                                  corner_size, corner_size), corner_color)
            
            painter.fillRect(QRect(int(selection_rect.topRight().x() - corner_size/2), 
                                  int(selection_rect.topRight().y() - corner_size/2), 
                                  corner_size, corner_size), corner_color)
            
            painter.fillRect(QRect(int(selection_rect.bottomLeft().x() - corner_size/2), 
                                  int(selection_rect.bottomLeft().y() - corner_size/2), 
                                  corner_size, corner_size), corner_color)
            
            painter.fillRect(QRect(int(selection_rect.bottomRight().x() - corner_size/2), 
                                  int(selection_rect.bottomRight().y() - corner_size/2), 
                                  corner_size, corner_size), corner_color)
            
            # Draw dimensions of selection
            width = selection_rect.width()
            height = selection_rect.height()
            dimension_text = f"{width} × {height}"
            
            # Position the text at the bottom right of the selection
            text_x = selection_rect.right() - 90
            text_y = selection_rect.bottom() + 25
            
            # Create a background for the text
            text_rect = QRect(text_x - 5, text_y - 20, 100, 30)
            painter.fillRect(text_rect, QColor(0, 0, 0, 220))
            
            # Draw the text
            painter.setPen(QColor(255, 255, 255))
            font = painter.font()
            font.setPointSize(12)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(text_x, text_y, dimension_text)
    
    def mousePressEvent(self, event):
        """Handle mouse press events to start selection"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.is_capturing = True
            self.status_text = "Release mouse to capture"
            self.update()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events to update selection"""
        if self.is_capturing:
            self.end_point = event.pos()
            self.update()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events to complete selection"""
        if event.button() == Qt.MouseButton.LeftButton and self.is_capturing:
            self.end_point = event.pos()
            self.is_capturing = False
            
            # Take the screenshot
            self.take_screenshot()
            self.hide()
    
    def keyPressEvent(self, event):
        """Handle key press events to cancel capture"""
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            # Make sure to properly clean up
            QApplication.processEvents()
            self.parent_app.on_capture_complete(None)
    
    def take_screenshot(self):
        """Capture the selected region of the screen using the pre-captured background image"""
        # Get the normalized rectangle coordinates in widget space
        rect = QRect(self.start_point, self.end_point).normalized()
        
        # Ensure we have a valid selection
        if rect.width() < 10 or rect.height() < 10:
            print("Selection too small")
            self.parent_app.on_capture_complete(None)
            return
        
        # Update status to provide feedback
        self.status_text = "Processing screenshot..."
        self.update()
        QApplication.processEvents()  # Make sure update is visible
        
        # We need to hide the overlay
        self.hide()
        QApplication.processEvents()  # Ensure window is hidden
        
        # Use special shortcut method for macOS
        if self.is_macos:
            # Try to take a new screenshot of the specific region directly
            # This can work better than cropping from a full screenshot
            print("Attempting direct region capture with macOS native method")
            try:
                # Convert widget coordinates to screen coordinates
                start_global = self.mapToGlobal(rect.topLeft())
                end_global = self.mapToGlobal(rect.bottomRight())
                
                global_rect = QRect(start_global, end_global).normalized()
                global_x = global_rect.x()
                global_y = global_rect.y()
                global_width = global_rect.width()
                global_height = global_rect.height()
                
                # Ensure coordinates are positive
                if global_width > 10 and global_height > 10:
                    # Use screencapture directly
                    temp_file = f"/tmp/direct_region_{int(time.time())}.png"
                    print(f"Running screencapture for region {global_x},{global_y},{global_width},{global_height}")
                    result = subprocess.run(
                        ['screencapture', '-x', '-R', f"{global_x},{global_y},{global_width},{global_height}", temp_file],
                        capture_output=True, check=False
                    )
                    
                    if result.returncode == 0 and os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                        try:
                            # Load the image
                            direct_img = Image.open(temp_file)
                            direct_img.load()  # Force load
                            os.unlink(temp_file)  # Clean up
                            
                            print(f"Direct region capture successful: {direct_img.width}x{direct_img.height}")
                            # Save a debug copy
                            debug_file = f"/tmp/direct_region_capture_{int(time.time())}.png"
                            direct_img.save(debug_file)
                            
                            # Send to parent
                            self.parent_app.on_capture_complete(direct_img)
                            return
                        except Exception as e:
                            print(f"Error loading direct region capture: {e}")
                    else:
                        print("Direct region capture failed or produced empty file")
            except Exception as e:
                print(f"Error with direct region capture: {e}")
                import traceback
                traceback.print_exc()
                
        # Fallback: Use the background image we already captured
        if self.background_image:
            try:
                # Convert widget coordinates to screen coordinates
                start_global = self.mapToGlobal(rect.topLeft())
                end_global = self.mapToGlobal(rect.bottomRight())
                
                global_rect = QRect(start_global, end_global).normalized()
                global_x = global_rect.x()
                global_y = global_rect.y()
                global_width = global_rect.width()
                global_height = global_rect.height()
                
                print(f"Raw global coordinates: x={global_x}, y={global_y}, width={global_width}, height={global_height}")
                
                # Handle negative coordinates (can happen with multiple monitors)
                if global_x < 0 or global_y < 0:
                    print("Detected negative coordinates, adjusting...")
                    # Adjust the coordinates if they are negative
                    if global_x < 0:
                        global_width += global_x  # Reduce width by the negative amount
                        global_x = 0
                    if global_y < 0:
                        global_height += global_y  # Reduce height by the negative amount
                        global_y = 0
                
                print(f"Adjusted coordinates for cropping: x={global_x}, y={global_y}, width={global_width}, height={global_height}")
                
                # Make sure we have positive width and height
                if global_width <= 0 or global_height <= 0:
                    print("Invalid dimensions after adjustment")
                    self.parent_app.on_capture_complete(None)
                    return
            except Exception as e:
                print(f"Error processing coordinates: {e}")
                import traceback
                traceback.print_exc()
                self.parent_app.on_capture_complete(None)
                return
            
            try:
                # Create a cropped version from our background image
                # Ensure coordinates are within image bounds
                img_width, img_height = self.background_image.size
                
                # Clamp coordinates to image bounds
                x1 = max(0, min(global_x, img_width - 1))
                y1 = max(0, min(global_y, img_height - 1))
                x2 = max(0, min(global_x + global_width, img_width))
                y2 = max(0, min(global_y + global_height, img_height))
                
                print(f"Cropping bounds: ({x1}, {y1}, {x2}, {y2}) from image size: {img_width}x{img_height}")
                
                if x2 <= x1 or y2 <= y1:
                    print("Invalid crop dimensions")
                    self.parent_app.on_capture_complete(None)
                    return
                
                try:
                    # Crop from the background image
                    cropped = self.background_image.crop((x1, y1, x2, y2))
                    
                    # Check if we need to convert the image format
                    if cropped.mode not in ['RGB', 'RGBA']:
                        print(f"Converting image from {cropped.mode} to RGBA")
                        cropped = cropped.convert('RGBA')
                    
                    print(f"Crop successful: {cropped.width}x{cropped.height}, mode: {cropped.mode}")
                    
                    # Send the cropped image to the parent
                    self.parent_app.on_capture_complete(cropped)
                except Exception as e:
                    import traceback
                    print(f"Error cropping image: {e}")
                    traceback.print_exc()
                    self.parent_app.on_capture_complete(None)
                return
            except Exception as e:
                print(f"Error cropping background image: {e}")
        
        # If we reach here, something went wrong with the background image approach
        # Fall back to taking a fresh screenshot
        print("Fallback to direct screenshot capture...")
        self._take_direct_screenshot(global_x, global_y, global_width, global_height)
    
    def take_pyqt_screenshot(self):
        """Take a full screenshot using PyQt's native screen capture abilities.
        
        This method attempts to capture all screens using PyQt's screen capture
        capabilities and combines them into a single PIL Image. If capturing
        multiple screens fails, it falls back to capturing just the primary screen.
        
        Returns:
            PIL.Image: The combined screenshot image of all screens, or None if capture fails
        """
        try:
            print("Starting PyQt screenshot capture")
            # We'll capture each screen separately and then combine them
            combined_image = None
            
            # Get all screens
            screens = QGuiApplication.screens()
            print(f"Found {len(screens)} screens")
            
            for i, screen in enumerate(screens):
                try:
                    print(f"Capturing screen {i+1}/{len(screens)}")
                    # Get screen geometry and logical DPI
                    geometry = screen.geometry()
                    dpi = screen.logicalDotsPerInch()
                    print(f"Screen {i+1} geometry: {geometry.x()},{geometry.y()} {geometry.width()}x{geometry.height()}, DPI: {dpi}")
                    
                    # Capture the screen - 0 = entire desktop
                    pixmap = screen.grabWindow(0)
                    
                    if pixmap.isNull():
                        print(f"Screen {i+1} capture returned null pixmap")
                        continue
                        
                    print(f"Screen {i+1} capture successful: {pixmap.width()}x{pixmap.height()}")
                    
                    # Save the pixmap to a temporary file
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                    temp_file.close()
                    pixmap.save(temp_file.name, 'PNG')
                    
                    # Open with PIL
                    screen_img = Image.open(temp_file.name)
                    os.unlink(temp_file.name)
                    
                    print(f"Converted to PIL Image: {screen_img.width}x{screen_img.height}")
                    
                    # If this is our first screen, just use it as the base
                    if combined_image is None:
                        combined_image = Image.new('RGB', (self.total_geometry.width(), self.total_geometry.height()), (0, 0, 0))
                        print(f"Created combined image: {combined_image.width}x{combined_image.height}")
                    
                    # Paste this screen at the correct position in the combined image
                    # Convert from screen coordinates to combined image coordinates
                    x = geometry.x() - self.total_geometry.x()
                    y = geometry.y() - self.total_geometry.y()
                    print(f"Pasting screen {i+1} at position {x},{y}")
                    combined_image.paste(screen_img, (x, y))
                    
                except Exception as e:
                    print(f"Error capturing screen {i+1}: {e}")
                    import traceback
                    traceback.print_exc()
            
            if combined_image:
                # Save a debug copy of the combined image
                debug_file = f"/tmp/combined_screenshot_{int(time.time())}.png"
                combined_image.save(debug_file)
                print(f"Saved combined screenshot to {debug_file}")
                return combined_image
            
            # If we couldn't create a combined image but have at least one screen, try a different approach
            print("Falling back to alternative PyQt screenshot method")
            # Try getting just the main screen
            screen = QGuiApplication.primaryScreen()
            if not screen:
                print("No primary screen found")
                return None
                
            # Try capturing the entire desktop
            pixmap = QGuiApplication.primaryScreen().grabWindow(0)
            if pixmap.isNull():
                print("Primary screen capture returned null pixmap")
                return None
                
            # Save to temporary file to avoid conversion issues
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            temp_file.close()
            pixmap.save(temp_file.name, 'PNG')
            
            # Load with PIL
            img = Image.open(temp_file.name)
            os.unlink(temp_file.name)
            
            print(f"Alternative PyQt screenshot successful: {img.width}x{img.height}")
            
            # Save a debug copy
            debug_file = f"/tmp/alternative_screenshot_{int(time.time())}.png"
            img.save(debug_file)
            print(f"Saved alternative screenshot to {debug_file}")
            
            return img
        except Exception as e:
            print(f"PyQt screenshot failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _take_direct_screenshot(self, x, y, width, height):
        """Take a direct screenshot of a specific region as a fallback method.
        
        Attempts multiple screenshot methods in order of preference:
        1. macOS native screencapture command (if on macOS)
        2. PyAutoGUI screenshot
        3. Crop from existing background image
        4. PyQt screenshot
        
        Args:
            x: The x-coordinate of the region to capture
            y: The y-coordinate of the region to capture
            width: The width of the region to capture
            height: The height of the region to capture
            
        Returns:
            None. Instead, it passes the captured screenshot (or None if failed)
            to the parent application via on_capture_complete.
        """
        print(f"Taking direct screenshot of region: {x},{y},{width},{height}")
        
        # Try multiple methods to get the screenshot
        screenshot = None
        
        try:
            # Method 1: For macOS, try using the native screencapture command
            if self.is_macos:
                print("Trying macOS native screencapture for region...")
                temp_file = f"/tmp/screenshot_region_{int(time.time())}.png"
                command = ['screencapture', '-x', '-R', f"{x},{y},{width},{height}", temp_file]
                print(f"Running command: {' '.join(command)}")
                
                result = subprocess.run(command, capture_output=True, text=True, check=False)
                
                if result.returncode == 0 and os.path.exists(temp_file):
                    file_size = os.path.getsize(temp_file)
                    print(f"Region screenshot file created: {temp_file}, size: {file_size} bytes")
                    
                    if file_size > 0:
                        try:
                            img = Image.open(temp_file)
                            img.load()  # Make sure the image data is loaded
                            print(f"Region screenshot loaded: {img.width}x{img.height}, mode: {img.mode}")
                            screenshot = img
                        except Exception as e:
                            print(f"Error loading region screenshot: {e}")
                    
                    # Clean up
                    try:
                        os.remove(temp_file)
                    except Exception as e:
                        print(f"Failed to remove temp file: {e}")
                else:
                    print(f"screencapture region command failed: {result.stderr}")
        except Exception as e:
            print(f"macOS screencapture method failed: {e}")
            import traceback
            traceback.print_exc()
                    
        # Method 2: Try PyAutoGUI if screencapture failed
        if screenshot is None:
            try:
                print("Trying PyAutoGUI for region screenshot...")
                screenshot = pyautogui.screenshot(region=(x, y, width, height))
                if screenshot:
                    print(f"PyAutoGUI region screenshot captured: {screenshot.width}x{screenshot.height}")
            except Exception as e:
                print(f"PyAutoGUI region screenshot failed: {e}")
                import traceback
                traceback.print_exc()
        
        # Method 3: Try cropping from the full screenshot we already have
        if screenshot is None and self.background_image:
            try:
                print("Trying to crop from existing background image...")
                x1 = max(0, min(x, self.background_image.width - 1))
                y1 = max(0, min(y, self.background_image.height - 1))
                x2 = max(0, min(x + width, self.background_image.width))
                y2 = max(0, min(y + height, self.background_image.height))
                
                if x2 > x1 and y2 > y1:
                    screenshot = self.background_image.crop((x1, y1, x2, y2))
                    print(f"Cropped from background: {screenshot.width}x{screenshot.height}")
            except Exception as e:
                print(f"Crop from background failed: {e}")
        
        # Method 4: Try using PyQt's screenshot capability
        if screenshot is None:
            try:
                print("Trying PyQt screenshot method...")
                # Get the screen that contains the selected region
                for screen in QGuiApplication.screens():
                    screen_geom = screen.geometry()
                    # Check if our region is at least partially on this screen
                    if (x < screen_geom.x() + screen_geom.width() and 
                        x + width > screen_geom.x() and
                        y < screen_geom.y() + screen_geom.height() and
                        y + height > screen_geom.y()):
                        
                        # Calculate screen-relative coordinates
                        rel_x = max(0, x - screen_geom.x())
                        rel_y = max(0, y - screen_geom.y())
                        rel_width = min(width, screen_geom.width() - rel_x)
                        rel_height = min(height, screen_geom.height() - rel_y)
                        
                        print(f"Using screen with geometry: {screen_geom.x()},{screen_geom.y()} {screen_geom.width()}x{screen_geom.height()}")
                        print(f"Relative coordinates: {rel_x},{rel_y} {rel_width}x{rel_height}")
                        
                        # Grab the screen
                        pixmap = screen.grabWindow(0)
                        if not pixmap.isNull():
                            # Crop to our region
                            cropped_pixmap = pixmap.copy(rel_x, rel_y, rel_width, rel_height)
                            if not cropped_pixmap.isNull():
                                # Convert to PIL Image
                                temp_path = tempfile.mktemp(suffix='.png')
                                cropped_pixmap.save(temp_path, 'PNG')
                                screenshot = Image.open(temp_path)
                                os.unlink(temp_path)
                                print(f"PyQt screenshot successful: {screenshot.width}x{screenshot.height}")
                                break
            except Exception as e:
                print(f"PyQt screenshot method failed: {e}")
                import traceback
                traceback.print_exc()
                
        # Send the result (or None if all methods failed)
        if screenshot and hasattr(screenshot, 'width') and hasattr(screenshot, 'height'):
            if screenshot.width > 0 and screenshot.height > 0:
                # Save a debug copy
                try:
                    debug_file = f"/tmp/screenshot_region_debug_{int(time.time())}.png"
                    screenshot.save(debug_file)
                    print(f"Debug region saved to: {debug_file}")
                except Exception as e:
                    print(f"Failed to save debug region: {e}")
                
                self.parent_app.on_capture_complete(screenshot)
                return
                
        print("All region screenshot methods failed")
        self.parent_app.on_capture_complete(None)