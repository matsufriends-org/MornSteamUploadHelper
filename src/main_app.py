"""
Main application class for Morn Steam Upload Helper

This module contains the main application logic, coordinating between
different managers for login, configuration, upload, and system settings.
"""

import flet as ft
import os
import time
import platform

from .constants import *
from .steam_upload_helper import SteamUploadHelper
from .utils import *
from .dialogs import *

# UI 定数
SECTION_PADDING = 15  # セクション内のpadding
SECTION_VERTICAL_PADDING = 0  # セクション間の垂直padding
HEADER_PADDING = 15  # ヘッダーのpadding
HEADER_BOTTOM_PADDING = 5  # ヘッダー下部のpadding
SECTION_TITLE_SPACING = 0  # セクションタイトルと内容の間隔
FIELD_SPACING = 10  # フィールド間の間隔（横・縦共通）
FIELD_COLUMN_SPACING = 5  # フィールド列の間隔
BUTTON_SPACING = 10  # ボタン間の間隔
CONTENT_SPACING = 10  # 一般的なコンテンツ間隔
SMALL_SPACING = 5  # 小さい間隔
TINY_SPACING = 2  # 極小間隔
LARGE_SPACING = 20  # 大きい間隔（左右分割など）

# Import managers
from .login_manager import LoginManager
from .config_manager import ConfigManager
from .upload_manager import UploadManager
from .system_settings_manager import SystemSettingsManager
from .ui_helpers import DialogBuilder, PlatformCommands
try:
    from .console_monitor import start_console_monitor
except ImportError:
    # Console monitoring is optional
    def start_console_monitor(*args, **kwargs):
        return None


