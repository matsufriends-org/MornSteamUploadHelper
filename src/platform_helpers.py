"""Platform-specific helper functions for Steam Upload Helper"""

import os
import platform
import subprocess
import threading
import time
from pathlib import Path


class SteamCMDLauncher:
    """プラットフォーム固有のSteamCMD起動処理を管理"""
    
    @staticmethod
    def get_steamcmd_path(content_builder_path: str) -> str:
        """プラットフォームに応じたSteamCMDパスを取得"""
        if platform.system() == "Darwin":  # macOS
            return os.path.join(content_builder_path, "builder_osx", "steamcmd.sh")
        elif platform.system() == "Windows":
            return os.path.join(content_builder_path, "builder", "steamcmd.exe")
        else:  # Linux
            return os.path.join(content_builder_path, "builder_linux", "steamcmd.sh")
    
    @staticmethod
    def launch_steamcmd_console(steamcmd_path: str, username: str, password: str, 
                              steam_guard: str = "", log_callback=None):
        """SteamCMDコンソールを起動"""
        system = platform.system()
        
        if system == "Darwin":
            return SteamCMDLauncher._launch_macos(steamcmd_path, username, password, steam_guard, log_callback)
        elif system == "Windows":
            return SteamCMDLauncher._launch_windows(steamcmd_path, username, password, steam_guard, log_callback)
        else:
            return SteamCMDLauncher._launch_linux(steamcmd_path, username, password, steam_guard, log_callback)
    
    @staticmethod
    def _launch_macos(steamcmd_path: str, username: str, password: str, steam_guard: str, log_callback):
        """macOS用のSteamCMD起動処理"""
        abs_steamcmd_path = os.path.abspath(steamcmd_path)
        
        login_cmd = f"login {username} {password}"
        if steam_guard:
            login_cmd += f" {steam_guard}"
        
        script_content = f'''#!/bin/bash
# ターミナルウィンドウのタイトルを設定
printf "\033]0;MornSteamCMD - Upload Console\007"
echo "MornSteamCMD - このウィンドウを閉じないでください"
echo "このコンソールはアップロードに使用されます"
echo ""
cd "{os.path.dirname(abs_steamcmd_path)}"
"{abs_steamcmd_path}" +{login_cmd}
'''
        
        # Get absolute path for script directory
        script_dir = Path(__file__).parent / "configs"
        script_dir.mkdir(exist_ok=True)
        script_path = script_dir / "steamcmd_session.sh"
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        
        # Use absolute path in AppleScript
        apple_script = f'''
        tell application "Terminal"
            set newWindow to do script "{str(script_path.absolute())}"
            set current settings of newWindow to settings set "Basic"
            activate
        end tell
        '''
        
        subprocess.run(['osascript', '-e', apple_script])
        
        if log_callback:
            log_callback("SteamCMDコンソールが開きました。")
        
        return {"terminal": True, "script_path": script_path}
    
    @staticmethod
    def _launch_windows(steamcmd_path: str, username: str, password: str, steam_guard: str, log_callback):
        """Windows用のSteamCMD起動処理"""
        abs_steamcmd_path = os.path.abspath(steamcmd_path)
        
        login_cmd = f"+login {username} {password}"
        if steam_guard:
            login_cmd += f" {steam_guard}"
        
        # バッチファイル作成
        script_content = f'''@echo off
echo MornSteamCMD - このウィンドウを閉じないでください
echo このコンソールはアップロードに使用されます
echo.
cd /d "{os.path.dirname(abs_steamcmd_path)}"
"{abs_steamcmd_path}" {login_cmd}
'''
        
        # Get absolute path for script directory
        script_dir = Path(__file__).parent / "configs"
        script_dir.mkdir(exist_ok=True)
        script_path = script_dir / "steamcmd_session.bat"
        with open(script_path, 'w', encoding='cp932') as f:
            f.write(script_content)
        
        # PowerShellでプロセスID取得
        ps_command = f'$p = Start-Process cmd -ArgumentList "/k", "{os.path.abspath(script_path)}" -PassThru -WindowStyle Normal; Write-Output $p.Id'
        
        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command', ps_command],
            capture_output=True,
            text=True
        )
        
        process_id = None
        if result.returncode == 0 and result.stdout.strip():
            process_id = int(result.stdout.strip())
            if log_callback:
                log_callback(f"SteamCMDコンソールを起動しました (PID: {process_id})")
        
        return {"terminal": True, "script_path": script_path, "process_id": process_id}
    
    @staticmethod
    def _launch_linux(steamcmd_path: str, username: str, password: str, steam_guard: str, log_callback):
        """Linux用のSteamCMD起動処理"""
        abs_steamcmd_path = os.path.abspath(steamcmd_path)
        
        login_cmd = f"login {username} {password}"
        if steam_guard:
            login_cmd += f" {steam_guard}"
        
        script_content = f'''#!/bin/bash
# ターミナルウィンドウのタイトルを設定
printf "\\033]0;MornSteamCMD\\007"
echo "SteamCMD コンソール - このウィンドウを閉じないでください"
echo "このコンソールはアップロードに使用されます"
echo ""
cd "{os.path.dirname(abs_steamcmd_path)}"
"{abs_steamcmd_path}" +{login_cmd}
'''
        
        # Get absolute path for script directory
        script_dir = Path(__file__).parent / "configs"
        script_dir.mkdir(exist_ok=True)
        script_path = script_dir / "steamcmd_session.sh"
        with open(script_path, 'w') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        
        # ターミナル起動を試行
        terminals = ['gnome-terminal', 'konsole', 'xterm']
        for term in terminals:
            try:
                if term == 'gnome-terminal':
                    subprocess.Popen([term, '--', str(script_path)])
                else:
                    subprocess.Popen([term, '-e', str(script_path)])
                break
            except:
                pass
        
        if log_callback:
            log_callback("SteamCMDコンソールが開きました。")
        
        return {"terminal": True, "script_path": script_path}


