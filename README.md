# macOS Screenshot Utility

A Python-based screenshot utility for macOS that allows users to select custom screen areas for capture, copy to clipboard, and annotate with basic shapes. The utility can run as a standalone application or as a background service in the menu bar.

## Features

- Select custom screen areas for capture
- Copy screenshots to clipboard
- Open screenshots for annotation with basic shapes and customizable colors
- Keyboard shortcut activation
- Background service with menu bar icon
- Global hotkey support
- Customizable preferences
- Auto-launch at login option

## Installation

1. Clone this repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate`
4. Install requirements: `pip install -r requirements.txt`

## Usage

### Standalone Mode

Run the application in standalone mode:

```
python run.py
```

### Background Service Mode

Run the application as a background service with a menu bar icon:

```
python run.py --service
```

### Direct Capture Mode

Run the application directly in capture mode (no main window, just the capture overlay):

```
python run.py --direct-capture
```

This mode is especially useful for testing and for when the background service calls the capture functionality.

### Creating an Application Bundle

To create a standalone macOS application (.app):

```
python package.py
```

This will create the app bundle in the `dist` directory. You can then move the app to your Applications folder.

### Using the Installer

The Screenshot Utility comes with an installer script that helps with installation, auto-launch configuration, and uninstallation:

```
python installer.py
```

This will show an interactive menu with the following options:
1. Install Application - Creates and installs the app in the Applications folder
2. Enable Auto-Launch at Login - Sets up the app to start automatically at login
3. Disable Auto-Launch at Login - Prevents the app from starting at login
4. Uninstall Application - Removes the app and its preferences

You can also use command-line arguments for non-interactive usage:

```
python installer.py install              # Install the app and enable auto-launch
python installer.py uninstall            # Uninstall the app
python installer.py enable-autostart     # Enable auto-launch at login
python installer.py disable-autostart    # Disable auto-launch at login
```

## Development

- Run tests: `pytest tests/`
- Modify hotkey: `python run.py --shortcut "Ctrl+Shift+4"`

## Customizing Preferences

When running in background service mode, you can access preferences through the menu bar icon:

1. Click the screenshot icon in the menu bar
2. Select "Preferences" > "Hotkey Settings" or other preference options
3. Adjust settings in the preferences dialog

Available preferences include:
- Global hotkey combination
- Screenshot save location
- Default annotation tools and colors
- Auto-launch at login option