"""
Utility functions for Morn Steam Upload Helper.
"""

import os
import webbrowser
from datetime import datetime
from pathlib import Path
# OS依存の処理はplatform_helpersからインポート
from platform_helpers import PlatformUtilities, SteamCMDLauncher


def open_content_folder(content_path):
    """Open the content folder in the system file explorer."""
    if content_path and os.path.exists(content_path):
        folder_path = os.path.dirname(content_path) if os.path.isfile(content_path) else content_path
        return PlatformUtilities.open_folder(folder_path)
    return False


def log_message(message):
    """Log a message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    return log_entry


def open_steam_page(page_type, app_id):
    """Open Steam partner pages in web browser."""
    if not app_id:
        return
    
    base_url = "https://partner.steamgames.com"
    urls = {
        "store": f"https://store.steampowered.com/app/{app_id}/",
        "partner": f"{base_url}/apps/landing/{app_id}",
        "builds": f"{base_url}/apps/builds/{app_id}",
        "depots": f"{base_url}/apps/depots/{app_id}"
    }
    
    if page_type in urls:
        webbrowser.open(urls[page_type])


def open_steam_page_for_config(page_type, app_id):
    """Opens Steam page for a specific configuration."""
    open_steam_page(page_type, app_id)


def cleanup_temp_scripts():
    """Remove any temporary script files containing credentials."""
    try:
        # Clean up all possible temporary script paths
        temp_scripts = [
            Path("./configs/steamcmd_session.sh"),
            Path("./configs/steamcmd_session.bat"),
            Path("./configs/steamcmd_login.sh"),
            Path("./configs/steamcmd_login.bat")
        ]
        
        for script_path in temp_scripts:
            if script_path.exists():
                script_path.unlink()
                log_message(f"一時スクリプトファイルを削除: {script_path.name}")
    except Exception as e:
        log_message(f"警告: 一時スクリプトファイルの削除エラー: {e}")


def ensure_executable(file_path):
    """Make a file executable on Unix systems."""
    # platform_helpersではWindowsチェックが必要
    import platform
    if platform.system() != "Windows" and file_path and os.path.exists(file_path):
        try:
            os.chmod(file_path, 0o755)
            return True
        except Exception as e:
            log_message(f"警告: 実行権限を設定できませんでした: {e}")
            return False
    return True


def get_steamcmd_path(content_builder_path):
    """Get the SteamCMD path based on the ContentBuilder path."""
    # platform_helpersのSteamCMDLauncherを使用
    return SteamCMDLauncher.get_steamcmd_path(content_builder_path)


def create_directories(*paths):
    """Create directories if they don't exist."""
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)


def get_platform_terminal_command(script_path):
    """Get platform-specific terminal command."""
    # platform_helpersに適切な引数を渡す
    working_dir = os.path.dirname(script_path) or "."
    return PlatformUtilities.get_platform_terminal_command(working_dir, script_path)


def copy_to_clipboard(text, page=None):
    """Copy text to clipboard (cross-platform)."""
    success = PlatformUtilities.copy_to_clipboard(text)
    if not success:
        log_message("クリップボードへのコピーに失敗")
    return success


def format_path_for_steam(path):
    """Format path for Steam VDF files."""
    # Convert to absolute path and use forward slashes
    abs_path = os.path.abspath(path)
    return abs_path.replace('\\', '/')


def is_process_running(process_name):
    """Check if a process is running."""
    return PlatformUtilities.is_process_running(process_name)


def get_timestamp():
    """Get formatted timestamp string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")