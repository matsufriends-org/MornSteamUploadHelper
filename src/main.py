#!/usr/bin/env python3
"""
Morn Steam Upload Helper

A GUI application to simplify the Steam game upload process using SteamCMD.
This tool helps developers automate the process of uploading game builds to Steam.

Features:
- GUI interface for SteamCMD operations
- Save and manage multiple upload configurations
- Automatic VDF file generation
- Cross-platform support (Windows, macOS, Linux)

Security Note:
This application passes credentials to SteamCMD. For enhanced security,
it's recommended to use Steam Guard mobile authentication.

Author: MornSteamUploadHelper Contributors
License: Unlicense (Public Domain)
"""

import flet as ft

# Import main application
from main_app import main as app_main

if __name__ == "__main__":
    ft.app(target=app_main)