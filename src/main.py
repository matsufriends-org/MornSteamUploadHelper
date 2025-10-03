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

import os
import sys
import platform

# macOS SDK version compatibility workaround
# Must be set before importing flet
if platform.system() == "Darwin":
    os.environ["SYSTEM_VERSION_COMPAT"] = "0"

import flet as ft

# Import main application
# Use absolute import for PyInstaller compatibility
if __package__:
    from .main_app import main as app_main
else:
    # When running as script (e.g., via PyInstaller)
    if getattr(sys, 'frozen', False):
        # PyInstallerでビルドされた場合
        bundle_dir = sys._MEIPASS
    else:
        # 通常のスクリプト実行
        bundle_dir = os.path.dirname(os.path.abspath(__file__))

    sys.path.insert(0, bundle_dir)
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
    # デバッグログファイルの設定
    import datetime
    log_file = None

    try:
        if getattr(sys, 'frozen', False):
            # PyInstallerビルド時のみログファイルを作成
            log_path = os.path.join(os.path.expanduser("~"), "MornSteamUploadHelper_debug.log")
            log_file = open(log_path, "a", encoding="utf-8", buffering=1)
            sys.stdout = log_file
            sys.stderr = log_file

        print(f"\n=== {datetime.datetime.now()} ===")
        print("Log started")
        print(f"Frozen: {getattr(sys, 'frozen', False)}")

        # プラットフォームチェック
        print("Checking platform...")
        check_platform()
        print("Platform check passed")

        # デバッグ情報を出力
        print(f"Starting application...")
        print(f"Python: {sys.version}")
        print(f"Platform: {platform.system()}")
        if getattr(sys, 'frozen', False):
            print(f"MEIPASS: {sys._MEIPASS}")

        print("Importing main_app...")
        # Import is already at the top, so just call it

        print("Launching flet app...")
        # アプリケーション起動
        ft.app(target=app_main)
        print("Flet app finished")
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print(traceback.format_exc())
        if not log_file:
            # コンソール表示の場合は入力待ち
            input("Press Enter to exit...")
    finally:
        if log_file:
            log_file.flush()
            log_file.close()