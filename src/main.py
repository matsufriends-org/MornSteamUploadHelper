#!/usr/bin/env python3
"""
Morn Steam Upload Helper

A GUI application to simplify the Steam game upload process using SteamCMD.
This tool helps developers automate the process of uploading game builds to Steam.

Features:
- GUI interface for SteamCMD operations
- Save and manage multiple upload configurations
- Automatic VDF file generation
- Cross-platform support (Windows, macOS)

Security Note:
This application passes credentials to SteamCMD. For enhanced security,
it's recommended to use Steam Guard mobile authentication.

Author: MornSteamUploadHelper Contributors
License: Unlicense (Public Domain)
"""

import sys
import platform
import flet as ft

# Import main application
from main_app import main as app_main

def check_platform():
    """プラットフォームをチェックし、非対応OSの場合はエラーを表示して終了"""
    system = platform.system()

    if system not in ["Windows", "Darwin"]:
        # Linuxまたはその他の非対応OS
        print("=" * 60)
        print("エラー: 非対応のオペレーティングシステムです")
        print("=" * 60)
        print()
        print(f"検出されたOS: {system}")
        print()
        print("このアプリケーションは以下のOSでのみ動作します:")
        print("  - Windows")
        print("  - macOS")
        print()
        print("Linux環境では動作確認が取れていないため、")
        print("現在サポート対象外となっています。")
        print()
        print("Windows、macOSのいずれかでご利用ください。")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    # プラットフォームチェック
    check_platform()

    # アプリケーション起動
    ft.app(target=app_main)