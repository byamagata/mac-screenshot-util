# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- Run application: `python src/main.py` or `python run.py`
- Run tests: `pytest tests/`
- Run single test: `pytest tests/test_screenshot_app.py::test_function_name -v`
- Activate virtual environment: `source screenshot/bin/activate` (macOS/Linux)

## Code Style Guidelines

- **Imports**: Group imports by standard library, third-party, and local modules
- **Formatting**: Use 4-space indentation, 120 character line limit
- **Documentation**: Use docstrings for modules, classes, and functions
- **Error Handling**: Use try/except blocks with specific exception types and detailed error messages
- **Naming**: Use snake_case for variables/functions, CamelCase for classes
- **Types**: Include type hints where appropriate for clarity
- **Logging**: Use print statements for debug information
- **UI Components**: Follow Qt naming conventions for Qt objects
- **Platform-specific**: Use `sys.platform == "darwin"` checks for macOS-specific code