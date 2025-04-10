#!/usr/bin/env python3
"""
macOS Screenshot Utility - Background Service Mode
"""
import os
import sys
import time
import json
import rumps
import threading
import tempfile
import subprocess
from pathlib import Path
from pynput import keyboard
from PyQt6.QtWidgets import QApplication
from src.screen_capture import ScreenCaptureOverlay
from src.screenshot_app import ScreenshotApp

# Default preferences
DEFAULT_PREFERENCES = {
    "hotkey": {"key": "4", "modifiers": ["command", "shift"]},
    "save_location": "~/Screenshots",
    "auto_launch": True
}

class HotkeyListener:
    """Global hotkey listener for triggering the screenshot utility"""
    
    def __init__(self, callback, preferences=None):
        self.callback = callback
        self.preferences = preferences or DEFAULT_PREFERENCES
        self.listener = None
        self.running = False
        self.hotkey = None
        
    def start(self):
        """Start listening for hotkeys"""
        if self.running:
            # If already running, stop first to ensure clean restart
            self.stop()
            
        # Safety delay to ensure previous listener is fully stopped
        time.sleep(0.1)
            
        self.running = True
        
        # Get hotkey configuration from preferences
        hotkey_config = self.preferences.get("hotkey", DEFAULT_PREFERENCES["hotkey"])
        hotkey_key = hotkey_config.get("key", "4")
        
        # Convert modifiers to pynput format
        modifiers = []
        modifier_names = []
        for mod in hotkey_config.get("modifiers", ["command", "shift"]):
            if mod == "command":
                modifiers.append(keyboard.Key.cmd)
                modifier_names.append("cmd")
            elif mod == "shift":
                modifiers.append(keyboard.Key.shift)
                modifier_names.append("shift")
            elif mod == "control":
                modifiers.append(keyboard.Key.ctrl)
                modifier_names.append("ctrl")
            elif mod == "option":
                modifiers.append(keyboard.Key.alt)
                modifier_names.append("alt")
        
        # Debug output
        print(f"Setting up hotkey with modifiers: {modifier_names} and key: {hotkey_key}")
        
        try:
            # Create a hotkey combination string
            hotkey_str = '+'.join([f'<{m.name}>' if hasattr(m, 'name') else str(m) for m in modifiers] + [hotkey_key])
            print(f"Hotkey string: {hotkey_str}")
            
            # Create hotkey combination
            self.hotkey = keyboard.HotKey(
                keyboard.HotKey.parse(hotkey_str),
                self.on_hotkey_activated
            )
            
            # Start the listener
            self.listener = keyboard.Listener(on_press=self.on_key_press, on_release=self.on_key_release)
            self.listener.start()
            print(f"Hotkey listener started with hotkey: {'+'.join(modifier_names + [hotkey_key])}")
        except Exception as e:
            print(f"Error setting up hotkey listener: {e}")
            import traceback
            traceback.print_exc()
            self.running = False
        
    def stop(self):
        """Stop listening for hotkeys"""
        if self.listener:
            try:
                self.listener.stop()
                # Wait for listener to fully stop
                if hasattr(self.listener, 'join'):
                    self.listener.join(0.5)
            except Exception as e:
                print(f"Error stopping listener: {e}")
            finally:
                self.listener = None
                self.running = False
                print("Hotkey listener stopped")
            
    def on_key_press(self, key):
        """Handle key press events"""
        if not self.hotkey:
            return
            
        try:
            # Pass to hotkey processor - using the key directly
            self.hotkey.press(key)
        except Exception as e:
            # Most errors here are normal (e.g. wrong key combinations)
            # so we don't need to print them all
            pass
            
    def on_key_release(self, key):
        """Handle key release events"""
        if not self.hotkey:
            return
            
        try:
            # Pass to hotkey processor - using the key directly
            self.hotkey.release(key)
        except Exception as e:
            # Most errors here are normal (e.g. wrong key combinations)
            # so we don't need to print them all
            pass
            
    def on_hotkey_activated(self):
        """Handle hotkey activation"""
        print("Hotkey activated!")
        self.callback()


