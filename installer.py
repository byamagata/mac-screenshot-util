#!/usr/bin/env python3
"""
Installer script for Screenshot Utility
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

APP_NAME = "Screenshot Utility"
APP_IDENTIFIER = "com.user.screenshotutil"
SERVICE_PLIST_NAME = f"{APP_IDENTIFIER}.plist"

def get_app_path():
    """Get the path to the application bundle if it exists"""
    # Look in standard locations
    app_path = f"/Applications/{APP_NAME}.app"
    user_app_path = os.path.expanduser(f"~/Applications/{APP_NAME}.app")
    
    if os.path.exists(app_path):
        return app_path
    elif os.path.exists(user_app_path):
        return user_app_path
    else:
        # Check if we have a dist directory with the app
        dist_app_path = f"dist/{APP_NAME}.app"
        if os.path.exists(dist_app_path):
            return os.path.abspath(dist_app_path)
    
    return None

def install_application():
    """Install the application to Applications folder"""
    # Check if we have a packaged app
    dist_app_path = f"dist/{APP_NAME}.app"
    
    if not os.path.exists(dist_app_path):
        print("Application bundle not found. Creating one...")
        try:
            subprocess.run([sys.executable, "package.py"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error packaging application: {e}")
            return False
    
    # Copy to Applications folder
    app_path = f"/Applications/{APP_NAME}.app"
    
    try:
        # Remove existing app if it exists
        if os.path.exists(app_path):
            print(f"Removing existing installation at {app_path}")
            shutil.rmtree(app_path)
        
        # Copy the app
        print(f"Copying app to {app_path}")
        shutil.copytree(dist_app_path, app_path)
        
        print(f"Application installed successfully to {app_path}")
        return True
    except Exception as e:
        print(f"Error installing application: {e}")
        return False

def install_launch_agent():
    """Install the launch agent for auto-start"""
    app_path = get_app_path()
    
    if not app_path:
        print("Application not found. Please install the application first.")
        return False
    
    try:
        # Create the LaunchAgents directory if it doesn't exist
        launch_agents_dir = os.path.expanduser("~/Library/LaunchAgents")
        os.makedirs(launch_agents_dir, exist_ok=True)
        
        # Get the executable path inside the app bundle
        executable_path = f"{app_path}/Contents/MacOS/{APP_NAME.replace(' ', '')}"
        
        # Create the plist content
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{APP_IDENTIFIER}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{executable_path}</string>
        <string>--service</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    <key>ProcessType</key>
    <string>Interactive</string>
    <key>ThrottleInterval</key>
    <integer>5</integer>
</dict>
</plist>
"""
        
        # Write the plist file
        plist_path = os.path.join(launch_agents_dir, SERVICE_PLIST_NAME)
        with open(plist_path, "w") as f:
            f.write(plist_content)
        
        # Load the launch agent
        subprocess.run(["launchctl", "load", plist_path], check=True)
        
        print(f"Launch agent installed at {plist_path}")
        print("The application will now start automatically at login")
        return True
    except Exception as e:
        print(f"Error installing launch agent: {e}")
        return False

def remove_launch_agent():
    """Remove the launch agent"""
    try:
        # Get the path to the plist file
        plist_path = os.path.expanduser(f"~/Library/LaunchAgents/{SERVICE_PLIST_NAME}")
        
        # Check if it exists
        if not os.path.exists(plist_path):
            print("Launch agent not found. Nothing to remove.")
            return True
        
        # Unload the launch agent
        subprocess.run(["launchctl", "unload", plist_path], check=True)
        
        # Remove the plist file
        os.remove(plist_path)
        
        print(f"Launch agent removed from {plist_path}")
        print("The application will no longer start automatically at login")
        return True
    except Exception as e:
        print(f"Error removing launch agent: {e}")
        return False

def uninstall_application():
    """Uninstall the application"""
    # Remove launch agent first
    remove_launch_agent()
    
    # Get the app path
    app_path = get_app_path()
    
    if not app_path:
        print("Application not found. Nothing to uninstall.")
        return True
    
    try:
        # Remove the application bundle
        print(f"Removing application from {app_path}")
        shutil.rmtree(app_path)
        
        # Remove preferences
        prefs_path = os.path.expanduser("~/.screenshot_util_preferences.json")
        if os.path.exists(prefs_path):
            os.remove(prefs_path)
            print(f"Removed preferences file {prefs_path}")
        
        print("Application uninstalled successfully")
        return True
    except Exception as e:
        print(f"Error uninstalling application: {e}")
        return False

def show_menu():
    """Show the installer menu"""
    while True:
        print("\n==== Screenshot Utility Installer ====")
        print("1. Install Application")
        print("2. Enable Auto-Launch at Login")
        print("3. Disable Auto-Launch at Login")
        print("4. Uninstall Application")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == "1":
            install_application()
        elif choice == "2":
            install_launch_agent()
        elif choice == "3":
            remove_launch_agent()
        elif choice == "4":
            uninstall_application()
        elif choice == "5":
            print("Exiting installer")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "install":
            install_application()
            install_launch_agent()
        elif command == "uninstall":
            uninstall_application()
        elif command == "enable-autostart":
            install_launch_agent()
        elif command == "disable-autostart":
            remove_launch_agent()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: install, uninstall, enable-autostart, disable-autostart")
    else:
        # No arguments, show interactive menu
        show_menu()