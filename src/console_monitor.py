"""
Console monitoring functions for Steam Upload Helper.
"""

import platform
import subprocess
import threading
import time
from pathlib import Path
from utils import log_message, cleanup_temp_scripts


def start_console_monitor(helper, login_status, login_button, enable_controls_func, page):
    """Start monitoring the console to detect if it's closed."""
    if helper.console_monitor_thread and helper.console_monitor_thread.is_alive():
        return  # Already monitoring
    
    def monitor_console():
        """Monitor the console window status."""
        log_message("コンソール監視を開始しました...")
        monitor_count = 0
        grace_period_checks = 2  # First ~2.5 seconds grace period for process startup

        while helper.steamcmd_terminal:
            monitor_count += 1
            console_closed = False

            try:
                if platform.system() == "Darwin":  # macOS
                    # First check if Terminal app has any windows
                    result = subprocess.run(
                        ['osascript', '-e', 'tell application "Terminal" to count windows'],
                        capture_output=True, text=True
                    )
                    
                    if result.returncode != 0 or result.stdout.strip() == "0":
                        console_closed = True
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
                        result = subprocess.run(
                            ['osascript', '-e', check_script],
                            capture_output=True, text=True
                        )
                        
                        # Also check using ps command as backup
                        ps_result = subprocess.run(
                            ['ps', 'aux'],
                            capture_output=True, text=True
                        )
                        has_steamcmd_process = 'steamcmd' in ps_result.stdout.lower()
                        
                        if result.stdout.strip() != "true" and not has_steamcmd_process:
                            console_closed = True
                            log_message(f"macOS: SteamCMDコンソールが見つかりません (AppleScript: {result.stdout.strip()}, ps: {has_steamcmd_process})")
                        else:
                            if monitor_count % 10 == 0:
                                log_message(f"macOS: SteamCMDコンソール検出 (AppleScript: {result.stdout.strip()}, ps: {has_steamcmd_process})")
                    
                elif platform.system() == "Windows":
                    # Check if steamcmd.exe process is still running
                    try:
                        # Check for steamcmd.exe process (fast check only)
                        result = subprocess.run(
                            ['tasklist', '/FI', 'IMAGENAME eq steamcmd.exe'],
                            capture_output=True, text=True
                        )

                        has_steamcmd = "steamcmd.exe" in result.stdout

                        # Apply grace period - don't close console during initial startup
                        if not has_steamcmd:
                            if monitor_count > grace_period_checks:
                                console_closed = True
                                log_message(f"Windows: SteamCMDコンソールが見つかりません")
                            else:
                                log_message(f"Windows: 起動待機中... ({monitor_count}/{grace_period_checks})")
                        else:
                            if monitor_count % 10 == 0:
                                log_message(f"Windows: SteamCMDコンソール検出")
                    except Exception as e:
                        log_message(f"Windows コンソールチェックエラー: {e}")
                
                if console_closed:
                    log_message("コンソールが閉じられました！ログイン状態をリセットしています...")
                    
                    # Disable upload controls only if user was logged in
                    if helper.is_logged_in:
                        enable_controls_func(False)
                    
                    # Reset login state
                    helper.is_logged_in = False
                    helper.steamcmd_terminal = False
                    login_status.value = "未ログイン"
                    login_status.color = "red"
                    
                    # Re-enable login button
                    login_button.disabled = False
                    
                    page.update()
                    break
                
                # Check every 0.5 seconds (faster!)
                time.sleep(0.5)
            except Exception as e:
                log_message(f"コンソール監視エラー: {e}")
            
        log_message("コンソール監視を停止しました。")
        helper.console_monitor_thread = None
        log_message(f"監視終了理由: steamcmd_terminal={helper.steamcmd_terminal}")
    
    # Start monitoring thread
    helper.console_monitor_thread = threading.Thread(target=monitor_console, daemon=True)
    helper.console_monitor_thread.start()
    log_message(f"コンソール監視スレッドを開始しました (thread alive: {helper.console_monitor_thread.is_alive()})")