#!/usr/bin/env python3
"""
Hotkey Settings Dialog for Screenshot Utility
"""
import sys
import json
import re
import os
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QMessageBox, QFormLayout
)
from PyQt6.QtCore import Qt

class HotkeyDialog(QDialog):
    """Dialog window for configuring screenshot hotkey settings.
    
    This dialog allows the user to set and save a custom hotkey combination
    for triggering the screenshot tool, consisting of modifier keys 
    (Command, Shift, Control, Option) and a single character key.
    """
    
    def __init__(self, config_path):
        """Initialize the hotkey settings dialog.
        
        Args:
            config_path: The path to the JSON preferences file
        """
        super().__init__()
        self.config_path = config_path
        self.setWindowTitle("Screenshot Hotkey Settings")
        self.setMinimumWidth(400)
        self.setMinimumHeight(200)
        
        # Load settings
        with open(config_path, 'r') as f:
            self.preferences = json.load(f)
        
        hotkey_config = self.preferences.get("hotkey", {"key": "4", "modifiers": ["command", "shift"]})
        
        # Setup UI
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Configure Screenshot Hotkey")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)
        
        # Form layout for modifiers and key
        form_layout = QFormLayout()
        layout.addLayout(form_layout)
        
        # Modifiers section
        modifiers_layout = QVBoxLayout()
        self.cmd_checkbox = QCheckBox("⌘ Command")
        self.shift_checkbox = QCheckBox("⇧ Shift")
        self.ctrl_checkbox = QCheckBox("⌃ Control")
        self.option_checkbox = QCheckBox("⌥ Option")
        
        # Set current values
        modifiers = hotkey_config.get("modifiers", [])
        self.cmd_checkbox.setChecked("command" in modifiers)
        self.shift_checkbox.setChecked("shift" in modifiers)
        self.ctrl_checkbox.setChecked("control" in modifiers)
        self.option_checkbox.setChecked("option" in modifiers)
        
        modifiers_layout.addWidget(self.cmd_checkbox)
        modifiers_layout.addWidget(self.shift_checkbox)
        modifiers_layout.addWidget(self.ctrl_checkbox)
        modifiers_layout.addWidget(self.option_checkbox)
        
        form_layout.addRow("Modifiers:", modifiers_layout)
        
        # Key input
        key_layout = QHBoxLayout()
        self.key_input = QLineEdit()
        self.key_input.setMaxLength(3)  # Allow f10, f11, f12
        self.key_input.setFixedWidth(50)
        current_key = hotkey_config.get("key", "4")
        self.key_input.setText(current_key)
        
        key_layout.addWidget(self.key_input)
        key_layout.addStretch(1)
        
        form_layout.addRow("Key:", key_layout)
        
        # Help text
        help_label = QLabel("Enter a single letter, number, or function key (e.g. 'a', '5', 'f1')")
        help_label.setStyleSheet("color: #666;")
        layout.addWidget(help_label)
        
        # Button layout
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        button_layout.addStretch(1)
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        # Save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_hotkey)
        button_layout.addWidget(save_button)
    
    def save_hotkey(self):
        """Save the hotkey configuration to the preferences file.
        
        Validates the user input for the key and modifier selections,
        updates the preferences with the new hotkey configuration, and
        writes the changes to the preferences file. Shows error messages
        if validation fails.
        
        Returns:
            None. Accepts the dialog if successful, otherwise remains open.
        """
        # Get the key from the input
        new_key = self.key_input.text().strip().lower()
        
        # Validate key is a single character or f1-f12
        if not (re.match(r'^[a-z0-9]$', new_key) or re.match(r'^f[1-9]$|^f1[0-2]$', new_key)):
            QMessageBox.critical(self, "Invalid Key", 
                               "Please enter a single letter, number, or function key (f1-f12)")
            return
        
        # Get modifiers
        modifiers = []
        if self.cmd_checkbox.isChecked():
            modifiers.append("command")
        if self.shift_checkbox.isChecked():
            modifiers.append("shift")
        if self.ctrl_checkbox.isChecked():
            modifiers.append("control")
        if self.option_checkbox.isChecked():
            modifiers.append("option")
        
        # Validate at least one modifier is selected
        if not modifiers:
            QMessageBox.critical(self, "Invalid Configuration", 
                              "Please select at least one modifier key")
            return
        
        # Update preferences
        self.preferences["hotkey"] = {
            "key": new_key,
            "modifiers": modifiers
        }
        
        # Save preferences
        with open(self.config_path, 'w') as f:
            json.dump(self.preferences, f, indent=4)
        
        self.accept()

def main():
    """Run the hotkey settings dialog"""
    if len(sys.argv) < 2:
        print("Error: Config path not provided")
        sys.exit(1)
        
    config_path = sys.argv[1]
    
    app = QApplication(sys.argv)
    dialog = HotkeyDialog(config_path)
    result = dialog.exec()
    
    # Return the result (1 for success, 0 for cancel)
    sys.exit(0 if result else 1)

if __name__ == "__main__":
    main()