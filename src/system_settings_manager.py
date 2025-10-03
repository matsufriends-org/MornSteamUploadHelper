"""System settings management for Steam Upload Helper"""

import flet as ft
import os
import platform
import threading
from pathlib import Path

from .ui_helpers import DialogBuilder
from .platform_helpers import SteamCMDLauncher
from .command_sender import CommandSender
from .folder_picker import pick_folder


class SystemSettingsManager:
    """システム設定を管理するクラス"""
    
    def __init__(self, helper, page: ft.Page):
        self.helper = helper
        self.page = page
        
        # UIコンポーネント
        self.steamcmd_path_text = None
        self.build_output_path_text = None
        
        # コールバック
        self.on_settings_changed = None
    
    def create_ui_components(self):
        """システム設定関連のUIコンポーネントを作成"""
        self.steamcmd_path_text = ft.Text(
            value=self.helper.settings.get("steamcmd_path", "SteamCMDが選択されていません"),
            size=12
        )
        
        self.build_output_path_text = ft.Text(
            value=self.helper.settings.get("build_output_path", "未設定"),
            size=12
        )
    
    def show_system_settings_dialog(self):
        """システム設定ダイアログを表示"""
        # Content Builder Path
        content_builder_path = self.helper.settings.get("content_builder_path", "")
        content_builder_field = ft.TextField(
            label="Content Builder フォルダパス",
            value=content_builder_path,
            read_only=True,
            hint_text="SteamCMD ContentBuilderフォルダを選択"
        )
        
        def select_content_builder(e):
            def run_picker():
                folder_path = pick_folder(title="ContentBuilder フォルダを選択")
                if folder_path:
                    # Validate the selected folder
                    if self._validate_content_builder_path(folder_path):
                        content_builder_field.value = folder_path
                        dlg.update()
                    else:
                        DialogBuilder.show_error_dialog(
                            self.page,
                            "選択されたフォルダは有効なContentBuilderフォルダではありません。\n"
                            "'builder' または 'builder_osx' フォルダを含む必要があります。"
                        )

            # Run in separate thread to avoid blocking UI
            threading.Thread(target=run_picker, daemon=True).start()
        
        select_cb_btn = ft.IconButton(
            ft.Icons.FOLDER_OPEN,
            on_click=select_content_builder,
            tooltip="フォルダを選択"
        )
        
        # Build Output Path  
        build_output_field = ft.TextField(
            label="ビルド出力フォルダ（オプション）",
            value=self.helper.settings.get("build_output_path", ""),
            read_only=True,
            hint_text="ビルドログの保存先"
        )
        
        def select_build_output(e):
            def run_picker():
                folder_path = pick_folder(title="ビルド出力フォルダを選択")
                if folder_path:
                    build_output_field.value = folder_path
                    dlg.update()

            # Run in separate thread to avoid blocking UI
            threading.Thread(target=run_picker, daemon=True).start()
        
        select_output_btn = ft.IconButton(
            ft.Icons.FOLDER_OPEN,
            on_click=select_build_output,
            tooltip="フォルダを選択"
        )
        
        def reset_build_output(e):
            build_output_field.value = ""
            dlg.update()
        
        reset_output_btn = ft.IconButton(
            ft.Icons.CLEAR,
            on_click=reset_build_output,
            tooltip="リセット"
        )
        
        
        
        # helpコマンドテストボタン
        def test_help_command(e):
            steamcmd_path = self.helper.settings.get("steamcmd_path")
            if not steamcmd_path:
                DialogBuilder.show_error_dialog(self.page, "SteamCMDパスが設定されていません")
                return
                
            # テストを実行
            success = CommandSender.test_send_help(
                steamcmd_path,
                self._log_message
            )
            
            if success:
                DialogBuilder.show_success_dialog(
                    self.page,
                    "helpコマンドの送信に成功しました！\n同じ仕組みでアップロードコマンドも送信されます。"
                )
            else:
                DialogBuilder.show_error_dialog(
                    self.page,
                    "helpコマンドの送信に失敗しました。\nSteamCMDウィンドウが正しく開いているか確認してください。"
                )
        
        test_help_btn = ft.ElevatedButton(
            "help 送信テスト",
            icon=ft.Icons.BUG_REPORT,
            on_click=test_help_command,
            tooltip="新しいSteamCMDウィンドウを開いてhelpコマンドを送信します"
        )
        
        def save_settings(e):
            # ContentBuilder pathを保存
            new_cb_path = content_builder_field.value
            if new_cb_path != content_builder_path:
                self.helper.settings["content_builder_path"] = new_cb_path
                
                # SteamCMDパスを自動更新
                steamcmd_path = SteamCMDLauncher.get_steamcmd_path(new_cb_path)
                if steamcmd_path and os.path.exists(steamcmd_path):
                    self.helper.settings["steamcmd_path"] = steamcmd_path
                    self.steamcmd_path_text.value = steamcmd_path
                    self._log_message(f"SteamCMDパスを更新: {steamcmd_path}")
            
            # その他の設定を保存
            self.helper.settings["build_output_path"] = build_output_field.value
            
            self.helper.save_settings()
            
            # UIを更新
            self.build_output_path_text.value = build_output_field.value or "未設定"
            self.page.update()
            
            DialogBuilder._close_dialog(self.page, dlg)
            DialogBuilder.show_success_dialog(self.page, "設定を保存しました")
            
            if self.on_settings_changed:
                self.on_settings_changed()
        
        # ダイアログ内容
        content = ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Text("SteamCMD設定", size=16, weight=ft.FontWeight.BOLD),
                    ft.Row([content_builder_field, select_cb_btn]),
                    ft.Text(
                        "※ ContentBuilderフォルダはbuilder/builder_osx/builder_linuxを含むフォルダです",
                        size=11,
                        color=ft.Colors.GREY
                    ),
                    ft.Container(height=10),
                    test_help_btn,
                ]),
                padding=ft.padding.only(bottom=20)
            ),
            
            ft.Container(
                content=ft.Column([
                    ft.Text("ビルド出力設定", size=16, weight=ft.FontWeight.BOLD),
                    ft.Row([build_output_field, select_output_btn, reset_output_btn]),
                    ft.Text(
                        "※ 設定すると、ビルドログがこのフォルダに保存されます",
                        size=11,
                        color=ft.Colors.GREY
                    ),
                ]),
                padding=ft.padding.only(bottom=20)
            ),
            
        ], width=500, scroll=ft.ScrollMode.AUTO)
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("基本設定"),
            content=content,
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: DialogBuilder._close_dialog(self.page, dlg)),
                ft.TextButton("保存", on_click=save_settings),
            ]
        )
        
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
    
    def _validate_content_builder_path(self, path: str) -> bool:
        """ContentBuilderパスの妥当性を検証"""
        if not os.path.exists(path):
            return False
        
        # プラットフォーム別のbuilderフォルダをチェック
        valid_folders = ["builder", "builder_osx", "builder_linux"]
        
        for folder in valid_folders:
            if os.path.exists(os.path.join(path, folder)):
                return True
        
        return False
    
    def select_build_output_folder(self):
        """ビルド出力フォルダを選択"""
        def run_picker():
            folder_path = pick_folder(title="ビルド出力フォルダを選択")
            if folder_path:
                self.helper.settings["build_output_path"] = folder_path
                self.helper.save_settings()
                self.build_output_path_text.value = folder_path
                self.page.update()
                self._log_message(f"ビルド出力フォルダを設定: {folder_path}")

        # Run in separate thread to avoid blocking UI
        threading.Thread(target=run_picker, daemon=True).start()
    
    def reset_build_output_folder(self):
        """ビルド出力フォルダをリセット"""
        self.helper.settings["build_output_path"] = ""
        self.helper.save_settings()
        self.build_output_path_text.value = "未設定"
        self.page.update()
        self._log_message("ビルド出力フォルダをリセットしました")
    
    def _log_message(self, message: str):
        """ログメッセージ出力"""
        import time
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")