"""
Application constants for Morn Steam Upload Helper.
"""
import os
import sys
from pathlib import Path

# Application Information
APP_VERSION = "1.0.24"
APP_NAME = "Morn Steam Upload Helper"

# Determine base directory
# When frozen by PyInstaller, use user's home directory
# When running as script, use current directory
if getattr(sys, 'frozen', False):
    # Running as compiled app
    BASE_DIR = Path.home() / ".morn_steam_upload_helper"
    BASE_DIR.mkdir(exist_ok=True)
else:
    # Running as script
    BASE_DIR = Path(".")

# Directory Configuration
CONFIG_DIR = str(BASE_DIR / "configs")
VDF_DIR = str(BASE_DIR / "vdf_files")
LOG_DIR = str(BASE_DIR / "log")

# UI Configuration
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800
DEFAULT_PADDING = 10