"""Upload management functionality for Steam Upload Helper"""

import flet as ft
import os
import time
import webbrowser
import platform
import subprocess
import threading
from pathlib import Path

from .ui_helpers import DialogBuilder, PlatformCommands
from .command_sender import CommandSender
from .platform_helpers import ConsoleMonitor


class UploadManager:
    """アップロード処理を管理するクラス"""
    
    def __init__(self, helper, page: ft.Page):
        self.helper = helper
        self.page = page
        self.upload_in_progress = False
        self.download_in_progress = False
        
        # UIコンポーネント
        self.upload_button = None
        self.login_status_text = None
        self.config_status_text = None
        self.progress_bar = None
        
        # ダウンロード用UIコンポーネント
        self.download_app_id_field = None
        self.download_depot_id_field = None
        self.download_manifest_gid_field = None
        self.open_builds_page_button = None
        self.download_start_button = None
        self.open_download_folder_button = None
        self.download_login_status_text = None
        
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
        
        # ダウンロード用のUIコンポーネント
        self.download_app_id_field = ft.TextField(
            label="App ID *",
            width=200,
            on_change=lambda e: self._on_download_field_change()
        )
        
        self.download_depot_id_field = ft.TextField(
            label="Depot ID *",
            width=200,
            on_change=lambda e: self._on_download_field_change()
        )
        
        self.download_manifest_gid_field = ft.TextField(
            label="Manifest GID *",
            width=250,
            on_change=lambda e: self._on_download_field_change()
        )
        
        self.open_builds_page_button = ft.ElevatedButton(
            "ビルドページを開く",
            icon=ft.Icons.OPEN_IN_NEW,
            on_click=lambda e: self._open_builds_page(),
            disabled=True,
            style=ft.ButtonStyle(
                color={
                    ft.ControlState.DEFAULT: ft.Colors.WHITE,
                    ft.ControlState.DISABLED: ft.Colors.GREY_400,
                },
                bgcolor={
                    ft.ControlState.DEFAULT: ft.Colors.PURPLE,
                    ft.ControlState.DISABLED: ft.Colors.GREY_300,
                },
            ),
        )
        
        self.download_start_button = ft.ElevatedButton(
            "ダウンロード開始",
            icon=ft.Icons.DOWNLOAD,
            on_click=lambda e: self.run_download_with_manifest(),
            style=ft.ButtonStyle(
                color={
                    ft.ControlState.DEFAULT: ft.Colors.WHITE,
                    ft.ControlState.DISABLED: ft.Colors.GREY_400,
                },
                bgcolor={
                    ft.ControlState.DEFAULT: ft.Colors.GREEN,
                    ft.ControlState.DISABLED: ft.Colors.GREY_300,
                },
            ),
            disabled=True
        )
        
        self.open_download_folder_button = ft.ElevatedButton(
            "フォルダを開く",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=lambda e: self.open_download_folder_from_input(),
            style=ft.ButtonStyle(
                color={
                    ft.ControlState.DEFAULT: ft.Colors.WHITE,
                    ft.ControlState.DISABLED: ft.Colors.GREY_400,
                },
                bgcolor={
                    ft.ControlState.DEFAULT: ft.Colors.ORANGE,
                    ft.ControlState.DISABLED: ft.Colors.GREY_300,
                },
            ),
            disabled=True
        )
        
        self.download_login_status_text = ft.Text(
            "❌ コンソールを開いてログインしている",
            size=14
        )
    
    def update_upload_button_state(self, is_logged_in: bool, has_config: bool):
        """アップロードボタンの状態を更新"""
        # ステータスアイコンを更新
        self.login_status_text.value = f"{'✅' if is_logged_in else '❌'} コンソールを開いてログインしている"
        self.config_status_text.value = f"{'✅' if has_config else '❌'} アップロード設定を選択している"
        # ダウンロード用のステータスも更新
        self.download_login_status_text.value = f"{'✅' if is_logged_in else '❌'} コンソールを開いてログインしている"
        
        # 両方の条件が満たされた時のみアップロードボタンを有効化
        self.upload_button.disabled = not (is_logged_in and has_config)
        
        # ダウンロードボタンの状態を更新
        self._update_download_button_states(is_logged_in)
        
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
        
        # アップロード進行中ダイアログを表示
        self._show_upload_progress_dialog()
        
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
            self._log_message("アップロードが完了するまでお待ちください...")
            # アップロード完了を監視
            self._monitor_upload_completion()
        else:
            self._log_message("自動送信に失敗しました。")
            # 進行中ダイアログを閉じる
            self._close_upload_progress_dialog()
            # 失敗時は手動でダイアログを表示（フォールバック）
            self._show_manual_command_dialog(upload_command)
    
    def _execute_upload_unix(self, upload_command: str):
        """Unix系環境でのアップロード実行"""
        # この分岐もプラットフォーム固有の処理が異なるため必要
        if platform.system() == "Darwin":
            self._execute_upload_macos(upload_command)
        else:
            # Linuxでは手動実行を促す
            # 進行中ダイアログを閉じる
            self._close_upload_progress_dialog()
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
            self._log_message("アップロードが完了するまでお待ちください...")
            # アップロード完了を監視
            self._monitor_upload_completion()
        else:
            self._log_message("自動送信に失敗しました。")
            # 進行中ダイアログを閉じる
            self._close_upload_progress_dialog()
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
    
    def _show_upload_progress_dialog(self):
        """アップロード進行中ダイアログを表示"""
        self._upload_progress_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("アップロード中"),
            content=ft.Column([
                ft.ProgressRing(width=40, height=40, stroke_width=3),
                ft.Text("Steamへアップロード中です...", size=14),
                ft.Container(height=10),
                ft.Text("アップロードが完了するまでお待ちください", 
                       size=12, color=ft.Colors.GREY),
                ft.Text("進行状況はSteamCMDコンソールで確認できます", 
                       size=12, color=ft.Colors.GREY),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            actions=[]  # ボタンなし（キャンセル不可）
        )
        
        self.page.overlay.append(self._upload_progress_dialog)
        self._upload_progress_dialog.open = True
        self.page.update()
    
    def _close_upload_progress_dialog(self):
        """アップロード進行中ダイアログを閉じる"""
        if hasattr(self, '_upload_progress_dialog') and self._upload_progress_dialog:
            DialogBuilder._close_dialog(self.page, self._upload_progress_dialog)
            self._upload_progress_dialog = None
    
    def _monitor_upload_completion(self):
        """アップロードの完了を監視"""
        def monitor_thread():
            # 最初に少し待機してアップロード開始を確認
            time.sleep(2)

            # Steam>プロンプトが戻ってくるまで監視
            max_wait = 600  # 最大10分待機
            check_interval = 1.0  # 1秒間隔でチェック
            elapsed = 0

            while elapsed < max_wait:
                # まず完了メッセージをチェック（より確実）
                if self._check_upload_complete():
                    self._log_message("アップロード完了メッセージを検出しました！")
                    # 少し待ってSteam>プロンプトが戻るのを待つ
                    time.sleep(1)

                    # ダイアログを閉じる
                    self._close_upload_progress_dialog()
                    # 成功メッセージを表示
                    DialogBuilder.show_success_dialog(
                        self.page,
                        "アップロードが正常に完了しました！\nSteamパートナーサイトで確認してください。"
                    )
                    break

                time.sleep(check_interval)
                elapsed += check_interval

                # 10秒ごとに進捗をログ
                if int(elapsed) % 10 == 0 and elapsed > 0:
                    self._log_message(f"アップロード処理中... ({elapsed}秒経過)")

            if elapsed >= max_wait:
                self._log_message("アップロード監視がタイムアウトしました")
                self._close_upload_progress_dialog()
                DialogBuilder.show_info_dialog(
                    self.page,
                    "アップロード処理が長時間かかっています。\nSteamCMDコンソールで状況を確認してください。"
                )

        # 監視スレッドを開始
        thread = threading.Thread(target=monitor_thread, daemon=True)
        thread.start()
    
    def _check_steam_prompt_returned(self) -> bool:
        """Steam>プロンプトが戻ってきたかチェック"""
        # platform_helpersの汎用実装を使用
        steamcmd_path = self.helper.settings.get("steamcmd_path")
        return ConsoleMonitor.check_steam_prompt(steamcmd_path=steamcmd_path, log_callback=self._log_message)

    def _check_upload_complete(self) -> bool:
        """アップロード完了をチェック"""
        # platform_helpersの汎用実装を使用
        from .platform_helpers import ConsoleMonitor
        # 完了メッセージのパターンをチェック
        steamcmd_path = self.helper.settings.get("steamcmd_path")
        return ConsoleMonitor.check_for_pattern("Successfully finished AppID", steamcmd_path=steamcmd_path)

    
    def _execute_download_windows(self, download_command: str, app_id: str):
        """Windows環境でのダウンロード実行"""
        self._log_message("自動コマンド送信を試行中...")
        
        # 共通のCommandSenderを使用
        success = CommandSender.send_command(
            download_command, 
            "Steam>",
            process_id=getattr(self.helper, 'steamcmd_cmd_process_id', None),
            log_callback=self._log_message
        )
        
        if success:
            self._log_message("✓ ダウンロードコマンドを自動実行しました")
            self._log_message("ダウンロードが完了するまでお待ちください...")
            # ダウンロード完了を監視
            self._monitor_download_completion(app_id)
        else:
            self._log_message("自動送信に失敗しました。")
            # 進行中ダイアログを閉じる
            self._close_download_progress_dialog()
            # 失敗時は手動でダイアログを表示（フォールバック）
            self._show_manual_download_dialog(download_command)
    
    def _execute_download_unix(self, download_command: str, app_id: str):
        """Unix系環境でのダウンロード実行"""
        if platform.system() == "Darwin":
            self._execute_download_macos(download_command, app_id)
        else:
            # Linuxでは手動実行を促す
            self._close_download_progress_dialog()
            self._show_manual_download_dialog(download_command)
    
    def _execute_download_macos(self, download_command: str, app_id: str):
        """macOS環境でのダウンロード実行"""
        self._log_message("自動コマンド送信を試行中...")
        
        # 共通のCommandSenderを使用
        success = CommandSender.send_command(
            download_command,
            "Steam>",
            log_callback=self._log_message
        )
        
        if success:
            self._log_message("✓ ダウンロードコマンドを自動実行しました")
            self._log_message("ダウンロードが完了するまでお待ちください...")
            # ダウンロード完了を監視
            self._monitor_download_completion(app_id)
        else:
            self._log_message("自動送信に失敗しました。")
            # 進行中ダイアログを閉じる
            self._close_download_progress_dialog()
            # 失敗時は手動でダイアログを表示（フォールバック）
            self._show_manual_download_dialog(download_command)
    
    def _show_download_progress_dialog(self):
        """ダウンロード進行中ダイアログを表示"""
        self._download_progress_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("ダウンロード中"),
            content=ft.Column([
                ft.ProgressRing(width=40, height=40, stroke_width=3),
                ft.Text("Steamからダウンロード中です...", size=14),
                ft.Container(height=10),
                ft.Text("ダウンロードが完了するまでお待ちください", 
                       size=12, color=ft.Colors.GREY),
                ft.Text("進行状況はSteamCMDコンソールで確認できます", 
                       size=12, color=ft.Colors.GREY),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            actions=[]  # ボタンなし（キャンセル不可）
        )
        
        self.page.overlay.append(self._download_progress_dialog)
        self._download_progress_dialog.open = True
        self.page.update()
    
    def _close_download_progress_dialog(self):
        """ダウンロード進行中ダイアログを閉じる"""
        if hasattr(self, '_download_progress_dialog') and self._download_progress_dialog:
            DialogBuilder._close_dialog(self.page, self._download_progress_dialog)
            self._download_progress_dialog = None
    
    def _show_manual_download_dialog(self, download_command: str):
        """手動でダウンロードコマンドを実行するためのダイアログを表示"""
        # クリップボードにコピー
        self.page.set_clipboard(download_command)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("ダウンロードコマンド"),
            content=ft.Column([
                ft.Text("以下のコマンドをSteamCMDコンソールで実行してください："),
                ft.Container(
                    content=ft.Text(download_command, selectable=True),
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
        
        self._log_message(f"Please run in SteamCMD console: {download_command}")
    
    def _monitor_download_completion(self, app_id: str):
        """ダウンロードの完了を監視"""
        def monitor_thread():
            # 最初に少し待機してダウンロード開始を確認
            time.sleep(2)

            # Steam>プロンプトが戻ってくるまで監視
            max_wait = 600  # 最大10分待機
            check_interval = 1.0  # 1秒間隔でチェック
            elapsed = 0

            # エラーメッセージをチェックするためのフラグ
            error_detected = False

            while elapsed < max_wait:
                # まず完了メッセージをチェック（より確実）
                if self._check_download_complete():
                    self._log_message("ダウンロード完了メッセージを検出しました！")
                    # 少し待ってSteam>プロンプトが戻るのを待つ
                    time.sleep(1)

                    # ダウンロード先を確認
                    download_path = self._get_download_path(app_id)
                    # ダイアログを閉じる
                    self._close_download_progress_dialog()
                    # 成功メッセージを表示
                    DialogBuilder.show_success_dialog(
                        self.page,
                        f"ダウンロードが正常に完了しました！\nダウンロード先: {download_path}"
                    )
                    break

                # エラーチェック
                if self._check_download_error():
                    self._log_message("ダウンロードエラーを検出しました")
                    self._close_download_progress_dialog()
                    DialogBuilder.show_error_dialog(
                        self.page,
                        "ダウンロードに失敗しました。\n\n考えられる原因：\n" +
                        "• App IDまたはDepot IDが正しくない\n" +
                        "• このゲームを所有していない\n" +
                        "• このデポはダウンロード不可\n" +
                        "• 認証が必要（anonymousログインでは不可）\n\n" +
                        "ゲームを所有しており、正しいIDを使用している場合は、\n" +
                        "別のデポIDを試すか、DepotDownloaderなどの\n" +
                        "サードパーティツールの使用を検討してください。"
                    )
                    error_detected = True
                    break

                time.sleep(check_interval)
                elapsed += check_interval

                # 10秒ごとに進捗をログ
                if int(elapsed) % 10 == 0 and elapsed > 0:
                    self._log_message(f"ダウンロード処理中... ({elapsed}秒経過)")

            if elapsed >= max_wait:
                self._log_message("ダウンロード監視がタイムアウトしました")
                self._close_download_progress_dialog()
                DialogBuilder.show_info_dialog(
                    self.page,
                    "ダウンロード処理が長時間かかっています。\nSteamCMDコンソールで状況を確認してください。"
                )

        # 監視スレッドを開始
        thread = threading.Thread(target=monitor_thread, daemon=True)
        thread.start()
    
    def _get_download_path(self, app_id: str) -> str:
        """ダウンロードパスを取得"""
        # SteamCMDのデフォルトダウンロードパスを構築
        # settingsからsteamcmd_pathを取得
        steamcmd_path = self.helper.settings.get("steamcmd_path")
        if not steamcmd_path:
            # steamcmd_pathが保存されていない場合はcontent_builder_pathから取得
            content_builder_path = self.helper.settings.get("content_builder_path")
            if content_builder_path:
                from .platform_helpers import SteamCMDLauncher
                steamcmd_path = SteamCMDLauncher.get_steamcmd_path(content_builder_path)
        
        if steamcmd_path:
            steamcmd_dir = os.path.dirname(steamcmd_path)
            download_path = os.path.join(steamcmd_dir, "steamapps", "content", f"app_{app_id}")
            return download_path
        else:
            # フォールバックとして現在のディレクトリを使用
            return os.path.join(os.getcwd(), "steamapps", "content", f"app_{app_id}")
    
    
    def _check_download_error(self) -> bool:
        """ダウンロードエラーをチェック"""
        # platform_helpersの汎用実装を使用
        from .platform_helpers import ConsoleMonitor
        # エラーメッセージのパターンをチェック
        return ConsoleMonitor.check_for_error_pattern([
            "Depot download failed",
            "Invalid default manifest",
            "missing app info",
            "Missing configuration"
        ])

    def _check_download_complete(self) -> bool:
        """ダウンロード完了をチェック"""
        # platform_helpersの汎用実装を使用
        from .platform_helpers import ConsoleMonitor
        # 完了メッセージのパターンをチェック
        steamcmd_path = self.helper.settings.get("steamcmd_path")
        return ConsoleMonitor.check_for_pattern("Depot download complete", steamcmd_path=steamcmd_path)

    def _on_download_field_change(self):
        """ダウンロードフィールドの入力変更時の処理"""
        # App IDが入力されたらビルドページボタンを有効化
        app_id = self.download_app_id_field.value
        self.open_builds_page_button.disabled = not app_id.strip()
        
        # ログイン状態を取得（helper.is_logged_in を使用）
        is_logged_in = self.helper.is_logged_in if self.helper else False
        self._update_download_button_states(is_logged_in)
        
        self.page.update()
    
    def _update_download_button_states(self, is_logged_in: bool):
        """ダウンロード関連ボタンの状態を更新"""
        # 入力値を取得
        app_id = self.download_app_id_field.value.strip() if self.download_app_id_field.value else ""
        depot_id = self.download_depot_id_field.value.strip() if self.download_depot_id_field.value else ""
        manifest_gid = self.download_manifest_gid_field.value.strip() if self.download_manifest_gid_field.value else ""
        
        # ダウンロード開始ボタン: ログイン済み + 3つ全て入力
        self.download_start_button.disabled = not (is_logged_in and app_id and depot_id and manifest_gid)
        
        # フォルダを開くボタン: AppIDとDepotIDが入力されていれば
        self.open_download_folder_button.disabled = not (app_id and depot_id)
    
    def _open_builds_page(self):
        """ビルドページを開く"""
        app_id = self.download_app_id_field.value
        if app_id:
            url = f"https://partner.steamgames.com/apps/builds/{app_id}"
            webbrowser.open(url)
            self._log_message(f"ビルドページを開きました: {url}")
    
    def run_download_with_manifest(self):
        """ManifestGID指定でダウンロード処理を実行"""
        if self.download_in_progress:
            self._log_message("ダウンロード処理中...")
            return
        
        if not self.helper.is_logged_in:
            DialogBuilder.show_error_dialog(self.page, "Steamにログインしてください！")
            return
        
        # 入力値を取得
        app_id = self.download_app_id_field.value.strip()
        depot_id = self.download_depot_id_field.value.strip()
        manifest_gid = self.download_manifest_gid_field.value.strip()
        
        # バリデーション
        if not app_id or not depot_id or not manifest_gid:
            DialogBuilder.show_error_dialog(
                self.page, 
                "App ID、Depot ID、Manifest GIDをすべて入力してください。"
            )
            return
        
        self.download_in_progress = True
        self.download_start_button.disabled = True
        self.progress_bar.visible = True
        self.page.update()
        
        try:
            self._log_message(f"ダウンロード開始:")
            self._log_message(f"App ID: {app_id}")
            self._log_message(f"Depot ID: {depot_id}")
            self._log_message(f"Manifest GID: {manifest_gid}")
            
            # download_depotコマンドを構築（ManifestGID付き）
            download_command = f"download_depot {app_id} {depot_id} {manifest_gid}"
            
            self._log_message(f"実行コマンド: {download_command}")
            
            # ダウンロード進行中ダイアログを表示
            self._show_download_progress_dialog()
            
            # プラットフォーム別の実行
            if platform.system() == "Windows":
                self._execute_download_windows(download_command, app_id)
            else:
                self._execute_download_unix(download_command, app_id)
            
        except Exception as ex:
            self._log_message(f"ダウンロード中にエラー: {str(ex)}")
            DialogBuilder.show_error_dialog(self.page, f"ダウンロードエラー: {str(ex)}")
        finally:
            self.download_start_button.disabled = False
            self.download_in_progress = False
            self.progress_bar.visible = False
            self.page.update()
    
    def open_download_folder_from_input(self):
        """入力されたApp IDからダウンロードフォルダを開く"""
        app_id = self.download_app_id_field.value.strip()
        depot_id = self.download_depot_id_field.value.strip()
        
        if not app_id:
            DialogBuilder.show_error_dialog(self.page, "App IDを入力してください。")
            return
        
        # パスを構築（depot_idも含む場合）
        download_path = self._get_download_path(app_id)
        if depot_id and os.path.exists(download_path):
            # depot_idフォルダがあるかチェック
            depot_path = os.path.join(download_path, f"depot_{depot_id}")
            if os.path.exists(depot_path):
                download_path = depot_path
        
        if os.path.exists(download_path):
            if platform.system() == "Windows":
                os.startfile(download_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", download_path])
            else:  # Linux
                subprocess.call(["xdg-open", download_path])
            self._log_message(f"ダウンロードフォルダを開きました: {download_path}")
        else:
            DialogBuilder.show_error_dialog(
                self.page,
                f"ダウンロードフォルダが見つかりません: {download_path}\n\n" +
                "まだダウンロードが完了していないか、\n" +
                "異なるApp ID/Depot IDの可能性があります。"
            )
    
    def _log_message(self, message: str):
        """ログメッセージ出力"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")