class ScreenshotUtilService(rumps.App):
    """Menu bar application for the screenshot utility service"""
    
    # Class variable to track instances
    _instance_running = False
    
    @classmethod
    def is_instance_running(cls):
        return cls._instance_running
        
    def __init__(self):
        # Check if another instance is already running
        if ScreenshotUtilService._instance_running:
            print("ERROR: Another instance of ScreenshotUtilService is already running!")
            raise RuntimeError("Another instance of ScreenshotUtilService is already running!")
            
        # Mark as running
        ScreenshotUtilService._instance_running = True
            
        # Check if we have a custom icon, otherwise use emoji
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "menu_icon.png")
        icon = icon_path if os.path.exists(icon_path) else "📷"
        
        super().__init__("Screenshot", icon=icon, quit_button=None)
        
        # Initialize preferences
        self.preferences_path = os.path.expanduser("~/.screenshot_util_preferences.json")
        self.preferences = self.load_preferences()
        
        # Create the QApplication instance for Qt components
        # This is needed for the screenshot capture overlay
        self.qt_app = None
        self.qt_thread = None
        
        # Initialize hotkey listener
        self.hotkey_listener = HotkeyListener(self.take_screenshot, self.preferences)
        
        # Initialize screenshot components
        self.screen_capture = None
        self.annotation_window = None
        
        # Setup menu
        self.setup_menu()
        
        # Start the hotkey listener
        self.hotkey_listener.start()
        
        # Setup launch agent if auto launch is enabled
        if self.preferences.get("auto_launch", True):
            self.setup_launch_agent()
        
    def setup_menu(self):
        """Set up the menu bar menu"""
        # Take Screenshot menu item
        self.menu.add(rumps.MenuItem("Take Screenshot", callback=self.take_screenshot))
        
        # Preferences submenu
        prefs_menu = rumps.MenuItem("Preferences")
        
        # Hotkey settings
        hotkey_menu = rumps.MenuItem("Hotkey Settings", callback=self.open_hotkey_settings)
        prefs_menu.add(hotkey_menu)
        
        # Save location
        save_location_menu = rumps.MenuItem("Save Location", callback=self.set_save_location)
        prefs_menu.add(save_location_menu)
        
        # Auto launch
        auto_launch_status = "Enabled" if self.preferences.get("auto_launch", True) else "Disabled"
        self.auto_launch_menu = rumps.MenuItem(f"Auto Launch: {auto_launch_status}", callback=self.toggle_auto_launch)
        prefs_menu.add(self.auto_launch_menu)
        
        # Add preferences menu
        self.menu.add(prefs_menu)
        
        # About menu item
        self.menu.add(rumps.MenuItem("About", callback=self.show_about))
        
        # Add quit menu item manually (since we disabled the default one)
        self.menu.add(rumps.MenuItem("Quit", callback=self.quit_app))
    
    def take_screenshot(self, _=None):
        """Take a screenshot using the screen capture overlay"""
        print("Taking screenshot...")
        
        # We need to run the screenshot capture directly but without showing the main UI
        try:
            # Use direct subprocess call to run the screenshot command in direct capture mode
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "run.py")
            # Run in background with direct-capture flag
            subprocess.Popen([sys.executable, script_path, "--direct-capture"], 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE)
            
            # Show notification
            rumps.notification(
                title="Screenshot Utility",
                subtitle="",
                message="Select a region to capture",
                icon=None
            )
            
        except Exception as e:
            print(f"Error launching screenshot tool: {e}")
            import traceback
            traceback.print_exc()
            
            # Show error notification
            rumps.notification(
                title="Screenshot Error",
                subtitle="",
                message=f"Error launching screenshot tool: {str(e)}",
                icon=None
            )
    
    def initialize_qt_app(self):
        """Initialize the Qt application"""
        # Instead of running QApplication in a separate thread,
        # we'll create it on demand when needed for screenshot operations
        print("Initializing Qt application")
        if QApplication.instance() is None:
            # No QApplication exists, create one
            self.qt_app = QApplication(sys.argv)
        else:
            # Use existing QApplication
            self.qt_app = QApplication.instance()
        print("Qt application initialized")
    
    def on_capture_complete(self, screenshot):
        """Handle completed screenshot capture"""
        if screenshot:
            try:
                # Add debug info about the screenshot
                print(f"Received screenshot for annotation: {type(screenshot)}")
                
                # Create a temporary file to save the screenshot
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                temp_file.close()
                screenshot.save(temp_file.name)
                
                # Open the image with Preview app for now
                # In future this should use our own annotation window when Qt integration is better
                subprocess.run(['open', temp_file.name], check=True)
                
                # Show notification
                rumps.notification(
                    title="Screenshot Captured",
                    subtitle="",
                    message="Screenshot has been captured successfully",
                    icon=None
                )
                
            except Exception as e:
                print(f"Error processing screenshot: {e}")
                import traceback
                traceback.print_exc()
                
                # Show error notification
                rumps.notification(
                    title="Screenshot Error",
                    subtitle="",
                    message=f"Error processing screenshot: {str(e)}",
                    icon=None
                )
        else:
            # Indicate canceled or failed capture
            print("Screenshot was canceled or failed")
    
    def open_hotkey_settings(self, _):
        """Open dialog to configure hotkeys"""
        # For now, we'll simply show a message about how to configure settings
        # In a production app, we would need to create a separate preferences app
        # that can communicate with the menu bar service
        rumps.alert(
            title="Preferences",
            message="Preferences can be configured by editing ~/.screenshot_util_preferences.json\n\n"
                   "Current hotkey: Command+Shift+4\n\n"
                   "A dedicated preferences UI will be added in a future update.",
            ok="OK"
        )
        
        # The following is a simplistic implementation of toggling the hotkey
        # between Command+Shift+4 and Command+Shift+5
        try:
            current_hotkey = self.preferences.get("hotkey", {"key": "4", "modifiers": ["command", "shift"]})
            current_key = current_hotkey.get("key", "4")
            
            # Toggle between 4 and 5
            new_key = "5" if current_key == "4" else "4"
            
            # Update preferences
            self.preferences["hotkey"] = {
                "key": new_key,
                "modifiers": current_hotkey.get("modifiers", ["command", "shift"])
            }
            self.save_preferences()
            
            # Restart hotkey listener
            self.hotkey_listener.stop()
            self.hotkey_listener = HotkeyListener(self.take_screenshot, self.preferences)
            self.hotkey_listener.start()
            
            # Show confirmation
            rumps.notification(
                title="Hotkey Changed",
                subtitle="",
                message=f"Screenshot hotkey changed to Command+Shift+{new_key}",
                icon=None
            )
        except Exception as e:
            print(f"Error changing hotkey: {e}")
            import traceback
            traceback.print_exc()
    
    def set_save_location(self, _):
        """Set the default save location for screenshots"""
        current_location = self.preferences.get("save_location", "~/Screenshots")
        expanded_path = os.path.expanduser(current_location)
        
        # Show current location
        response = rumps.alert(
            title="Save Location",
            message=f"Current save location: {current_location}\n\n"
                   f"Would you like to use the default Screenshots folder?",
            ok="Use ~/Screenshots", 
            cancel="Keep Current"
        )
        
        if response:
            # Update to default location
            self.preferences["save_location"] = "~/Screenshots"
            self.save_preferences()
            
            # Ensure the directory exists
            screenshots_dir = os.path.expanduser("~/Screenshots")
            os.makedirs(screenshots_dir, exist_ok=True)
            
            # Show confirmation
            rumps.notification(
                title="Save Location Changed",
                subtitle="",
                message="Screenshots will be saved to ~/Screenshots",
                icon=None
            )
    
    def toggle_auto_launch(self, _):
        """Toggle auto launch at login"""
        current_setting = self.preferences.get("auto_launch", True)
        new_setting = not current_setting
        
        # Update preferences
        self.preferences["auto_launch"] = new_setting
        self.save_preferences()
        
        # Update menu item
        auto_launch_status = "Enabled" if new_setting else "Disabled"
        self.auto_launch_menu.title = f"Auto Launch: {auto_launch_status}"
        
        # Setup or remove launch agent
        if new_setting:
            self.setup_launch_agent()
        else:
            self.remove_launch_agent()
        
        # Show confirmation
        rumps.notification(
            title="Auto Launch Setting Changed",
            subtitle="",
            message=f"Auto launch at login: {auto_launch_status}",
            icon=None
        )
    
    def setup_launch_agent(self):
        """Set up launch agent for auto-launch at login"""
        try:
            # Get the path to the current script
            app_path = os.path.abspath(sys.argv[0])
            
            # Create the launch agent plist content
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.screenshotutil</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{app_path}</string>
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
            
            # Create the LaunchAgents directory if it doesn't exist
            launch_agents_dir = os.path.expanduser("~/Library/LaunchAgents")
            os.makedirs(launch_agents_dir, exist_ok=True)
            
            # Write the plist file
            plist_path = os.path.join(launch_agents_dir, "com.user.screenshotutil.plist")
            with open(plist_path, "w") as f:
                f.write(plist_content)
            
            # Load the launch agent
            subprocess.run(["launchctl", "load", plist_path], check=True)
            
            print(f"Launch agent created at {plist_path}")
            
        except Exception as e:
            print(f"Error setting up launch agent: {e}")
            import traceback
            traceback.print_exc()
    
    def remove_launch_agent(self):
        """Remove launch agent to disable auto-launch at login"""
        try:
            # Get the path to the plist file
            plist_path = os.path.expanduser("~/Library/LaunchAgents/com.user.screenshotutil.plist")
            
            # Unload the launch agent if it exists
            if os.path.exists(plist_path):
                subprocess.run(["launchctl", "unload", plist_path], check=True)
                
                # Remove the plist file
                os.remove(plist_path)
                
                print(f"Launch agent removed from {plist_path}")
            
        except Exception as e:
            print(f"Error removing launch agent: {e}")
            import traceback
            traceback.print_exc()
    
    def load_preferences(self):
        """Load preferences from file"""
        try:
            # Check if preferences file exists
            if os.path.exists(self.preferences_path):
                with open(self.preferences_path, "r") as f:
                    return json.load(f)
            # Return default preferences if file doesn't exist
            return DEFAULT_PREFERENCES.copy()
        except Exception as e:
            print(f"Error loading preferences: {e}")
            return DEFAULT_PREFERENCES.copy()
    
    def save_preferences(self):
        """Save preferences to file"""
        try:
            with open(self.preferences_path, "w") as f:
                json.dump(self.preferences, f, indent=4)
        except Exception as e:
            print(f"Error saving preferences: {e}")
    
    def show_about(self, _):
        """Show about dialog"""
        from src import __version__
        rumps.alert(
            title="About Screenshot Utility",
            message=f"A utility for capturing and annotating screenshots on macOS.\n\nVersion {__version__}",
            ok="OK"
        )
    
    def quit_app(self, _):
        """Quit the application"""
        print("Quitting application...")
        
        # Stop the hotkey listener
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        
        # Make sure any subprocesses are terminated
        try:
            # This is a stronger approach to ensure we exit
            # Find our own process group and terminate it
            pid = os.getpid()
            print(f"Terminating process ID: {pid}")
            
            # Kill all processes in our process group
            # This will also prevent the LaunchAgent from auto-restarting since we're cleanly exiting
            subprocess.run(["/usr/bin/pkill", "-f", "python.*screenshot-util"], 
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        except Exception as e:
            print(f"Error cleaning up processes: {e}")
        
        # Disable the LaunchAgent temporarily to prevent auto-restart
        try:
            launch_agent = os.path.expanduser("~/Library/LaunchAgents/com.user.screenshotutil.plist")
            if os.path.exists(launch_agent):
                subprocess.run(["launchctl", "unload", launch_agent], 
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        except Exception as e:
            print(f"Error disabling LaunchAgent: {e}")
        
        # Force exit to ensure we really quit
        rumps.quit_application()
        
        # If we're still running after rumps.quit_application(), use sys.exit
        print("Forcing exit...")
        sys._exit(0)  # Use _exit to ensure we really exit


def run_service():
    """Run the screenshot utility as a background service"""
    try:
        # Add a unique identifying string that we can use to detect this process later
        print("Starting Screenshot Utility service with identifier: screenshot-service-instance")
        
        # Create an ID file to mark this as the active service
        service_lock_path = os.path.expanduser("~/.screenshot_util_service.lock")
        try:
            # Write our PID to the lock file
            with open(service_lock_path, "w") as f:
                f.write(str(os.getpid()))
                
            # Make sure to clean up the lock file on exit
            import atexit
            def cleanup_lock():
                try:
                    if os.path.exists(service_lock_path):
                        os.remove(service_lock_path)
                except:
                    pass
            atexit.register(cleanup_lock)
        except Exception as e:
            print(f"Error creating lock file: {e}")
            # Continue anyway
            
        # Start the service
        app = ScreenshotUtilService()
        app.run()
    except KeyboardInterrupt:
        print("Service interrupted by user, exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"Error in service: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_service()