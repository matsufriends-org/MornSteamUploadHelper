"""
Console monitoring functions for Steam Upload Helper.
"""

import threading
import time
from pathlib import Path
from .utils import log_message, cleanup_temp_scripts
from .platform_helpers import ConsoleMonitor as PlatformConsoleMonitor


def start_console_monitor(helper, login_status, login_button, enable_controls_func, page):
    """Start monitoring the console to detect if it's closed."""
    log_message(f"[コンソール監視] start_console_monitor呼び出し")
    log_message(f"[コンソール監視] helper.steamcmd_terminal = {helper.steamcmd_terminal}")
    log_message(f"[コンソール監視] 既存スレッド: {helper.console_monitor_thread if hasattr(helper, 'console_monitor_thread') else 'なし'}")
    log_message(f"[コンソール監視] helper.is_logged_in = {helper.is_logged_in if hasattr(helper, 'is_logged_in') else 'None'}")
    
    if hasattr(helper, 'console_monitor_thread') and helper.console_monitor_thread and helper.console_monitor_thread.is_alive():
        log_message(f"[コンソール監視] 既に監視中のため終了")
        return  # Already monitoring
    
    def monitor_console():
        """Monitor the console window status."""
        log_message("[コンソール監視] monitor_console関数が開始されました")
        log_message(f"[コンソール監視] 監視対象: helper.steamcmd_terminal = {helper.steamcmd_terminal}")
        monitor_count = 0
        grace_period_checks = 10  # First ~5 seconds grace period for process startup
        
        log_message(f"[コンソール監視] whileループ開始前: helper.steamcmd_terminal = {helper.steamcmd_terminal}")
        while helper.steamcmd_terminal:
            monitor_count += 1
            console_closed = False
            
            if monitor_count == 1:
                log_message(f"[コンソール監視] whileループ内に入りました (monitor_count={monitor_count})")

            try:
                # OS固有のコンソールチェックをplatform_helpersに委譲
                console_status = PlatformConsoleMonitor.check_console_status(monitor_count, grace_period_checks)
                console_closed = console_status.get('closed', False)
                
                if console_status.get('log_message'):
                    log_message(console_status['log_message'])
                
                if console_closed:
                    log_message("⚠️ コンソールが閉じられました！ログイン状態をリセットしています...")
                    
                    # Reset state
                    helper.is_logged_in = False
                    helper.steamcmd_terminal = False
                    
                    # Notify through main app callback
                    if hasattr(helper, 'on_console_closed_callback') and helper.on_console_closed_callback:
                        helper.on_console_closed_callback()
                    
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
    log_message(f"[コンソール監視] スレッドを開始しました (thread alive: {helper.console_monitor_thread.is_alive()})")
    
    # Return the thread for reference
    return helper.console_monitor_thread