#!/usr/bin/env python3
"""
Preferences Dialog Module for configuring Screenshot Utility
"""
import os
import json
import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QCheckBox, QFileDialog, QGroupBox,
    QFormLayout, QTabWidget, QWidget
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QKeySequenceEdit

class PreferencesDialog(QDialog):
    """Dialog for configuring Screenshot Utility preferences"""
    
    def __init__(self, parent=None, preferences=None):
        super().__init__(parent)
        self.preferences = preferences or {}
        
        self.setWindowTitle("Screenshot Utility Preferences")
        self.setMinimumWidth(400)
        
        # Setup UI
        self.setup_ui()
        
        # Load preferences to UI
        self.load_preferences_to_ui()
    
    def setup_ui(self):
        """Set up the preferences dialog UI"""
        layout = QVBoxLayout(self)
        
        # Create tabs
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # General tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        tab_widget.addTab(general_tab, "General")
        
        # Auto-launch settings
        auto_launch_group = QGroupBox("Startup")
        auto_launch_layout = QVBoxLayout(auto_launch_group)
        self.auto_launch_checkbox = QCheckBox("Launch at system startup")
        auto_launch_layout.addWidget(self.auto_launch_checkbox)
        general_layout.addWidget(auto_launch_group)
        
        # Save location
        save_group = QGroupBox("Save Settings")
        save_layout = QHBoxLayout(save_group)
        save_layout.addWidget(QLabel("Save Location:"))
        self.save_location_edit = QLineEdit()
        save_layout.addWidget(self.save_location_edit)
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_save_location)
        save_layout.addWidget(browse_button)
        general_layout.addWidget(save_group)
        
        # Hotkeys tab
        hotkeys_tab = QWidget()
        hotkeys_layout = QVBoxLayout(hotkeys_tab)
        tab_widget.addTab(hotkeys_tab, "Hotkeys")
        
        # Screenshot hotkey
        hotkeys_group = QGroupBox("Screenshot Hotkey")
        hotkeys_form = QFormLayout(hotkeys_group)
        
        # For system-wide hotkey, we need to use modifiers + key format
        hotkey_layout = QHBoxLayout()
        
        # Modifier checkboxes
        self.command_checkbox = QCheckBox("Command (⌘)")
        self.shift_checkbox = QCheckBox("Shift (⇧)")
        self.control_checkbox = QCheckBox("Control (⌃)")
        self.option_checkbox = QCheckBox("Option (⌥)")
        
        # Add checkboxes to layout
        modifiers_layout = QVBoxLayout()
        modifiers_layout.addWidget(self.command_checkbox)
        modifiers_layout.addWidget(self.shift_checkbox)
        modifiers_layout.addWidget(self.control_checkbox)
        modifiers_layout.addWidget(self.option_checkbox)
        
        hotkey_layout.addLayout(modifiers_layout)
        
        # Key dropdown
        self.key_dropdown = QComboBox()
        # Add common keys
        for key in "1234567890abcdefghijklmnopqrstuvwxyz":
            self.key_dropdown.addItem(key.upper(), key)
        
        # Add function keys
        for i in range(1, 13):
            self.key_dropdown.addItem(f"F{i}", f"f{i}")
        
        hotkey_layout.addWidget(self.key_dropdown)
        
        hotkeys_form.addRow("Capture Hotkey:", hotkey_layout)
        hotkeys_layout.addWidget(hotkeys_group)
        
        # Annotation tab
        annotation_tab = QWidget()
        annotation_layout = QVBoxLayout(annotation_tab)
        tab_widget.addTab(annotation_tab, "Annotation")
        
        # Default tool
        tool_group = QGroupBox("Default Tool")
        tool_layout = QVBoxLayout(tool_group)
        self.tool_dropdown = QComboBox()
        self.tool_dropdown.addItems(["Pen", "Line", "Arrow", "Rectangle"])
        tool_layout.addWidget(self.tool_dropdown)
        annotation_layout.addWidget(tool_group)
        
        # Default color (simplified for now)
        color_group = QGroupBox("Default Color")
        color_layout = QVBoxLayout(color_group)
        self.color_dropdown = QComboBox()
        self.color_dropdown.addItems(["Red", "Blue", "Green", "Yellow", "Black", "White"])
        color_layout.addWidget(self.color_dropdown)
        annotation_layout.addWidget(color_group)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        # Save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(save_button)
    
    def load_preferences_to_ui(self):
        """Load preferences data to UI elements"""
        # Auto launch
        self.auto_launch_checkbox.setChecked(self.preferences.get("auto_launch", True))
        
        # Save location
        self.save_location_edit.setText(self.preferences.get("save_location", "~/Screenshots"))
        
        # Hotkey
        hotkey_config = self.preferences.get("hotkey", {"key": "4", "modifiers": ["command", "shift"]})
        
        # Set modifiers
        self.command_checkbox.setChecked("command" in hotkey_config.get("modifiers", []))
        self.shift_checkbox.setChecked("shift" in hotkey_config.get("modifiers", []))
        self.control_checkbox.setChecked("control" in hotkey_config.get("modifiers", []))
        self.option_checkbox.setChecked("option" in hotkey_config.get("modifiers", []))
        
        # Set key
        key = hotkey_config.get("key", "4")
        index = self.key_dropdown.findData(key.lower())
        if index >= 0:
            self.key_dropdown.setCurrentIndex(index)
        
        # Default tool
        tool_index = self.tool_dropdown.findText(self.preferences.get("default_tool", "Pen"))
        if tool_index >= 0:
            self.tool_dropdown.setCurrentIndex(tool_index)
        
        # Default color
        color_index = self.color_dropdown.findText(self.preferences.get("default_color", "Red"))
        if color_index >= 0:
            self.color_dropdown.setCurrentIndex(color_index)
    
    def get_preferences(self):
        """Get preferences from UI elements"""
        # Create preferences dict
        preferences = {}
        
        # Auto launch
        preferences["auto_launch"] = self.auto_launch_checkbox.isChecked()
        
        # Save location
        preferences["save_location"] = self.save_location_edit.text()
        
        # Hotkey
        modifiers = []
        if self.command_checkbox.isChecked():
            modifiers.append("command")
        if self.shift_checkbox.isChecked():
            modifiers.append("shift")
        if self.control_checkbox.isChecked():
            modifiers.append("control")
        if self.option_checkbox.isChecked():
            modifiers.append("option")
        
        key = self.key_dropdown.currentData()
        preferences["hotkey"] = {
            "key": key,
            "modifiers": modifiers
        }
        
        # Default tool
        preferences["default_tool"] = self.tool_dropdown.currentText()
        
        # Default color
        preferences["default_color"] = self.color_dropdown.currentText()
        
        return preferences
    
    def browse_save_location(self):
        """Open folder browser to select save location"""
        current_location = os.path.expanduser(self.save_location_edit.text())
        
        # Open directory dialog
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Save Location",
            current_location,
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        
        if directory:
            # Convert to ~/path if in home directory
            home = os.path.expanduser("~")
            if directory.startswith(home):
                directory = "~" + directory[len(home):]
            
            self.save_location_edit.setText(directory)
    
    def accept(self):
        """Save preferences when dialog is accepted"""
        self.preferences = self.get_preferences()
        super().accept()