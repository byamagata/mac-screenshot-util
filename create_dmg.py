#!/usr/bin/env python3
"""
Script to create a DMG file from the Screenshot Utility app
"""
import os
import sys
import subprocess

APP_NAME = "Screenshot Utility"

def create_dmg():
    """Create a DMG file from the app bundle"""
    try:
        # Make sure we're in the project directory
        project_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(project_dir)
        
        # Check if app exists
        app_path = f"dist/{APP_NAME}.app"
        if not os.path.exists(app_path):
            print(f"Error: {app_path} does not exist. Run package.py first.")
            return False
        
        # Check if create-dmg is installed
        try:
            subprocess.run(["which", "create-dmg"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("create-dmg not found. Installing with Homebrew...")
            try:
                subprocess.run(["brew", "install", "create-dmg"], check=True)
            except subprocess.CalledProcessError:
                print("Error installing create-dmg. Make sure Homebrew is installed.")
                return False
        
        # Create the DMG
        print(f"Creating DMG for {APP_NAME}...")
        dmg_name = f"{APP_NAME.replace(' ', '-')}.dmg"
        
        cmd = [
            "create-dmg",
            "--volname", APP_NAME,
            "--window-pos", "200", "120",
            "--window-size", "800", "400",
            "--icon-size", "100",
            "--icon", f"{APP_NAME}.app", "200", "190",
            "--hide-extension", f"{APP_NAME}.app",
            "--app-drop-link", "600", "185",
            dmg_name,
            app_path
        ]
        
        subprocess.run(cmd, check=True)
        
        if os.path.exists(dmg_name):
            print(f"DMG created successfully: {dmg_name}")
            return True
        else:
            print("DMG creation failed.")
            return False
        
    except Exception as e:
        print(f"Error creating DMG: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    create_dmg()