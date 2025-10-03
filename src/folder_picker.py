"""
Cross-platform folder picker using native dialogs
"""

import os
import sys
import platform
import subprocess
from typing import Optional, Callable


def pick_folder(title: str = "フォルダを選択", callback: Optional[Callable[[str], None]] = None) -> Optional[str]:
    """
    フォルダ選択ダイアログを表示

    Args:
        title: ダイアログのタイトル
        callback: 選択後に呼び出されるコールバック関数（パスを引数に取る）

    Returns:
        選択されたフォルダのパス（キャンセルされた場合はNone）
    """
    try:
        system = platform.system()

        if system == "Darwin":  # macOS
            # osascriptを使用してネイティブのフォルダ選択ダイアログを表示
            script = f'''
tell application "System Events"
    activate
    set folderPath to choose folder with prompt "{title}"
    return POSIX path of folderPath
end tell
'''
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0 and result.stdout.strip():
                folder_path = result.stdout.strip()
                if callback:
                    callback(folder_path)
                return folder_path
            return None

        elif system == "Windows":
            # Windowsの場合はPowerShellを使用
            script = '''
Add-Type -AssemblyName System.Windows.Forms
$folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
$folderBrowser.Description = "{}"
$result = $folderBrowser.ShowDialog()
if ($result -eq [System.Windows.Forms.DialogResult]::OK) {{
    Write-Output $folderBrowser.SelectedPath
}}
'''.format(title)

            result = subprocess.run(
                ['powershell', '-Command', script],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0 and result.stdout.strip():
                folder_path = result.stdout.strip()
                if callback:
                    callback(folder_path)
                return folder_path
            return None

        else:
            print(f"Error: Unsupported platform {system}")
            return None

    except subprocess.TimeoutExpired:
        print("Error: Folder picker timed out")
        return None
    except Exception as e:
        print(f"Error in folder picker: {e}")
        return None
