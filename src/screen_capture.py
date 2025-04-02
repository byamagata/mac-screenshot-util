#!/usr/bin/env python3
"""
Screen Capture Overlay Module for selecting screen regions
"""
import sys
import os
import time
import pyautogui
import subprocess
from PIL import Image
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtGui import QPainter, QPen, QColor, QGuiApplication, QScreen
from PyQt6.QtCore import Qt, QPoint, QRect, QTimer, QSize

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
        try:
            print("Taking full screenshot of all screens...")
            # Use different approach for macOS
            if self.is_macos:
                # On macOS, we'll take a screenshot before showing our overlay
                self.background_image = self.take_full_screenshot()
                if self.background_image:
                    print(f"Background image captured: {self.background_image.width}x{self.background_image.height}")
                else:
                    print("Failed to capture background image")
                    self.parent_app.on_capture_complete(None)
                    return
            else:
                # For other platforms this approach should work
                self.background_image = pyautogui.screenshot()
        except Exception as e:
            print(f"Error capturing background: {e}")
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
        
        # Show the overlay
        if self.is_macos:
            # On macOS, avoid showFullScreen as it can capture only itself
            self.show()
        else:
            self.showFullScreen()
        
        self.raise_()
        self.activateWindow()
        self.setCursor(Qt.CursorShape.CrossCursor)
        
        # Process events to ensure window is shown properly
        QApplication.processEvents()
        
        # Force the window to be active and on top
        self.activateWindow()
        self.raise_()
    
    def take_full_screenshot(self):
        """Take a full screenshot of all screens using macOS native command"""
        try:
            # Create a temporary file
            temp_file = f"/tmp/screenshot_temp_{int(time.time())}.png"
            
            # Use macOS native screencapture command
            result = subprocess.run(['screencapture', '-x', temp_file], 
                                 capture_output=True, text=True, check=False)
            
            if result.returncode != 0:
                print(f"screencapture failed: {result.stderr}")
                return None
                
            # Check if file exists
            if not os.path.exists(temp_file):
                print(f"Screenshot file not created: {temp_file}")
                return None
                
            # Open the image file
            img = Image.open(temp_file)
            
            # Clean up the temp file
            try:
                os.remove(temp_file)
            except:
                pass
                
            return img
        except Exception as e:
            print(f"Error taking full screenshot: {e}")
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
        
        # Use the background image we already captured
        if self.background_image:
            # Convert widget coordinates to screen coordinates
            start_global = self.mapToGlobal(rect.topLeft())
            end_global = self.mapToGlobal(rect.bottomRight())
            
            global_rect = QRect(start_global, end_global).normalized()
            global_x = global_rect.x()
            global_y = global_rect.y()
            global_width = global_rect.width()
            global_height = global_rect.height()
            
            print(f"Cropping from background image: x={global_x}, y={global_y}, width={global_width}, height={global_height}")
            
            try:
                # Create a cropped version from our background image
                cropped = self.background_image.crop((
                    global_x, 
                    global_y, 
                    global_x + global_width, 
                    global_y + global_height
                ))
                
                print(f"Crop successful: {cropped.width}x{cropped.height}")
                # Send the cropped image to the parent
                self.parent_app.on_capture_complete(cropped)
                return
            except Exception as e:
                print(f"Error cropping background image: {e}")
        
        # If we reach here, something went wrong with the background image approach
        # Fall back to taking a fresh screenshot
        print("Fallback to direct screenshot capture...")
        self._take_direct_screenshot(global_x, global_y, global_width, global_height)
    
    def _take_direct_screenshot(self, x, y, width, height):
        """Take a direct screenshot as a fallback method"""
        try:
            if self.is_macos:
                # For macOS, try using the native screencapture command
                temp_file = f"/tmp/screenshot_region_{int(time.time())}.png"
                result = subprocess.run(['screencapture', '-x', '-R', f"{x},{y},{width},{height}", temp_file], 
                                       capture_output=True, text=True, check=False)
                
                if result.returncode == 0 and os.path.exists(temp_file):
                    img = Image.open(temp_file)
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                    self.parent_app.on_capture_complete(img)
                    return
            
            # Try pyautogui as a last resort
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            if screenshot and screenshot.width > 0 and screenshot.height > 0:
                self.parent_app.on_capture_complete(screenshot)
            else:
                self.parent_app.on_capture_complete(None)
        except Exception as e:
            print(f"Direct screenshot error: {e}")
            self.parent_app.on_capture_complete(None)