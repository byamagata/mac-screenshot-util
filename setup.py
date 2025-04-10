from setuptools import setup, find_packages
import sys
import os

# Add the project root to the path so we can import the version
sys.path.insert(0, os.path.abspath('.'))
from src import __version__

setup(
    name="screenshot-util",
    version=__version__,
    packages=find_packages(),
    install_requires=[
        "pyqt6>=6.0.0",
        "pillow>=9.0.0",
        "pyperclip>=1.8.0",
        "pyautogui>=0.9.0",
        "pyobjc>=8.0",
    ],
    entry_points={
        "console_scripts": [
            "screenshot-util=src.main:main",
        ],
    },
    python_requires=">=3.8",
    author="Your Name",
    description="A macOS screenshot utility for capturing, annotating, and copying screenshots",
)