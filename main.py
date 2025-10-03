#!/usr/bin/env python3
"""
Entry point for Flet build system
"""
from src.main import *

if __name__ == "__main__":
    import sys
    import platform
    import flet as ft
    from src.main_app import main as app_main
    from src.main import check_platform

    check_platform()
    ft.app(target=app_main)