class LoginMonitor:
    """ログイン状態の監視を管理"""
    
    @staticmethod
    def monitor_login(steamcmd_path: str, username: str, callbacks: dict, 
                     timeout: int = 30, log_callback=None):
        """ログイン状態を監視（バックグラウンドスレッドで実行）"""
        def monitor_thread():
            system = platform.system()
            
            if log_callback:
                log_callback(f"[ログイン監視] スレッド開始 (Platform: {system})")
            
            if system == "Windows":
                LoginMonitor._monitor_windows(steamcmd_path, username, callbacks, timeout, log_callback)
            elif system == "Darwin":
                LoginMonitor._monitor_macos(steamcmd_path, username, callbacks, timeout, log_callback)
            else:
                LoginMonitor._monitor_linux(steamcmd_path, username, callbacks, timeout, log_callback)
        
        thread = threading.Thread(target=monitor_thread, daemon=True)
        thread.start()
        return thread
    
    @staticmethod
    def _get_log_files(steamcmd_path: str) -> list:
        """ログファイルのパスリストを取得"""
        steamcmd_dir = os.path.dirname(os.path.abspath(steamcmd_path))
        
        return [
            os.path.join(steamcmd_dir, "logs", "console_log.txt"),
            os.path.join(steamcmd_dir, "logs", "stderr.txt"),
            os.path.join(steamcmd_dir, "logs", "stdout.txt"),
            os.path.join(steamcmd_dir, "..", "logs", "console_log.txt"),
            os.path.join(steamcmd_dir, "..", "logs", "stderr.txt"),
            os.path.join(steamcmd_dir, "builder", "logs", "console_log.txt"),
        ]
    
    @staticmethod
    def _check_log_content(log_files: list, start_positions: dict) -> str:
        """ログファイルの新しい内容をチェック"""
        for log_path in log_files:
            log_path = os.path.abspath(log_path)
            if os.path.exists(log_path):
                try:
                    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        start_pos = start_positions.get(log_path, 0)
                        f.seek(start_pos)
                        new_content = f.read()
                        
                        # ログイン成功チェック（モバイル認証後も含む）
                        if any(phrase in new_content for phrase in [
                            "Waiting for user info...OK",
                            "Logged in OK",
                            ("Logging in user" in new_content and "OK" in new_content and "Steam>" in new_content)
                        ]):
                            return "success"
                        
                        # モバイル2FA待機中チェック（成功チェックより後に配置）
                        if ("This account is protected by a Steam Guard mobile authenticator" in new_content 
                            and "Waiting for user info...OK" not in new_content):
                            return "mobile_2fa_waiting"
                        
                        # ログイン失敗チェック
                        if any(phrase in new_content for phrase in [
                            "FAILED login",
                            "Invalid Password",
                            "Rate Limit Exceeded",
                            "Two-factor code mismatch",
                            "ERROR (Two-factor code mismatch)"
                        ]):
                            return "failed"
                except:
                    continue
        
        return "unknown"
    
    @staticmethod
    def _monitor_windows(steamcmd_path: str, username: str, callbacks: dict, timeout: int, log_callback=None):
        """Windows用のログイン監視"""
        log_files = LoginMonitor._get_log_files(steamcmd_path)
        
        # 初期位置を記録
        log_positions = {}
        for log_path in log_files:
            if os.path.exists(log_path):
                try:
                    log_positions[log_path] = os.path.getsize(log_path)
                except:
                    pass
        
        time.sleep(2)  # ログイン開始を待つ
        
        # フラグをリセット
        LoginMonitor._mobile_2fa_shown = False
        
        check_count = 0
        max_checks = timeout * 2  # 0.5秒ごとにチェック
        
        if log_callback:
            log_callback(f"[ログイン監視] 開始 (最大{timeout}秒間監視)")
        
        while check_count < max_checks:
            # プロセスチェック
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq steamcmd.exe'],
                capture_output=True, text=True
            )
            
            if "steamcmd.exe" not in result.stdout:
                callbacks.get('on_process_ended', lambda: None)()
                break
            
            # ログチェック
            status = LoginMonitor._check_log_content(log_files, log_positions)
            
            if status == "success":
                callbacks.get('on_success', lambda: None)()
                break
            elif status == "failed":
                callbacks.get('on_failure', lambda: None)()
                break
            elif status == "mobile_2fa_waiting":
                # 初回のみモバイル2FAコールバックを実行
                if not getattr(LoginMonitor, '_mobile_2fa_shown', False):
                    LoginMonitor._mobile_2fa_shown = True
                    callbacks.get('on_mobile_2fa', lambda: None)()
                # モバイル2FA待機中は継続して監視
            
            time.sleep(0.5)
            check_count += 1
            
            # 1秒ごとに進捗をログ出力（0.5秒 × 2）
            if check_count % 2 == 0:
                elapsed = check_count * 0.5
                if log_callback:
                    log_callback(f"[ログイン監視] {elapsed:.0f}秒経過 - ログインチェック中...")
        
        if check_count >= max_checks:
            callbacks.get('on_timeout', lambda: None)()
    
    @staticmethod
    def _monitor_macos(steamcmd_path: str, username: str, callbacks: dict, timeout: int, log_callback=None):
        """macOS用のログイン監視"""
        # フラグをリセット
        LoginMonitor._mobile_2fa_shown = False
        
        check_count = 0
        max_checks = timeout  # 1秒ごとにチェック
        
        if log_callback:
            log_callback(f"[ログイン監視] 開始 (macOS, 最大{timeout}秒間監視)")
        
        while check_count < max_checks:
            # Terminal窓チェック
            window_check = subprocess.run(
                ['osascript', '-e', 'tell application "Terminal" to count windows'],
                capture_output=True, text=True
            )
            
            if window_check.returncode != 0 or window_check.stdout.strip() == "0":
                callbacks.get('on_process_ended', lambda: None)()
                break
            
            # AppleScriptでログイン状態チェック
            check_script = '''
            tell application "Terminal"
                set loginStatus to "unknown"
                try
                    repeat with w in windows
                        try
                            set tabContent to contents of selected tab of w
                            if tabContent contains "steamcmd" or tabContent contains "Steam>" then
                                if tabContent contains "Waiting for user info...OK" then
                                    set loginStatus to "logged_in"
                                    exit repeat
                                else if tabContent contains "FAILED" and tabContent contains "Login Failure" then
                                    set loginStatus to "failed"
                                    exit repeat
                                else if tabContent contains "Two-factor code mismatch" then
                                    set loginStatus to "failed"
                                    exit repeat
                                else if tabContent contains "This account is protected by a Steam Guard mobile authenticator" then
                                    set loginStatus to "mobile_2fa"
                                    exit repeat
                                end if
                            end if
                        end try
                    end repeat
                end try
                return loginStatus
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', check_script],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                status = result.stdout.strip()
                if status == "logged_in":
                    callbacks.get('on_success', lambda: None)()
                    break
                elif status == "failed":
                    callbacks.get('on_failure', lambda: None)()
                    break
                elif status == "mobile_2fa":
                    # 初回のみモバイル2FAコールバックを実行
                    if not getattr(LoginMonitor, '_mobile_2fa_shown', False):
                        LoginMonitor._mobile_2fa_shown = True
                        callbacks.get('on_mobile_2fa', lambda: None)()
                    # モバイル2FA待機中は継続して監視
            
            time.sleep(1)
            check_count += 1
            
            # 1秒ごとに進捗をログ出力
            if log_callback:
                log_callback(f"[ログイン監視] {check_count}秒経過 - ログインチェック中...")
        
        if check_count >= max_checks:
            callbacks.get('on_timeout', lambda: None)()
    
    @staticmethod
    def _monitor_linux(steamcmd_path: str, username: str, callbacks: dict, timeout: int, log_callback=None):
        """Linux用のログイン監視（主にログファイルベース）"""
        # Windowsと同様の実装を使用
        LoginMonitor._monitor_windows(steamcmd_path, username, callbacks, timeout, log_callback)


class PlatformUtilities:
    """OS依存のユーティリティ関数を集約"""
    
    @staticmethod
    def open_folder(path: str) -> bool:
        """フォルダをOSのデフォルトアプリで開く"""
        if not path or not os.path.exists(path):
            return False
        
        system = platform.system()
        try:
            if system == "Darwin":
                subprocess.run(["open", path])
            elif system == "Windows":
                subprocess.run(["explorer", path])
            else:  # Linux
                subprocess.run(["xdg-open", path])
            return True
        except:
            return False
    
    @staticmethod
    def copy_to_clipboard(text: str) -> bool:
        """テキストをクリップボードにコピー"""
        system = platform.system()
        try:
            if system == "Darwin":
                process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
                process.communicate(text.encode())
            elif system == "Windows":
                process = subprocess.Popen(['clip'], stdin=subprocess.PIPE)
                process.communicate(text.encode('cp932'))
            else:  # Linux
                process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
                process.communicate(text.encode())
            return True
        except:
            return False
    
    @staticmethod
    def get_platform_terminal_command(working_dir: str, script_path: str) -> list:
        """プラットフォーム固有のターミナル起動コマンドを取得"""
        system = platform.system()
        
        if system == "Darwin":
            return ['osascript', '-e', f'tell application "Terminal" to do script "cd {working_dir} && {script_path}"']
        elif system == "Windows":
            return ['cmd', '/c', 'start', 'cmd', '/k', f'cd /d "{working_dir}" && "{script_path}"']
        else:  # Linux
            return ['gnome-terminal', '--', 'bash', '-c', f'cd "{working_dir}" && "{script_path}"; exec bash']
    
    @staticmethod
    def is_process_running(process_name: str) -> bool:
        """指定したプロセスが実行中か確認"""
        system = platform.system()
        try:
            if system == "Windows":
                result = subprocess.run(
                    ['tasklist', '/FI', f'IMAGENAME eq {process_name}'],
                    capture_output=True, text=True
                )
                return process_name in result.stdout
            else:  # macOS/Linux
                result = subprocess.run(
                    ['ps', 'aux'],
                    capture_output=True, text=True
                )
                return process_name.lower() in result.stdout.lower()
        except:
            return False


class ConsoleMonitor:
    """プラットフォーム固有のコンソール監視処理"""
    
    @staticmethod
    def check_console_status(monitor_count: int, grace_period_checks: int) -> dict:
        """コンソールの状態をチェック"""
        system = platform.system()
        result = {'closed': False, 'log_message': None}
        
        try:
            if system == "Darwin":  # macOS
                # First check if Terminal app has any windows
                check_result = subprocess.run(
                    ['osascript', '-e', 'tell application "Terminal" to count windows'],
                    capture_output=True, text=True
                )
                
                if check_result.returncode != 0 or check_result.stdout.strip() == "0":
                    result['closed'] = True
                else:
                    # Check if any window contains steamcmd
                    check_script = '''
                    tell application "Terminal"
                        set steamcmdFound to false
                        set windowCount to count windows
                        repeat with w in windows
                            try
                                repeat with t in tabs of w
                                    if processes of t contains "steamcmd" or name of t contains "steamcmd" then
                                        set steamcmdFound to true
                                        exit repeat
                                    end if
                                end repeat
                            end try
                        end repeat
                        return steamcmdFound
                    end tell
                    '''
                    check_result = subprocess.run(
                        ['osascript', '-e', check_script],
                        capture_output=True, text=True
                    )
                    
                    # Also check using ps command as backup
                    ps_result = subprocess.run(
                        ['ps', 'aux'],
                        capture_output=True, text=True
                    )
                    has_steamcmd_process = 'steamcmd' in ps_result.stdout.lower()
                    
                    if check_result.stdout.strip() != "true" and not has_steamcmd_process:
                        result['closed'] = True
                        result['log_message'] = f"macOS: SteamCMDコンソールが見つかりません (AppleScript: {check_result.stdout.strip()}, ps: {has_steamcmd_process})"
                    else:
                        # 1秒ごとに出力（0.5秒 × 2）
                        if monitor_count % 2 == 0:
                            result['log_message'] = f"[コンソール監視] 存在確認OK - Terminal windows: {check_result.stdout.strip()}, steamcmd process: {has_steamcmd_process} (check #{monitor_count})"
                
            elif system == "Windows":
                # Check if steamcmd.exe process is still running
                check_result = subprocess.run(
                    ['tasklist', '/FI', 'IMAGENAME eq steamcmd.exe'],
                    capture_output=True, text=True
                )

                has_steamcmd = "steamcmd.exe" in check_result.stdout

                # Apply grace period - don't close console during initial startup
                if not has_steamcmd:
                    if monitor_count > grace_period_checks:
                        result['closed'] = True
                        result['log_message'] = "Windows: SteamCMDコンソールが見つかりません"
                    else:
                        result['log_message'] = f"Windows: 起動待機中... ({monitor_count}/{grace_period_checks})"
                else:
                    # 1秒ごとに出力（0.5秒 × 2）
                    if monitor_count % 2 == 0:
                        result['log_message'] = f"[コンソール監視] 存在確認OK - steamcmd.exe検出 (check #{monitor_count})"
            else:
                # Linux - 現在は未実装
                pass
                
        except Exception as e:
            result['log_message'] = f"コンソールチェックエラー: {e}"
            
        return result


class WindowsCommandSender:
    """Windows環境でのコマンド送信処理"""
    
    @staticmethod
    def send_command_to_console(command: str, process_id: int = None, log_callback=None) -> bool:
        """コンソールウィンドウにコマンドを送信"""
        if platform.system() != "Windows":
            return False
        
        try:
            # PowerShellスクリプトでコマンドを送信
            escaped_command = command.replace('"', '`"').replace("'", "''")
            
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

        [DllImport("user32.dll")]
        public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

        [DllImport("imm32.dll")]
        public static extern IntPtr ImmGetContext(IntPtr hWnd);

        [DllImport("imm32.dll")]
        public static extern bool ImmReleaseContext(IntPtr hWnd, IntPtr hIMC);

        [DllImport("imm32.dll")]
        public static extern bool ImmGetOpenStatus(IntPtr hIMC);

        [DllImport("imm32.dll")]
        public static extern bool ImmSetOpenStatus(IntPtr hIMC, bool fOpen);

        public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

        public const int SW_RESTORE = 9;
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
        if ($title -like "*steamcmd*" -or $title -like "*MornSteamCMD*") {{
            $procId = 0
            [InputHelper]::GetWindowThreadProcessId($hWnd, [ref]$procId) | Out-Null
            $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue

            $obj = [PSCustomObject]@{{
                Handle = $hWnd
                Title = $title
                PID = $procId
                ProcessName = if ($proc) {{ $proc.ProcessName }} else {{ "Unknown" }}
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
$targetWindow = $null
foreach ($cand in $candidates) {{
    if ($cand.Title -like "*MornSteamCMD*") {{
        $targetWindow = $cand
        break
    }}
}}
if ($targetWindow -eq $null) {{
    foreach ($cand in $candidates) {{
        if ($cand.ProcessName -eq "conhost") {{
            $targetWindow = $cand
            break
        }}
    }}
}}
if ($targetWindow -eq $null) {{
    $targetWindow = $candidates[0]
}}

# Save current foreground window
$originalWindow = [InputHelper]::GetForegroundWindow()

# Focus and send (minimal delay)
[InputHelper]::SetForegroundWindow($targetWindow.Handle) | Out-Null
Start-Sleep -Milliseconds 80

try {{
    # Copy command to clipboard
    Set-Clipboard -Value "{escaped_command}"

    # Force disable IME using Windows API
    $hIMC = [InputHelper]::ImmGetContext($targetWindow.Handle)
    if ($hIMC -ne [IntPtr]::Zero) {{
        $imeStatus = [InputHelper]::ImmGetOpenStatus($hIMC)
        if ($imeStatus) {{
            # IME is ON, turn it OFF
            [InputHelper]::ImmSetOpenStatus($hIMC, $false) | Out-Null
        }}
        [InputHelper]::ImmReleaseContext($targetWindow.Handle, $hIMC) | Out-Null
    }}
    Start-Sleep -Milliseconds 50

    # Paste from clipboard (supports Japanese) + enter
    [System.Windows.Forms.SendKeys]::SendWait("^v{{ENTER}}")
    Write-Output "SUCCESS"
}} catch {{
    Write-Output "ERROR: $_"
    exit 1
}} finally {{
    # Restore immediately
    if ($originalWindow -ne [IntPtr]::Zero) {{
        [InputHelper]::SetForegroundWindow($originalWindow) | Out-Null
    }}
}}
'''
            
            result = subprocess.run(
                ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if "SUCCESS" in result.stdout:
                if log_callback:
                    log_callback(f"✓ コマンドを自動送信しました: {command}")
                return True
            elif "NOTFOUND" in result.stdout:
                if log_callback:
                    log_callback("✗ エラー: SteamCMDコンソールウィンドウが見つかりませんでした。")
                return False
            else:
                if log_callback:
                    log_callback(f"✗ 自動送信エラー: {result.stderr}")
                return False
            
        except Exception as e:
            if log_callback:
                log_callback(f"コマンド送信エラー: {e}")
            return False