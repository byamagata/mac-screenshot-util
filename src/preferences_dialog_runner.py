#!/usr/bin/env python3
import sys
import os
import json
from PyQt6.QtWidgets import QApplication
from src.preferences_dialog import PreferencesDialog

def main():
    # Load preferences
    preferences_path = os.path.expanduser("~/.screenshot_util_preferences.json")
    preferences = {}
    
    try:
        if os.path.exists(preferences_path):
            with open(preferences_path, "r") as f:
                preferences = json.load(f)
    except Exception as e:
        print(f"Error loading preferences: {e}")
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Create and show preferences dialog
    dialog = PreferencesDialog(preferences=preferences)
    result = dialog.exec()
    
    # Save preferences if dialog was accepted
    if result == 1:  # QDialog::Accepted
        new_preferences = dialog.get_preferences()
        try:
            with open(preferences_path, "w") as f:
                json.dump(new_preferences, f, indent=4)
            print("Preferences saved successfully")
            print(json.dumps(new_preferences))
        except Exception as e:
            print(f"Error saving preferences: {e}")

if __name__ == "__main__":
    main()
