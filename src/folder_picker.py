"""
Cross-platform folder picker using native dialogs
"""

import os
import sys
import platform
import subprocess
from pathlib import Path
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
Add-Type @"
    using System;
    using System.Runtime.InteropServices;
    using System.Threading;
    public class WinAPI {
        [DllImport("user32.dll")]
        public static extern bool SetForegroundWindow(IntPtr hWnd);

        [DllImport("user32.dll")]
        public static extern IntPtr GetForegroundWindow();

        [DllImport("user32.dll")]
        public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
    }
"@

$folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
$folderBrowser.Description = "{{DIALOG_TITLE}}"

# フォーカス処理用のRunspaceを準備
$runspace = [runspacefactory]::CreateRunspace()
$runspace.Open()

$powershell = [powershell]::Create()
$powershell.Runspace = $runspace

# フォーカス処理スクリプト
$focusBlock = {
    param($targetTitle, $parentPid)

    Add-Type @"
        using System;
        using System.Runtime.InteropServices;
        using System.Text;
        public class WinAPI2 {
            [DllImport("user32.dll")]
            public static extern bool SetForegroundWindow(IntPtr hWnd);

            [DllImport("user32.dll")]
            public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);

            [DllImport("user32.dll")]
            public static extern bool EnumWindows(EnumWindowsProc enumProc, IntPtr lParam);

            [DllImport("user32.dll")]
            public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

            [DllImport("user32.dll")]
            public static extern bool IsWindowVisible(IntPtr hWnd);

            [DllImport("user32.dll")]
            public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

            [DllImport("user32.dll")]
            public static extern IntPtr GetForegroundWindow();

            [DllImport("user32.dll")]
            public static extern bool BringWindowToTop(IntPtr hWnd);

            [DllImport("user32.dll")]
            public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

            [DllImport("user32.dll")]
            public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);

            public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

            public const int SW_SHOW = 5;
            public static readonly IntPtr HWND_TOPMOST = new IntPtr(-1);
            public static readonly IntPtr HWND_NOTOPMOST = new IntPtr(-2);
            public const uint SWP_NOMOVE = 0x0002;
            public const uint SWP_NOSIZE = 0x0001;
            public const uint SWP_SHOWWINDOW = 0x0040;
        }
"@

    Start-Sleep -Milliseconds 100

    for ($i = 0; $i -lt 20; $i++) {
        Start-Sleep -Milliseconds 30

        # ダイアログウィンドウを検出
        $dialogWindow = [IntPtr]::Zero

        $callback = {
            param($hWnd, $lParam)
            if ([WinAPI2]::IsWindowVisible($hWnd)) {
                $sb = New-Object System.Text.StringBuilder 256
                [WinAPI2]::GetWindowText($hWnd, $sb, $sb.Capacity) | Out-Null
                $title = $sb.ToString()

                # プロセスIDを確認
                $procId = 0
                [WinAPI2]::GetWindowThreadProcessId($hWnd, [ref]$procId) | Out-Null

                # 同じプロセスのダイアログウィンドウを探す
                if ($procId -eq $parentPid -and ($title -eq "$targetTitle" -or $title -like "*フォルダ*" -or $title -like "*参照*")) {
                    $script:dialogWindow = $hWnd
                    return $false
                }
            }
            return $true
        }

        [WinAPI2]::EnumWindows($callback, [IntPtr]::Zero) | Out-Null

        if ($dialogWindow -ne [IntPtr]::Zero) {
            # ウィンドウを前面に持ってくる
            [WinAPI2]::ShowWindow($dialogWindow, [WinAPI2]::SW_SHOW) | Out-Null
            [WinAPI2]::BringWindowToTop($dialogWindow) | Out-Null
            [WinAPI2]::SetWindowPos($dialogWindow, [WinAPI2]::HWND_TOPMOST, 0, 0, 0, 0, [WinAPI2]::SWP_NOMOVE -bor [WinAPI2]::SWP_NOSIZE -bor [WinAPI2]::SWP_SHOWWINDOW) | Out-Null
            Start-Sleep -Milliseconds 10
            [WinAPI2]::SetForegroundWindow($dialogWindow) | Out-Null
            Start-Sleep -Milliseconds 10
            [WinAPI2]::SetWindowPos($dialogWindow, [WinAPI2]::HWND_NOTOPMOST, 0, 0, 0, 0, [WinAPI2]::SWP_NOMOVE -bor [WinAPI2]::SWP_NOSIZE -bor [WinAPI2]::SWP_SHOWWINDOW) | Out-Null
            [WinAPI2]::SetForegroundWindow($dialogWindow) | Out-Null
            break
        }
    }
}

$powershell.AddScript($focusBlock).AddArgument("{{DIALOG_TITLE}}").AddArgument($PID) | Out-Null
$handle = $powershell.BeginInvoke()

# ダイアログを表示
$result = $folderBrowser.ShowDialog()

# クリーンアップ
$powershell.EndInvoke($handle)
$powershell.Dispose()
$runspace.Close()

if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
    Write-Output $folderBrowser.SelectedPath
}
'''.replace("{{DIALOG_TITLE}}", title)

            result = subprocess.run(
                ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', script],
                capture_output=True,
                text=True,
                timeout=300,
                creationflags=0x08000000  # CREATE_NO_WINDOW
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
