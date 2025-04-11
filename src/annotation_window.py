#!/usr/bin/env python3
"""
Annotation Window Module for annotating captured screenshots
"""
import pyperclip
from PIL import Image
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QToolBar, QColorDialog, QFileDialog, QMessageBox
)
from PyQt6.QtGui import (
    QPixmap, QPainter, QPen, QColor, QIcon, QImage, QAction
)
from PyQt6.QtCore import Qt, QPoint, QSize

class DrawingArea(QWidget):
    """Widget for drawing annotations on screenshots"""
    
    def __init__(self, screenshot, parent=None):
        super().__init__(parent)
        self.screenshot = screenshot
        
        print(f"Drawing area initializing with screenshot type: {type(screenshot)}")
        
        # Convert PIL Image to QPixmap
        try:
            # Ensure we have an RGB or RGBA mode image
            if screenshot.mode not in ['RGB', 'RGBA']:
                print(f"Converting image from {screenshot.mode} to RGBA")
                img = screenshot.convert("RGBA")
            else:
                img = screenshot
                
            print(f"PIL Image size: {img.width}x{img.height}, mode: {img.mode}")
            
            # Get raw image data for conversion to QImage
            img_data = img.tobytes("raw", "RGBA")
            
            # Create QImage with correct stride
            qimg = QImage(img_data, img.width, img.height, img.width * 4, QImage.Format.Format_RGBA8888)
            if qimg.isNull():
                print("QImage is null after conversion")
            else:
                print(f"QImage created: {qimg.width()}x{qimg.height()}")
                
            # Convert to QPixmap for drawing
            self.pixmap = QPixmap.fromImage(qimg)
            if self.pixmap.isNull():
                print("QPixmap is null after conversion from QImage")
            else:
                print(f"QPixmap created: {self.pixmap.width()}x{self.pixmap.height()}")
        except Exception as e:
            import traceback
            print(f"Error converting screenshot to QPixmap: {e}")
            traceback.print_exc()
            # Create a fallback empty pixmap as a last resort
            self.pixmap = QPixmap(400, 300)
            self.pixmap.fill(QColor(255, 255, 255))
            print("Created fallback empty pixmap")
            
        # Initialize drawing properties
        self.last_point = QPoint()
        self.drawing = False
        self.preview_pixmap = None  # For temporary drawing preview
        self.pen_color = QColor(255, 0, 0)  # Default: Red
        self.pen_width = 2
        self.tool = "pen"  # Default tool
        self.start_point = QPoint()  # For shape tools
        self.current_point = QPoint()  # For tracking current mouse position
        
        # History for undo/redo
        self.history = [self.pixmap.copy()]
        self.history_index = 0
        
        # Set fixed size based on screenshot
        print(f"Setting drawing area size to: {self.pixmap.width()}x{self.pixmap.height()}")
        self.setFixedSize(self.pixmap.size())
    
    def set_tool(self, tool):
        """Set the current drawing tool"""
        self.tool = tool
    
    def set_pen_color(self, color):
        """Set the pen color"""
        self.pen_color = color
    
    def set_pen_width(self, width):
        """Set the pen width"""
        self.pen_width = width
    
    def paintEvent(self, event):
        """Handle paint events to draw the image and annotations"""
        painter = QPainter(self)
        
        # Draw the base image with annotations
        painter.drawPixmap(0, 0, self.pixmap)
        
        # If we're drawing a shape, draw the preview on top
        if self.drawing and self.tool != "pen" and not self.start_point.isNull() and not self.current_point.isNull():
            # Create a temporary painter on the widget (not the pixmap)
            pen = QPen(self.pen_color, self.pen_width, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            pen.setStyle(Qt.PenStyle.DashLine)  # Use dashed line for preview
            painter.setPen(pen)
            
            # Draw preview based on current tool
            if self.tool == "line":
                painter.drawLine(self.start_point, self.current_point)
            elif self.tool == "rectangle":
                x = min(self.start_point.x(), self.current_point.x())
                y = min(self.start_point.y(), self.current_point.y())
                width = abs(self.start_point.x() - self.current_point.x())
                height = abs(self.start_point.y() - self.current_point.y())
                painter.drawRect(x, y, width, height)
            elif self.tool == "arrow":
                # Draw line part of arrow
                painter.drawLine(self.start_point, self.current_point)
                
                # Calculate arrow head
                arrow_length = 20
                dx = self.current_point.x() - self.start_point.x()
                dy = self.current_point.y() - self.start_point.y()
                
                # Normalize
                length = (dx**2 + dy**2)**0.5
                if length > 0:  # Avoid division by zero
                    dx /= length
                    dy /= length
                    
                    # Calculate arrow head points
                    p1 = QPoint(
                        int(self.current_point.x() - arrow_length * (dx * 0.866 + dy * 0.5)),
                        int(self.current_point.y() - arrow_length * (dy * 0.866 - dx * 0.5))
                    )
                    
                    p2 = QPoint(
                        int(self.current_point.x() - arrow_length * (dx * 0.866 - dy * 0.5)),
                        int(self.current_point.y() - arrow_length * (dy * 0.866 + dx * 0.5))
                    )
                    
                    # Draw arrow head
                    painter.drawLine(self.current_point, p1)
                    painter.drawLine(self.current_point, p2)
    
    def mousePressEvent(self, event):
        """Handle mouse press events to start drawing"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.last_point = event.pos()
            self.drawing = True
            
            # Store start position for all tools
            self.start_point = event.pos()
            self.current_point = event.pos()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for drawing"""
        if event.buttons() & Qt.MouseButton.LeftButton and self.drawing:
            self.current_point = event.pos()
            
            # For pen tool, draw directly to the pixmap
            if self.tool == "pen":
                self._draw_line_to(event.pos())
            else:
                # For shape tools, just update to show the preview
                self.update()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events to complete drawing"""
        if event.button() == Qt.MouseButton.LeftButton and self.drawing:
            if self.tool == "pen":
                self._draw_line_to(event.pos())
            elif self.tool == "line":
                self._draw_line(self.start_point, event.pos())
            elif self.tool == "arrow":
                self._draw_arrow(self.start_point, event.pos())
            elif self.tool == "rectangle":
                self._draw_rectangle(self.start_point, event.pos())
            
            self.drawing = False
            
            # Add to history for undo/redo
            self._add_to_history()
    
    def _draw_line_to(self, end_point):
        """Draw a line from last point to current point"""
        painter = QPainter(self.pixmap)
        pen = QPen(self.pen_color, self.pen_width, Qt.PenStyle.SolidLine, 
                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(self.last_point, end_point)
        
        # Update last point
        self.last_point = end_point
        self.update()
    
    def _draw_line(self, start_point, end_point):
        """Draw a straight line from start to end"""
        painter = QPainter(self.pixmap)
        pen = QPen(self.pen_color, self.pen_width, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(start_point, end_point)
        self.update()
    
    def _draw_arrow(self, start_point, end_point):
        """Draw an arrow from start to end"""
        painter = QPainter(self.pixmap)
        pen = QPen(self.pen_color, self.pen_width, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        # Draw the line
        painter.drawLine(start_point, end_point)
        
        # Calculate arrow head
        angle = 0.5  # 30 degrees in radians
        arrow_length = 20
        
        # Calculate direction vector
        dx = end_point.x() - start_point.x()
        dy = end_point.y() - start_point.y()
        
        # Normalize
        length = (dx**2 + dy**2)**0.5
        if length == 0:
            return
        
        dx /= length
        dy /= length
        
        # Calculate arrow head points
        p1 = QPoint(
            int(end_point.x() - arrow_length * (dx * 0.866 + dy * 0.5)),
            int(end_point.y() - arrow_length * (dy * 0.866 - dx * 0.5))
        )
        
        p2 = QPoint(
            int(end_point.x() - arrow_length * (dx * 0.866 - dy * 0.5)),
            int(end_point.y() - arrow_length * (dy * 0.866 + dx * 0.5))
        )
        
        # Draw arrow head
        painter.drawLine(end_point, p1)
        painter.drawLine(end_point, p2)
        
        self.update()
    
    def _draw_rectangle(self, start_point, end_point):
        """Draw a rectangle from start to end"""
        painter = QPainter(self.pixmap)
        pen = QPen(self.pen_color, self.pen_width, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        # Calculate rectangle
        x = min(start_point.x(), end_point.x())
        y = min(start_point.y(), end_point.y())
        width = abs(start_point.x() - end_point.x())
        height = abs(start_point.y() - end_point.y())
        
        painter.drawRect(x, y, width, height)
        self.update()
    
    def _add_to_history(self):
        """Add current state to history for undo/redo functionality.
        
        Updates the history list by:
        1. Removing any forward history beyond the current index
        2. Adding the current pixmap state to history
        3. Limiting history size to maximum 20 items to conserve memory
        """
        # Remove any forward history
        while len(self.history) > self.history_index + 1:
            self.history.pop()
        
        # Add current state
        self.history.append(self.pixmap.copy())
        self.history_index += 1
        
        # Limit history size
        if len(self.history) > 20:
            self.history.pop(0)
            self.history_index -= 1
    
    def undo(self):
        """Undo the last drawing action"""
        if self.history_index > 0:
            self.history_index -= 1
            self.pixmap = self.history[self.history_index].copy()
            self.update()
    
    def redo(self):
        """Redo a previously undone action"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.pixmap = self.history[self.history_index].copy()
            self.update()
    
    def get_image(self):
        """Get the image with annotations as a QPixmap"""
        return self.pixmap.copy()


class AnnotationWindow(QMainWindow):
    """Window for annotating and editing screenshots"""
    
    def __init__(self, screenshot, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.screenshot = screenshot
        
        self.setWindowTitle("Screenshot Annotation")
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the annotation window UI"""
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create drawing area
        self.drawing_area = DrawingArea(self.screenshot)
        main_layout.addWidget(self.drawing_area)
        
        # Setup toolbar
        self.setup_toolbar()
        
        # Button layout
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)
        
        # Copy to clipboard button
        copy_button = QPushButton("Copy to Clipboard")
        copy_button.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(copy_button)
        
        # Save button
        save_button = QPushButton("Save As...")
        save_button.clicked.connect(self.save_image)
        button_layout.addWidget(save_button)
        
        # Resize window to fit screenshot with toolbar
        self.adjustSize()
    
    def setup_toolbar(self):
        """Set up the annotation toolbar"""
        toolbar = QToolBar("Annotation Tools")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        # Pen tool
        pen_action = QAction("Pen", self)
        pen_action.triggered.connect(lambda: self.drawing_area.set_tool("pen"))
        toolbar.addAction(pen_action)
        
        # Line tool
        line_action = QAction("Line", self)
        line_action.triggered.connect(lambda: self.drawing_area.set_tool("line"))
        toolbar.addAction(line_action)
        
        # Arrow tool
        arrow_action = QAction("Arrow", self)
        arrow_action.triggered.connect(lambda: self.drawing_area.set_tool("arrow"))
        toolbar.addAction(arrow_action)
        
        # Rectangle tool
        rect_action = QAction("Rectangle", self)
        rect_action.triggered.connect(lambda: self.drawing_area.set_tool("rectangle"))
        toolbar.addAction(rect_action)
        
        toolbar.addSeparator()
        
        # Color picker
        color_action = QAction("Color", self)
        color_action.triggered.connect(self.choose_color)
        toolbar.addAction(color_action)
        
        toolbar.addSeparator()
        
        # Undo action
        undo_action = QAction("Undo", self)
        undo_action.triggered.connect(self.drawing_area.undo)
        toolbar.addAction(undo_action)
        
        # Redo action
        redo_action = QAction("Redo", self)
        redo_action.triggered.connect(self.drawing_area.redo)
        toolbar.addAction(redo_action)
    
    def choose_color(self):
        """Open color picker dialog"""
        color = QColorDialog.getColor(self.drawing_area.pen_color, self, "Choose Pen Color")
        if color.isValid():
            self.drawing_area.set_pen_color(color)
    
    def copy_to_clipboard(self):
        """Copy screenshot with annotations to clipboard"""
        # Get image with annotations
        pixmap = self.drawing_area.get_image()
        
        # Convert QPixmap to QImage
        image = pixmap.toImage()
        
        # Copy to clipboard
        QApplication.clipboard().setImage(image)
        
        # Show confirmation
        QMessageBox.information(self, "Success", "Screenshot copied to clipboard")
    
    def save_image(self):
        """Save screenshot with annotations to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Screenshot", "", "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg)"
        )
        
        if file_path:
            # Get image with annotations
            pixmap = self.drawing_area.get_image()
            
            # Save to file
            pixmap.save(file_path)
            
            # Show confirmation
            QMessageBox.information(self, "Success", f"Screenshot saved to {file_path}")
    
    def closeEvent(self, event):
        """Handle window close event.
        
        Notifies the parent application that this window is being closed
        and accepts the close event.
        
        Args:
            event: The QCloseEvent triggered when closing the window
        """
        # Inform parent the annotation window is closed
        if self.parent_app:
            self.parent_app.annotation_window = None
        event.accept()