"""Upload management functionality for Steam Upload Helper"""

import flet as ft
import os
import time
import webbrowser
import platform
import subprocess
from pathlib import Path

from ui_helpers import DialogBuilder, PlatformCommands
from command_sender import CommandSender


class UploadManager:
    """アップロード処理を管理するクラス"""
    
    def __init__(self, helper, page: ft.Page):
        self.helper = helper
        self.page = page
        self.upload_in_progress = False
        
        # UIコンポーネント
        self.upload_button = None
        self.login_status_text = None
        self.config_status_text = None
        self.progress_bar = None
        
        # 現在の設定
        self.current_config = None
        self.current_config_name = None
        
        # コールバック
        self.on_upload_complete = None
    
    def create_ui_components(self):
        """アップロード関連のUIコンポーネントを作成"""
        self.upload_button = ft.ElevatedButton(
            "Steamにアップロード",
            on_click=lambda e: self.run_upload(),
            icon=ft.Icons.UPLOAD,
            style=ft.ButtonStyle(
                color={
                    ft.ControlState.DEFAULT: ft.Colors.WHITE,
                    ft.ControlState.DISABLED: ft.Colors.GREY_400,
                },
                bgcolor={
                    ft.ControlState.DEFAULT: ft.Colors.BLUE,
                    ft.ControlState.DISABLED: ft.Colors.GREY_300,
                },
            ),
            disabled=True
        )
        
        self.login_status_text = ft.Text(
            "❌ コンソールを開いてログインしている",
            size=14
        )
        
        self.config_status_text = ft.Text(
            "❌ アップロード設定を選択している",
            size=14
        )
        
        self.progress_bar = ft.ProgressBar(width=740, visible=False)
    
    def update_upload_button_state(self, is_logged_in: bool, has_config: bool):
        """アップロードボタンの状態を更新"""
        # ステータスアイコンを更新
        self.login_status_text.value = f"{'✅' if is_logged_in else '❌'} コンソールを開いてログインしている"
        self.config_status_text.value = f"{'✅' if has_config else '❌'} アップロード設定を選択している"
        
        # 両方の条件が満たされた時のみアップロードボタンを有効化
        self.upload_button.disabled = not (is_logged_in and has_config)
        self.page.update()
    
    def run_upload(self):
        """アップロード処理を実行"""
        if self.upload_in_progress:
            self._log_message("アップロード処理中...")
            return
        
        if not self.helper.is_logged_in:
            DialogBuilder.show_error_dialog(self.page, "Steamにログインしてください！")
            return
        
        # 現在の設定を取得
        config_name = self.current_config_name
        config = self.current_config
        
        if not config or not config_name:
            DialogBuilder.show_error_dialog(self.page, "アップロード設定を選択してください！")
            return
        
        # コンテンツパスの検証
        content_path = config.get("content_path", "")
        if not content_path or not os.path.exists(content_path):
            DialogBuilder.show_error_dialog(
                self.page, 
                f"コンテンツパスが存在しません: {content_path}"
            )
            return
        
        self.upload_in_progress = True
        self.upload_button.disabled = True
        self.progress_bar.visible = True
        self.page.update()
        
        try:
            self._log_message(f"アップロード開始: {config_name}")
            self._log_message(f"App ID: {config.get('app_id')}")
            self._log_message(f"Depot ID: {config.get('depot_id')}")
            self._log_message(f"ブランチ: {config.get('branch', 'なし')}")
            self._log_message(f"コンテンツパス: {content_path}")
            
            # VDFファイル生成とアップロード実行
            self._execute_upload(config_name, config, content_path)
            
        except Exception as ex:
            self._log_message(f"アップロード中にエラー: {str(ex)}")
            DialogBuilder.show_error_dialog(self.page, f"アップロードエラー: {str(ex)}")
        finally:
            self.upload_button.disabled = False
            self.upload_in_progress = False
            self.progress_bar.visible = False
            self.page.update()
    
    def _execute_upload(self, config_name: str, config: dict, content_path: str):
        """実際のアップロード処理を実行"""
        # VDFファイルを生成
        vdf_path = self.helper.create_vdf_file(config_name, config)
        
        if not vdf_path:
            self._log_message("VDFファイルの生成に失敗しました")
            return
        
        self._log_message(f"VDFファイルを生成: {vdf_path}")
        
        # アップロードコマンドを構築
        upload_command = self._build_upload_command(vdf_path)
        
        self._log_message(f"実行コマンド: {upload_command}")
        
        # プラットフォーム別の実行（この分岐は必要なので残す）
        if platform.system() == "Windows":
            self._execute_upload_windows(upload_command)
        else:
            self._execute_upload_unix(upload_command)
    
    def _build_upload_command(self, vdf_path: str) -> str:
        """アップロードコマンドを構築"""
        # VDFファイルの絶対パスを取得
        abs_vdf_path = os.path.abspath(vdf_path)
        
        # パスにスペースがある場合は引用符で囲む
        if " " in abs_vdf_path:
            abs_vdf_path = f'"{abs_vdf_path}"'
        
        # SteamCMD内での正しいコマンド形式（+は起動時オプションなので、コンソール内では使わない）
        return f"run_app_build {abs_vdf_path}"
    
    def _execute_upload_windows(self, upload_command: str):
        """Windows環境でのアップロード実行"""
        self._log_message("自動コマンド送信を試行中...")
        
        # 共通のCommandSenderを使用
        success = CommandSender.send_command(
            upload_command, 
            "Steam>",
            process_id=getattr(self.helper, 'steamcmd_cmd_process_id', None),
            log_callback=self._log_message
        )
        
        if success:
            self._log_message("✓ アップロードコマンドを自動実行しました")
            self._log_message("Steamコンソールでアップロードを開始しました。進行状況はコンソールで確認してください。")
        else:
            self._log_message("自動送信に失敗しました。")
            # 失敗時は手動でダイアログを表示（フォールバック）
            self._show_manual_command_dialog(upload_command)
    
    def _execute_upload_unix(self, upload_command: str):
        """Unix系環境でのアップロード実行"""
        # この分岐もプラットフォーム固有の処理が異なるため必要
        if platform.system() == "Darwin":
            self._execute_upload_macos(upload_command)
        else:
            # Linuxでは手動実行を促す
            self._show_manual_command_dialog(upload_command)
    
    def _execute_upload_macos(self, upload_command: str):
        """macOS環境でのアップロード実行"""
        self._log_message("自動コマンド送信を試行中...")
        
        # 共通のCommandSenderを使用 - Steam>を含むウィンドウを自動で探す
        success = CommandSender.send_command(
            upload_command,
            "Steam>",
            log_callback=self._log_message
        )
        
        if success:
            self._log_message("✓ アップロードコマンドを自動実行しました")
            self._log_message("Steamコンソールでアップロードを開始しました。進行状況はコンソールで確認してください。")
        else:
            self._log_message("自動送信に失敗しました。")
            # 失敗時は手動でダイアログを表示（フォールバック）
            self._show_manual_command_dialog(upload_command)
    
    def _show_manual_command_dialog(self, upload_command: str):
        """手動でコマンドを実行するためのダイアログを表示"""
        # クリップボードにコピー
        self.page.set_clipboard(upload_command)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("アップロードコマンド"),
            content=ft.Column([
                ft.Text("以下のコマンドをSteamCMDコンソールで実行してください："),
                ft.Container(
                    content=ft.Text(upload_command, selectable=True),
                    bgcolor=ft.Colors.GREY_900,
                    padding=10,
                    border_radius=5
                ),
                ft.Text("(コマンドはクリップボードにコピーされました)", 
                       size=12, color=ft.Colors.GREY)
            ], width=400),
            actions=[
                ft.TextButton("OK", on_click=lambda e: DialogBuilder._close_dialog(self.page, dlg))
            ]
        )
        
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
        
        self._log_message(f"Please run in SteamCMD console: {upload_command}")
    
    def _log_message(self, message: str):
        """ログメッセージ出力"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")