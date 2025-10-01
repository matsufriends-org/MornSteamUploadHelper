"""Command sending functionality for Steam Upload Helper"""

import platform
import subprocess
import time
from pathlib import Path
from typing import Optional, Callable


class CommandSender:
    """プラットフォーム共通のコマンド送信クラス"""
    
    @staticmethod
    def send_command(command: str, target_window_pattern: str = "Steam>", 
                    process_id: Optional[int] = None, 
                    log_callback: Optional[Callable] = None) -> bool:
        """
        コンソールウィンドウにコマンドを送信
        
        Args:
            command: 送信するコマンド
            target_window_pattern: ターゲットウィンドウを識別するパターン
            process_id: Windows用のプロセスID（オプション）
            log_callback: ログ出力用のコールバック
            
        Returns:
            bool: 送信成功/失敗
        """
        system = platform.system()
        
        if system == "Windows":
            return CommandSender._send_windows(command, target_window_pattern, process_id, log_callback)
        elif system == "Darwin":
            return CommandSender._send_macos(command, target_window_pattern, log_callback)
        else:
            return CommandSender._send_linux(command, target_window_pattern, log_callback)
    
    @staticmethod
    def _send_windows(command: str, target_pattern: str, process_id: Optional[int], log_callback) -> bool:
        """Windows環境でのコマンド送信"""
        try:
            escaped_command = command.replace('"', '`"').replace("'", "''")
            
            # PowerShellスクリプト
            ps_script = f'''
Add-Type -AssemblyName System.Windows.Forms

Add-Type @"
    using System;
    using System.Runtime.InteropServices;
    using System.Text;

    public class InputHelper {{
        [DllImport("user32.dll")]
        public static extern bool EnumWindows(EnumWindowsProc enumProc, IntPtr lParam);

        [DllImport("user32.dll")]
        public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

        [DllImport("user32.dll")]
        public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

        [DllImport("user32.dll")]
        public static extern bool IsWindowVisible(IntPtr hWnd);

        [DllImport("user32.dll")]
        public static extern bool SetForegroundWindow(IntPtr hWnd);

        [DllImport("user32.dll")]
        public static extern IntPtr GetForegroundWindow();

        [DllImport("imm32.dll")]
        public static extern IntPtr ImmGetContext(IntPtr hWnd);

        [DllImport("imm32.dll")]
        public static extern bool ImmReleaseContext(IntPtr hWnd, IntPtr hIMC);

        [DllImport("imm32.dll")]
        public static extern bool ImmGetOpenStatus(IntPtr hIMC);

        [DllImport("imm32.dll")]
        public static extern bool ImmSetOpenStatus(IntPtr hIMC, bool fOpen);

        public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    }}
"@

# Find console window
$candidates = @()
$callback = {{
    param($hWnd, $lParam)
    $sb = New-Object System.Text.StringBuilder 256
    [InputHelper]::GetWindowText($hWnd, $sb, $sb.Capacity) | Out-Null
    $title = $sb.ToString()

    if ([InputHelper]::IsWindowVisible($hWnd)) {{
        # Look for windows containing the target pattern
        if ($title -like "*{target_pattern}*" -or $title -like "*steamcmd*" -or $title -like "*MornSteamCMD*") {{
            $procId = 0
            [InputHelper]::GetWindowThreadProcessId($hWnd, [ref]$procId) | Out-Null
            
            $obj = [PSCustomObject]@{{
                Handle = $hWnd
                Title = $title
                PID = $procId
            }}
            $script:candidates += $obj
        }}
    }}
    return $true
}}

$candidates = @()
[InputHelper]::EnumWindows($callback, [IntPtr]::Zero) | Out-Null

if ($candidates.Count -eq 0) {{
    Write-Output "NOTFOUND"
    exit 1
}}

# Select best candidate
$targetWindow = $candidates[0]

# Save current foreground window
$originalWindow = [InputHelper]::GetForegroundWindow()

# Focus and send
[InputHelper]::SetForegroundWindow($targetWindow.Handle) | Out-Null
Start-Sleep -Milliseconds 100

try {{
    # Copy command to clipboard
    Set-Clipboard -Value "{escaped_command}"

    # Disable IME if needed
    $hIMC = [InputHelper]::ImmGetContext($targetWindow.Handle)
    if ($hIMC -ne [IntPtr]::Zero) {{
        $imeStatus = [InputHelper]::ImmGetOpenStatus($hIMC)
        if ($imeStatus) {{
            [InputHelper]::ImmSetOpenStatus($hIMC, $false) | Out-Null
        }}
        [InputHelper]::ImmReleaseContext($targetWindow.Handle, $hIMC) | Out-Null
    }}
    Start-Sleep -Milliseconds 50

    # Paste from clipboard + enter
    [System.Windows.Forms.SendKeys]::SendWait("^v{{ENTER}}")
    Write-Output "SUCCESS"
}} catch {{
    Write-Output "ERROR: $_"
    exit 1
}} finally {{
    # Restore focus
    if ($originalWindow -ne [IntPtr]::Zero) {{
        [InputHelper]::SetForegroundWindow($originalWindow) | Out-Null
    }}
}}
'''
            
            result = subprocess.run(
                ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if "SUCCESS" in result.stdout:
                if log_callback:
                    log_callback(f"✓ コマンドを送信しました: {command}")
                return True
            elif "NOTFOUND" in result.stdout:
                if log_callback:
                    log_callback("✗ 対象ウィンドウが見つかりませんでした")
                return False
            else:
                if log_callback:
                    log_callback(f"✗ 送信エラー: {result.stderr}")
                return False
                
        except Exception as e:
            if log_callback:
                log_callback(f"コマンド送信エラー: {e}")
            return False
    
    @staticmethod
    def _send_macos(command: str, target_pattern: str, log_callback) -> bool:
        """macOS環境でのコマンド送信"""
        try:
            escaped_command = command.replace('\\', '\\\\').replace('"', '\\"')
            
            # AppleScript for sending command
            apple_script = f'''
tell application "Terminal"
    -- Find the window with SteamCMD
    set found to false
    set targetWindow to missing value
    set debugInfo to ""
    set windowCount to count windows
    set debugInfo to debugInfo & "Total windows: " & windowCount & "\n"
    
    -- Look for windows containing steamcmd
    repeat with i from 1 to windowCount
        try
            set w to window i
            set windowName to name of w
            set debugInfo to debugInfo & "Window " & i & " name: " & windowName & "\n"
            
            -- Check if window name contains our markers
            if windowName contains "MornSteamCMD" or windowName contains "Help Test" or windowName contains "steamcmd" then
                set targetWindow to w
                set found to true
                set debugInfo to debugInfo & "Found by window name!\n"
                exit repeat
            end if
            
            -- Check tabs for steamcmd process
            set tabCount to count tabs of w
            repeat with j from 1 to tabCount
                try
                    set t to tab j of w
                    set tabProcesses to processes of t
                    set debugInfo to debugInfo & "  Tab " & j & " processes: " & (tabProcesses as string) & "\n"
                    
                    if "steamcmd" is in tabProcesses then
                        set targetWindow to w
                        set found to true
                        set debugInfo to debugInfo & "Found by process in tab " & j & "!\n"
                        exit repeat
                    end if
                end try
            end repeat
            
            if found then exit repeat
        on error errMsg
            set debugInfo to debugInfo & "Error checking window " & i & ": " & errMsg & "\n"
        end try
    end repeat
    
    if not found then
        return "NOTFOUND: " & debugInfo
    end if
    
    -- Activate the found window
    set index of targetWindow to 1
    activate
end tell

-- Wait for window to be active
delay 0.5

-- Send the command
tell application "System Events"
    tell process "Terminal"
        -- Type the command
        keystroke "{escaped_command}"
        delay 0.1
        -- Press Enter
        keystroke return
    end tell
end tell

return "SUCCESS: " & debugInfo
'''
            
            # デバッグ: AppleScriptの内容をログ出力
            if log_callback:
                log_callback(f"[デバッグ] macOS コマンド送信: '{command}'")
                log_callback(f"[デバッグ] ターゲットパターン: '{target_pattern}'")
            
            result = subprocess.run(
                ['osascript', '-e', apple_script],
                capture_output=True,
                text=True
            )
            
            # デバッグ情報を出力
            if log_callback:
                if result.stderr:
                    log_callback(f"[デバッグ] AppleScript stderr: {result.stderr}")
                if "NOTFOUND" in result.stdout:
                    log_callback(f"[デバッグ] {result.stdout}")
                elif "SUCCESS" in result.stdout:
                    log_callback(f"[デバッグ] {result.stdout}")
            
            if result.returncode == 0 and "SUCCESS" in result.stdout:
                if log_callback:
                    log_callback(f"✓ コマンドを送信しました: {command}")
                return True
            elif "NOTFOUND" in result.stdout:
                if log_callback:
                    log_callback("✗ 対象ウィンドウが見つかりませんでした")
                return False
            else:
                if log_callback:
                    log_callback(f"✗ 送信エラー: {result.stderr}")
                return False
                
        except Exception as e:
            if log_callback:
                log_callback(f"コマンド送信エラー: {e}")
            return False
    
    @staticmethod
    def _send_linux(command: str, target_pattern: str, log_callback) -> bool:
        """Linux環境でのコマンド送信（未実装）"""
        if log_callback:
            log_callback("Linux環境での自動送信は未サポートです")
        return False
    
    @staticmethod
    def test_send_help(steamcmd_path: str, log_callback: Optional[Callable] = None) -> bool:
        """
        helpコマンドの送信テスト
        
        新しいSteamCMDウィンドウを開いて、helpコマンドを送信できるかテストする
        """
        if log_callback:
            log_callback("SteamCMDテストを開始します...")
        
        # プラットフォーム別にSteamCMDを起動
        system = platform.system()
        
        try:
            if system == "Windows":
                # Windowsでcmd.exeを開いてSteamCMDを起動
                script_content = f'''@echo off
echo SteamCMD Help Test Window
echo.
cd /d "{Path(steamcmd_path).parent}"
"{steamcmd_path}"
'''
                script_path = Path(__file__).parent / "configs" / "test_help.bat"
                script_path.parent.mkdir(exist_ok=True)
                with open(script_path, 'w', encoding='cp932') as f:
                    f.write(script_content)
                
                subprocess.Popen(['cmd', '/k', str(script_path)])
                
            elif system == "Darwin":
                # macOSでTerminalを開いてSteamCMDを起動
                script_content = f'''#!/bin/bash
# ウィンドウタイトルを設定して識別しやすくする
printf "\\033]0;MornSteamCMD - Help Test\\007"
echo "SteamCMD Help Test Window"
echo ""
cd "{Path(steamcmd_path).parent}"
"{steamcmd_path}"
'''
                script_path = Path(__file__).parent / "configs" / "test_help.sh"
                script_path.parent.mkdir(exist_ok=True)
                with open(script_path, 'w') as f:
                    f.write(script_content)
                script_path.chmod(0o755)
                
                apple_script = f'''
                tell application "Terminal"
                    do script "{str(script_path.absolute())}"
                    activate
                end tell
                '''
                subprocess.run(['osascript', '-e', apple_script])
                
            else:
                if log_callback:
                    log_callback("Linux環境はサポートされていません")
                return False
            
            # SteamCMDの起動を待機
            if log_callback:
                log_callback("SteamCMDの起動を待機中...")
            
            # まずsteamcmdプロセスが起動するまで待つ（1秒ごとに確認）
            max_wait = 10  # 最大10秒待機
            process_check_interval = 1.0  # 1秒ごとに確認
            elapsed = 0
            process_found = False
            
            while elapsed < max_wait:
                check_script = '''
tell application "Terminal"
    repeat with w in windows
        try
            set windowName to name of w
            if windowName contains "MornSteamCMD" or windowName contains "Help Test" then
                repeat with t in tabs of w
                    try
                        if "steamcmd" is in (processes of t) then
                            return "FOUND"
                        end if
                    end try
                end repeat
            end if
        end try
    end repeat
    return "NOTFOUND"
end tell
'''
                result = subprocess.run(['osascript', '-e', check_script], capture_output=True, text=True)
                
                if "FOUND" in result.stdout:
                    process_found = True
                    if log_callback:
                        log_callback(f"steamcmdプロセスを検出しました（{elapsed:.0f}秒後）")
                    break
                
                time.sleep(process_check_interval)
                elapsed += process_check_interval
                if log_callback and elapsed < max_wait:
                    log_callback(f"steamcmdプロセス待機中... ({elapsed:.0f}秒経過)")
            
            if process_found:
                # Steam>プロンプトが表示されるまで待機（0.5秒ごとに確認）
                if log_callback:
                    log_callback("Steam>プロンプトを待機中...")
                
                prompt_wait_interval = 0.5  # 0.5秒ごとに確認
                prompt_max_wait = 10  # 最大10秒待機
                prompt_elapsed = 0
                
                while prompt_elapsed < prompt_max_wait:
                    # 簡単な方法：一定時間待てばSteam>が表示される
                    # 通常は2-3秒で表示される
                    time.sleep(prompt_wait_interval)
                    prompt_elapsed += prompt_wait_interval
                    
                    # 2.5秒経過したら十分とみなす
                    if prompt_elapsed >= 2.5:
                        if log_callback:
                            log_callback(f"Steam>プロンプトの表示を待機完了（{prompt_elapsed:.1f}秒後）")
                        break
                    
                    if int(prompt_elapsed * 2) % 2 == 0:  # 1秒ごとにログ
                        if log_callback:
                            log_callback(f"Steam>プロンプト待機中... ({prompt_elapsed:.1f}秒経過)")
            else:
                if log_callback:
                    log_callback("警告: steamcmdプロセスが検出できませんでした")
            
            # helpコマンドを送信（本番と同じ実装を使用）
            success = CommandSender.send_command("help", "Steam>", log_callback=log_callback)
            
            if success:
                if log_callback:
                    log_callback("✅ helpコマンドの送信に成功しました！")
                    log_callback("この仕組みで本番のアップロードコマンドも送信されます。")
            else:
                if log_callback:
                    log_callback("❌ helpコマンドの送信に失敗しました。")
                    log_callback("ウィンドウが正しく開いているか確認してください。")
            
            return success
            
        except Exception as e:
            if log_callback:
                log_callback(f"テスト中にエラーが発生しました: {e}")
            return False