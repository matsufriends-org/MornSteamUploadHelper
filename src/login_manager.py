"""Login management functionality for Steam Upload Helper"""

import flet as ft
import time
import threading
from pathlib import Path
import os

from ui_helpers import DialogBuilder, ButtonStateManager
from platform_helpers import SteamCMDLauncher, LoginMonitor


class LoginManager:
    """Steamログイン処理を管理するクラス"""
    
    def __init__(self, helper, page: ft.Page):
        self.helper = helper
        self.page = page
        self.login_in_progress = False
        
        # UIコンポーネント
        self.username_field = None
        self.password_field = None
        self.steam_guard_field = None
        self.login_status = None
        self.login_button = None
        self.confirm_login_button = None
        self.login_error_text = None
        
        # コールバック
        self.on_login_success = None
        self.on_login_failure = None
        self.enable_controls_callback = None
    
    def create_ui_components(self):
        """ログイン関連のUIコンポーネントを作成"""
        self.username_field = ft.TextField(
            label="Steam ユーザー名 *",
            value=self.helper.settings.get("username", ""),
            width=300,
            autofocus=True
        )
        
        self.password_field = ft.TextField(
            label="パスワード *",
            password=True,
            can_reveal_password=True,
            width=200
        )
        
        self.steam_guard_field = ft.TextField(
            label="Steam Guard コード (任意)",
            width=250
        )
        
        self.login_status = ft.Text(
            "未ログイン", 
            color=ft.Colors.RED, 
            weight=ft.FontWeight.BOLD
        )
        
        self.login_button = ft.ElevatedButton(
            "コンソールを開いて自動ログイン",
            icon=ft.Icons.TERMINAL,
            on_click=self._login_button_click
        )
        
        self.login_error_text = ft.Text(
            "",
            size=11,
            color=ft.Colors.ERROR,
            visible=False
        )
    
    def check_content_builder_paths(self) -> bool:
        """ContentBuilderとSteamCMDのパスをチェック"""
        content_builder_path = self.helper.settings.get("content_builder_path")
        if not content_builder_path:
            self.login_button.disabled = True
            self.login_error_text.value = "ContentBuilderフォルダが設定されていません。基本設定から設定してください。"
            self.login_error_text.visible = True
            return False
        
        # プラットフォーム固有のSteamCMDパス取得
        steamcmd_path = SteamCMDLauncher.get_steamcmd_path(content_builder_path)
        
        if not steamcmd_path or not os.path.exists(steamcmd_path):
            self.login_button.disabled = True
            self.login_error_text.value = f"SteamCMDが見つかりません: {steamcmd_path if steamcmd_path else 'None'}"
            self.login_error_text.visible = True
            return False
        
        # 正常
        self.login_button.disabled = False
        self.login_error_text.visible = False
        
        # 設定を更新
        self.helper.settings["steamcmd_path"] = steamcmd_path
        self.helper.save_settings()
        
        return True
    
    def _login_button_click(self, e):
        """ログインボタンクリック処理"""
        if self.login_in_progress:
            self._log_message("ログイン処理中...")
            return
        
        self.login_in_progress = True
        try:
            self.login_to_steam_console()
        finally:
            self.login_in_progress = False
    
    def login_to_steam_console(self):
        """Steamコンソールを開いてログイン処理を開始"""
        # 入力検証
        if not self.username_field.value or not self.password_field.value:
            DialogBuilder.show_error_dialog(self.page, "ユーザー名とパスワードは必須です！")
            return
        
        # ContentBuilderパスチェック
        if not self.check_content_builder_paths():
            return
        
        steamcmd_path = self.helper.settings.get("steamcmd_path")
        if not steamcmd_path:
            DialogBuilder.show_error_dialog(self.page, "SteamCMDのパスが設定されていません。基本設定を確認してください。")
            return
        
        # 既存のコンソールをクリア
        self.helper.steamcmd_terminal = False
        self.helper.is_logged_in = False
        
        self._log_message("SteamCMDコンソールを起動しています...")
        
        # プラットフォーム固有の起動処理
        result = SteamCMDLauncher.launch_steamcmd_console(
            steamcmd_path,
            self.username_field.value,
            self.password_field.value,
            self.steam_guard_field.value,
            self._log_message
        )
        
        if result.get("terminal"):
            self.helper.steamcmd_terminal = True
            
            if "process_id" in result:
                self.helper.steamcmd_cmd_process_id = result["process_id"]
            
            self.login_status.value = "Steamコンソールが開きました - ログインを待っています..."
            self.login_status.color = ft.Colors.ORANGE
            self.login_button.disabled = True
            
            if self.enable_controls_callback:
                self.enable_controls_callback(False)
            
            # コンソール監視を即座に開始（ログイン前から監視する）
            if hasattr(self.helper, '_start_console_monitor_callback') and self.helper._start_console_monitor_callback:
                self._log_message("コンソール監視をログイン前に開始します")
                self.helper._start_console_monitor_callback()
            
            # ログイン監視開始
            self._start_login_monitoring(steamcmd_path)
            
            # ログイン待機ダイアログを表示
            self._show_login_waiting_dialog()
            
            self.page.update()
    
    def _start_login_monitoring(self, steamcmd_path: str):
        """ログイン状態の監視を開始"""
        callbacks = {
            'on_success': self._handle_login_success,
            'on_failure': self._handle_login_failure,
            'on_process_ended': self._handle_process_ended,
            'on_timeout': self._handle_login_timeout,
            'on_mobile_2fa': self._handle_mobile_2fa
        }
        
        LoginMonitor.monitor_login(
            steamcmd_path,
            self.username_field.value,
            callbacks,
            timeout=3600,  # 1時間待機（実質無限）
            log_callback=self._log_message
        )
    
    def _handle_login_success(self):
        """ログイン成功時の処理"""
        self._log_message("Steamログインが正常に完了しました！")
        self.helper.is_logged_in = True
        self.login_status.value = f"{self.username_field.value} としてログイン中"
        self.login_status.color = ft.Colors.GREEN
        
        # ログイン待機ダイアログを閉じる
        if hasattr(self, '_login_waiting_dialog') and self._login_waiting_dialog:
            DialogBuilder._close_dialog(self.page, self._login_waiting_dialog)
            self._login_waiting_dialog = None
        
        # モバイル2FAダイアログが開いていれば閉じる
        if hasattr(self, '_mobile_2fa_dialog') and self._mobile_2fa_dialog:
            DialogBuilder._close_dialog(self.page, self._mobile_2fa_dialog)
            self._mobile_2fa_dialog = None
        
        # ユーザー名を保存
        self.helper.settings["username"] = self.username_field.value
        self.helper.save_settings()
        
        # セキュリティのため一時ファイルをクリーンアップ
        self._cleanup_temp_scripts()
        
        # パスワードフィールドをクリア
        self.password_field.value = ""
        self.steam_guard_field.value = ""
        
        if self.enable_controls_callback:
            self.enable_controls_callback(True)
        
        if self.on_login_success:
            self.on_login_success()
        
        self.page.update()
    
    def _handle_login_failure(self):
        """ログイン失敗時の処理"""
        self._log_message("ログイン失敗を検出しました")

        # ログイン待機ダイアログを閉じる
        if hasattr(self, '_login_waiting_dialog') and self._login_waiting_dialog:
            DialogBuilder._close_dialog(self.page, self._login_waiting_dialog)
            self._login_waiting_dialog = None

        self.helper.is_logged_in = False
        self.helper.steamcmd_terminal = False
        self.login_button.disabled = False

        # シンプルなエラー表示のみ（ポップアップは表示しない）
        self.login_status.value = "ログイン失敗 - 詳細はコンソールを確認してください"
        self.login_status.color = ft.Colors.RED
        
        if self.enable_controls_callback:
            self.enable_controls_callback(False)
        
        if self.on_login_failure:
            self.on_login_failure()
        
        self.page.update()
    
    def _handle_process_ended(self):
        """プロセス終了時の処理"""
        self._log_message("SteamCMDプロセスが終了しました。")
        
        # ログイン待機ダイアログを閉じる
        if hasattr(self, '_login_waiting_dialog') and self._login_waiting_dialog:
            DialogBuilder._close_dialog(self.page, self._login_waiting_dialog)
            self._login_waiting_dialog = None
        
        self.helper.is_logged_in = False
        self.helper.steamcmd_terminal = False
        self.login_status.value = "未ログイン"
        self.login_status.color = ft.Colors.RED
        self.login_button.disabled = False
        
        if self.enable_controls_callback:
            self.enable_controls_callback(False)
        
        self.page.update()
    
    def _handle_login_timeout(self):
        """ログイン監視タイムアウト時の処理"""
        # タイムアウトしても待機を続ける（ダイアログは閉じない）
        self._log_message("ログイン監視を継続しています...")
    
    def _handle_mobile_2fa(self):
        """モバイル2FA待機時の処理"""
        self._log_message("モバイル認証を検出しました。Steamモバイルアプリで承認してください。")
        self.login_status.value = "モバイルアプリでの承認を待っています..."
        self.login_status.color = ft.Colors.ORANGE
        self.page.update()
        
        # モバイル2FAダイアログを表示
        self._show_mobile_2fa_dialog()
    
    def _show_login_waiting_dialog(self):
        """ログイン待機ダイアログを表示"""
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Steamログイン中"),
            content=ft.Column([
                ft.ProgressRing(width=40, height=40, stroke_width=3),
                ft.Text("ログインを処理しています...", size=14),
                ft.Container(height=10),
                ft.Text("コンソールウィンドウでログイン処理が完了するまでお待ちください", 
                       size=12, color=ft.Colors.GREY),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            actions=[]  # ボタンなし（キャンセル不可）
        )
        
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
        
        self._login_waiting_dialog = dlg
    
    def _cleanup_temp_scripts(self):
        """一時スクリプトファイルをクリーンアップ"""
        # Get script directory path
        script_dir = Path(__file__).parent / "configs"
        
        temp_files = [
            script_dir / "steamcmd_session.sh",
            script_dir / "steamcmd_session.bat",
            script_dir / "steamcmd_2fa_code.txt"
        ]
        
        for file_path in temp_files:
            if file_path.exists():
                try:
                    file_path.unlink()
                    self._log_message(f"一時ファイルを削除: {file_path}")
                except:
                    pass
    
    def _log_message(self, message: str):
        """ログメッセージ出力"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def _show_mobile_2fa_dialog(self):
        """モバイル2FA専用のダイアログを表示"""
        # 既存のログイン待機ダイアログを閉じる
        if hasattr(self, '_login_waiting_dialog') and self._login_waiting_dialog:
            DialogBuilder._close_dialog(self.page, self._login_waiting_dialog)
            self._login_waiting_dialog = None
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Steam Guard モバイル認証"),
            content=ft.Column([
                ft.Icon(ft.Icons.PHONE_ANDROID, size=50, color=ft.Colors.BLUE),
                ft.Text("Steamモバイルアプリで承認してください", size=16),
                ft.Container(height=10),
                ft.ProgressRing(width=30, height=30, stroke_width=3),
                ft.Text("承認を待っています...", size=12, color=ft.Colors.GREY),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            actions=[]  # ボタンなし（キャンセル不可）
        )
        
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
        
        # 承認が完了したら自動的にダイアログを閉じる
        self._mobile_2fa_dialog = dlg
    
    def _cancel_mobile_2fa(self, dlg):
        """モバイル2FA待機をキャンセル"""
        DialogBuilder._close_dialog(self.page, dlg)
        self._mobile_2fa_dialog = None
    
    def show_2fa_dialog(self):
        """2FA認証ダイアログを表示"""
        auth_code_field = ft.TextField(
            label="Steam Guardコードを入力（任意）",
            autofocus=True,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        waiting_text = ft.Text("モバイルアプリでの承認を待っています...", visible=False)
        progress_ring = ft.ProgressRing(width=16, height=16, stroke_width=2, visible=False)
        
        def cancel_2fa(dlg):
            self.helper.waiting_for_mobile_2fa = False
            DialogBuilder._close_dialog(self.page, dlg)
        
        def submit_2fa_code(code, dlg):
            if code:
                self.helper.steam_guard_code = code
                DialogBuilder._close_dialog(self.page, dlg)
                # 2FAコードでログイン再試行
                self.steam_guard_field.value = code
                self.login_to_steam_console()
        
        def wait_for_mobile_approval(dlg, waiting_text, progress_ring):
            waiting_text.visible = True
            progress_ring.visible = True
            self.page.update()
            self.helper.waiting_for_mobile_2fa = True
            DialogBuilder._close_dialog(self.page, dlg)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Steam Guard 認証"),
            content=ft.Column([
                ft.Text("以下のいずれかの方法を選択してください："),
                ft.Text("1. Steamモバイルアプリでログインリクエストを承認", size=14),
                ft.Text("2. Steamモバイルアプリまたはメールからコードを入力：", size=14),
                auth_code_field,
                ft.Row([progress_ring, waiting_text], spacing=10)
            ], height=200, spacing=10),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: cancel_2fa(dlg)),
                ft.TextButton("コードを送信", on_click=lambda e: submit_2fa_code(auth_code_field.value, dlg)),
                ft.TextButton("モバイルで承認しました", on_click=lambda e: wait_for_mobile_approval(dlg, waiting_text, progress_ring))
            ]
        )
        
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
        
        return dlg, auth_code_field