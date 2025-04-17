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

### Creating and Distributing the Application Bundle

To create a standalone macOS application (.app) that you can distribute to colleagues:

```
python package.py
```

The script will:
1. Clean up any previous packaging attempts
2. Install required dependencies
3. Create the application bundle in the `dist` directory
4. Create a ZIP archive for easy distribution
5. Display clear instructions on where to find the files

When the packaging process is complete, you'll find:
- The application bundle at `dist/Screenshot Utility.app`
- A distribution ZIP file at `dist/Screenshot Utility-x.x.x.zip` (where x.x.x is the version number)

You can then:
- Move the .app to your Applications folder for personal use
- Send the ZIP file to colleagues who can extract it and use the app

Additional options:
```
python package.py --clean    # Just clean previous builds without creating a new package
python package.py --help     # Show help information
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