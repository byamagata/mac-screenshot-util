from setuptools import setup, find_packages

setup(
    name="screenshot-util",
    version="0.1.0",
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