class SteamUploadApp:
    """メインアプリケーションクラス"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.helper = SteamUploadHelper()
        
        # マネージャーの初期化
        self.login_manager = LoginManager(self.helper, page)
        self.config_manager = ConfigManager(self.helper, page)
        self.upload_manager = UploadManager(self.helper, page)
        self.system_settings_manager = SystemSettingsManager(self.helper, page)
        
        # コールバックの設定
        self._setup_callbacks()
        
        # UIの初期化
        self._setup_page()
        self._create_ui_components()
        self._build_ui()
        
        # 初期状態の設定
        self._initialize_state()
    
    def _setup_callbacks(self):
        """マネージャー間のコールバックを設定"""
        # Login Manager callbacks
        self.login_manager.on_login_success = self._handle_login_success
        self.login_manager.on_login_failure = self._handle_login_failure
        self.login_manager.enable_controls_callback = self._enable_controls
        
        # コンソール監視コールバックをhelperに設定
        self.helper._start_console_monitor_callback = self._start_console_monitor_wrapper
        
        # Config Manager callbacks
        self.config_manager.on_config_loaded = self._handle_config_loaded
        self.config_manager.on_config_changed = self._handle_config_changed
        
        # System Settings callbacks
        self.system_settings_manager.on_settings_changed = self._handle_settings_changed
    
    def _setup_page(self):
        """ページの基本設定"""
        self.page.title = APP_NAME
        self.page.window.width = WINDOW_WIDTH
        self.page.window.height = WINDOW_HEIGHT
        self.page.padding = 0
        self.page.scroll = ft.ScrollMode.AUTO
    
    def _create_ui_components(self):
        """UIコンポーネントを作成"""
        # 各マネージャーでUIコンポーネントを作成
        self.login_manager.create_ui_components()
        self.config_manager.create_ui_components()
        self.upload_manager.create_ui_components()
        self.system_settings_manager.create_ui_components()
        
        # その他のUIコンポーネント
        self.console_monitor_wrapper = None
    
    def _build_ui(self):
        """UIを構築"""
        content = ft.Column([
            # ヘッダー
            self._build_header(),
            
            # 1. Steamログイン
            self._build_login_section(),
            
            # 2. アップロード設定
            self._build_config_section(),
            
            # 3. アップロード
            self._build_upload_section(),
            
            # 4. ダウンロード
            self._build_download_section(),
        ])
        
        self.page.add(content)
    
    def _build_header(self):
        """ヘッダーセクションを構築"""
        from .constants import APP_VERSION
        import sys
        import os

        # アイコンのパスを取得（PyInstaller対応）
        if getattr(sys, 'frozen', False):
            # PyInstallerでビルドされた場合
            base_path = sys._MEIPASS
        else:
            # 通常のPythonスクリプトとして実行された場合
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        icon_path = os.path.join(base_path, "img", "icon-512.png")

        return ft.Container(
            content=ft.Row([
                ft.Image(src=icon_path, width=32, height=32, fit=ft.ImageFit.CONTAIN) if os.path.exists(icon_path) else ft.Container(),
                ft.Text("Morn Steam アップロードヘルパー", size=24, weight=ft.FontWeight.BOLD),
                ft.Text(f"v{APP_VERSION}", size=14, color=ft.Colors.GREY_700),
                ft.Container(expand=True),
                self.login_manager.login_status,
                ft.ElevatedButton(
                    "基本設定",
                    icon=ft.Icons.SETTINGS,
                    on_click=lambda e: self.system_settings_manager.show_system_settings_dialog()
                )
            ]),
            padding=ft.padding.only(left=HEADER_PADDING, right=HEADER_PADDING, top=HEADER_PADDING, bottom=HEADER_BOTTOM_PADDING)
        )
    
    def _build_login_section(self):
        """ログインセクションを構築"""
        return ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("1. Steam ログイン", size=18, weight=ft.FontWeight.W_500),
                            ft.Container(expand=True),
                            self.login_manager.login_error_text,
                        ]),
                        ft.Row([
                            self.login_manager.username_field,
                            self.login_manager.password_field
                        ], spacing=FIELD_SPACING),
                        ft.Row([
                            ft.Column([
                                self.login_manager.steam_guard_field,
                                ft.Text(
                                    "※ 入力時は自動認証、未入力時はモバイルアプリからの承認が必要です",
                                    size=11,
                                    color=ft.Colors.GREY
                                )
                            ], spacing=TINY_SPACING, expand=True),
                            ft.Column([
                                ft.Row([
                                    self.login_manager.login_button,
                                ], spacing=FIELD_COLUMN_SPACING),
                                ft.Row([
                                    ft.Icon(ft.Icons.WARNING, color=ft.Colors.AMBER, size=16),
                                    ft.Text("コンソールは閉じないで！", 
                                           size=12, color=ft.Colors.AMBER, weight=ft.FontWeight.BOLD)
                                ], spacing=TINY_SPACING)
                            ], spacing=TINY_SPACING, horizontal_alignment=ft.CrossAxisAlignment.END)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ], spacing=FIELD_SPACING),
                    padding=SECTION_PADDING
                )
            ),
            padding=ft.padding.symmetric(horizontal=SECTION_PADDING, vertical=SECTION_VERTICAL_PADDING)
        )
    
    def _build_config_section(self):
        """設定セクションを構築"""
        # コンテンツパスを開くボタン
        open_folder_btn = ft.IconButton(
            icon=ft.Icons.FOLDER_OPEN,
            tooltip="フォルダを開く",
            on_click=lambda e: self._open_content_folder()
        )
        
        return ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("2. アップロード設定", size=18, weight=ft.FontWeight.W_500),
                            ft.Container(expand=True),
                            self.config_manager.new_config_button,
                            self.config_manager.edit_config_button,
                            self.config_manager.delete_config_button
                        ]),
                        ft.Row([
                            self.config_manager.config_dropdown,
                            self.config_manager.config_build_page_btn,
                            self.config_manager.config_depot_page_btn
                        ], spacing=SMALL_SPACING),
                        ft.Divider(),
                        ft.Row([
                            ft.Text("App ID:", size=14),
                            self.config_manager.app_id_field,
                            ft.Text("Depot ID:", size=14),
                            self.config_manager.depot_id_field,
                            ft.Text("ブランチ:", size=14),
                            self.config_manager.branch_field,
                        ], spacing=FIELD_SPACING),
                        ft.Row([
                            ft.Text("説明:", size=14),
                            self.config_manager.upload_description_field,
                        ], spacing=FIELD_SPACING),
                        ft.Row([
                            ft.Text("コンテンツパス:", size=14),
                            self.config_manager.content_path_field,
                            open_folder_btn
                        ], spacing=FIELD_SPACING),
                    ]),
                    padding=SECTION_PADDING
                )
            ),
            padding=ft.padding.symmetric(horizontal=SECTION_PADDING, vertical=SECTION_VERTICAL_PADDING)
        )
    
    def _build_upload_section(self):
        """アップロードセクションを構築"""
        return ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("3. アップロード", size=18, weight=ft.FontWeight.W_500),
                        ft.Row([
                            ft.Container(
                                content=self.upload_manager.login_status_text,
                                expand=True,
                                alignment=ft.alignment.center_left
                            ),
                            ft.Container(
                                content=self.upload_manager.config_status_text,
                                expand=True,
                                alignment=ft.alignment.center_left
                            )
                        ]),
                        ft.Container(height=CONTENT_SPACING),
                        ft.Row([
                            self.upload_manager.upload_button,
                        ], alignment=ft.MainAxisAlignment.CENTER),
                    ]),
                    padding=SECTION_PADDING
                )
            ),
            padding=ft.padding.symmetric(horizontal=SECTION_PADDING, vertical=SECTION_VERTICAL_PADDING)
        )
    
    def _build_download_section(self):
        """ダウンロードセクションを構築"""
        return ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("4. ダウンロード（Depot Download）", size=18, weight=ft.FontWeight.W_500),
                        # 左右に分割
                        ft.Row([
                            # 左側: 入力欄
                            ft.Column([
                                ft.Row([
                                    self.upload_manager.download_app_id_field,
                                    self.upload_manager.download_depot_id_field,
                                ], spacing=FIELD_SPACING),
                                ft.Row([
                                    self.upload_manager.download_manifest_gid_field,
                                    self.upload_manager.open_builds_page_button,
                                ], spacing=FIELD_SPACING),
                            ], spacing=FIELD_SPACING, expand=True),
                            
                            # 右側: 説明文とボタン
                            ft.Column([
                                # 説明文
                                ft.Container(
                                    content=ft.Text(
                                        "⚠️ アクティブなブランチの最新ビルドのみダウンロード可能\n" +
                                        "（非アクティブブランチ・過去のビルドは不可）",
                                        size=12,
                                        color=ft.Colors.ORANGE
                                    ),
                                    bgcolor=ft.Colors.ORANGE_50,
                                    padding=CONTENT_SPACING,
                                    border_radius=5,
                                    width=400,
                                ),
                                ft.Container(height=SMALL_SPACING),
                                # ログイン状態表示
                                self.upload_manager.download_login_status_text,
                                ft.Container(height=TINY_SPACING),
                                # ボタン
                                ft.Row([
                                    self.upload_manager.download_start_button,
                                    self.upload_manager.open_download_folder_button,
                                ], spacing=FIELD_SPACING),
                            ], spacing=FIELD_COLUMN_SPACING),
                        ], spacing=LARGE_SPACING, alignment=ft.MainAxisAlignment.START),
                    ], spacing=SECTION_TITLE_SPACING),
                    padding=SECTION_PADDING
                )
            ),
            padding=ft.padding.symmetric(horizontal=SECTION_PADDING, vertical=SECTION_VERTICAL_PADDING)
        )
    
    def _initialize_state(self):
        """初期状態を設定"""
        # 初期ログメッセージ
        self._log_message("Morn Steam アップロードヘルパーへようこそ")
        self._log_message("ツールを使用するには、まずSteamにログインしてください")
        
        # ContentBuilderパスのチェック
        self.login_manager.check_content_builder_paths()
        
        # 初期コントロール状態
        self._enable_controls(False)
    
    def _enable_controls(self, enabled=True):
        """コントロールの有効/無効を管理"""
        # ログイン状態に関わらず使用可能
        self.config_manager.update_controls_state(enabled)
        
        # アップロードボタンの状態を更新
        has_config = bool(self.config_manager.config_dropdown.value)
        self.upload_manager.update_upload_button_state(
            self.helper.is_logged_in, 
            has_config
        )
        
        self.page.update()
    
    def _open_content_folder(self):
        """コンテンツフォルダを開く"""
        path = self.config_manager.content_path_field.value
        if PlatformCommands.open_folder(path):
            self._log_message(f"フォルダを開きました: {path}")
        else:
            self._log_message("コンテンツパスが設定されていないか、存在しません")
    
    def _start_console_monitor_wrapper(self):
        """コンソール監視を開始（設定に応じて）"""
        self._log_message(f"[デバッグ] コンソール監視の開始を試行... monitor_console設定: {self.helper.settings.get('monitor_console', True)}")
        self._log_message(f"[デバッグ] start_console_monitor関数: {start_console_monitor}")
        self._log_message(f"[デバッグ] helper.steamcmd_terminal: {self.helper.steamcmd_terminal}")
        
        if self.helper.settings.get("monitor_console", True) and start_console_monitor:
            try:
                # コンソールが閉じられた時のコールバックを設定
                self.helper.on_console_closed_callback = self._handle_console_closed
                
                self.console_monitor_wrapper = start_console_monitor(
                    self.helper,
                    self.login_manager.login_status,
                    self.login_manager.login_button,
                    self._enable_controls,
                    self.page
                )
                self._log_message("コンソール監視を開始しました")
                self._log_message(f"[デバッグ] 監視スレッド: {self.console_monitor_wrapper}")
            except Exception as e:
                self._log_message(f"コンソール監視の開始に失敗: {e}")
                import traceback
                self._log_message(f"[デバッグ] トレースバック: {traceback.format_exc()}")
    
    # コールバックハンドラー
    def _handle_login_success(self):
        """ログイン成功時の処理"""
        # コンソール監視は既にコンソールが開いた時点で開始されている
        self._enable_controls(True)
    
    def _handle_login_failure(self):
        """ログイン失敗時の処理"""
        self._enable_controls(False)
    
    def _handle_config_loaded(self, config):
        """設定読み込み時の処理"""
        # アップロードマネージャーに現在の設定を渡す
        if config:
            self.upload_manager.current_config = config
            self.upload_manager.current_config_name = self.config_manager.config_dropdown.value
        else:
            self.upload_manager.current_config = None
            self.upload_manager.current_config_name = None
        self._enable_controls(self.helper.is_logged_in)
    
    def _handle_config_changed(self):
        """設定変更時の処理"""
        self._enable_controls(self.helper.is_logged_in)
    
    def _handle_settings_changed(self):
        """システム設定変更時の処理"""
        # ContentBuilderパスの再チェック
        self.login_manager.check_content_builder_paths()
    
    def _handle_console_closed(self):
        """コンソールが閉じられた時の処理"""
        self._log_message("コンソールが閉じられました")
        
        # ログイン監視を停止
        from .platform_helpers import LoginMonitor
        LoginMonitor.stop_monitoring()
        self._log_message("ログイン監視を停止しました")
        
        # ログイン待機ダイアログを閉じる
        if hasattr(self.login_manager, '_login_waiting_dialog') and self.login_manager._login_waiting_dialog:
            DialogBuilder._close_dialog(self.page, self.login_manager._login_waiting_dialog)
            self.login_manager._login_waiting_dialog = None
        
        # モバイル2FAダイアログも閉じる
        if hasattr(self.login_manager, '_mobile_2fa_dialog') and self.login_manager._mobile_2fa_dialog:
            DialogBuilder._close_dialog(self.page, self.login_manager._mobile_2fa_dialog)
            self.login_manager._mobile_2fa_dialog = None
        
        # ログイン状態をリセット
        self.login_manager.login_status.value = "未ログイン"
        self.login_manager.login_status.color = ft.Colors.RED
        self.login_manager.login_button.disabled = False
        
        # コントロールを無効化
        self._enable_controls(False)
        
        self.page.update()
    
    def _log_message(self, message: str):
        """ログメッセージ出力"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")


def main(page: ft.Page):
    """アプリケーションエントリーポイント"""
    app = SteamUploadApp(page)