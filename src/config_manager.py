"""Configuration management for Steam Upload Helper"""

import flet as ft
import time
from ui_helpers import DialogBuilder, ConfigDialogBuilder, SteamPageOpener


class ConfigManager:
    """アップロード設定を管理するクラス"""
    
    def __init__(self, helper, page: ft.Page):
        self.helper = helper
        self.page = page
        
        # UIコンポーネント
        self.config_dropdown = None
        self.new_config_button = None
        self.edit_config_button = None
        self.delete_config_button = None
        self.config_build_page_btn = None
        self.config_depot_page_btn = None
        
        # 設定表示フィールド
        self.app_id_field = None
        self.depot_id_field = None
        self.branch_field = None
        self.upload_description_field = None
        self.content_path_field = None
        
        # コールバック
        self.on_config_loaded = None
        self.on_config_changed = None
    
    def create_ui_components(self):
        """設定関連のUIコンポーネントを作成"""
        self.config_dropdown = ft.Dropdown(
            label="アップロード設定",
            hint_text="設定を選択...",
            width=300,
            options=[ft.dropdown.Option(name) for name in self.helper.upload_configs.keys()],
            on_change=lambda e: self.load_upload_config()
        )
        
        self.new_config_button = ft.ElevatedButton(
            "新規設定",
            on_click=lambda e: self.show_new_config_dialog(),
            icon=ft.Icons.ADD,
            disabled=True
        )
        
        self.edit_config_button = ft.ElevatedButton(
            "設定を編集",
            on_click=lambda e: self.show_edit_config_dialog(),
            icon=ft.Icons.EDIT,
            disabled=True
        )
        
        self.delete_config_button = ft.ElevatedButton(
            "削除",
            on_click=lambda e: self.delete_current_config(),
            icon=ft.Icons.DELETE,
            disabled=True
        )
        
        # Steam ページボタン
        self.config_build_page_btn = ft.ElevatedButton(
            "ビルドページ",
            icon=ft.Icons.OPEN_IN_NEW,
            disabled=True,
            on_click=lambda e: self._open_steam_page_for_config("builds")
        )
        
        self.config_depot_page_btn = ft.ElevatedButton(
            "デポページ",
            icon=ft.Icons.OPEN_IN_NEW,
            disabled=True,
            on_click=lambda e: self._open_steam_page_for_config("depots")
        )
        
        # 設定表示フィールド
        self.app_id_field = ft.Text(value="", size=14)
        self.depot_id_field = ft.Text(value="", size=14)
        self.branch_field = ft.Text(value="", size=14)
        self.upload_description_field = ft.Text(value="", size=14, expand=True)
        self.content_path_field = ft.Text(value="", size=14, expand=True)
    
    def load_upload_config(self):
        """選択された設定を読み込む"""
        if not self.config_dropdown.value:
            return
        
        config = self.helper.upload_configs.get(self.config_dropdown.value, {})
        self.app_id_field.value = config.get("app_id", "")
        self.depot_id_field.value = config.get("depot_id", "")
        self.branch_field.value = config.get("branch", "")
        self.upload_description_field.value = config.get("description", "")
        
        # コンテンツパスを更新
        if "content_path" in config and config["content_path"]:
            self.content_path_field.value = config["content_path"]
        else:
            self.content_path_field.value = ""
        
        # ボタン状態を更新
        self._update_button_states()
        
        self.page.update()
        self._log_message(f"設定を読み込みました: {self.config_dropdown.value}")
        
        if self.on_config_loaded:
            self.on_config_loaded(config)
    
    def delete_current_config(self):
        """現在選択されている設定を削除"""
        if not self.config_dropdown.value:
            DialogBuilder.show_error_dialog(self.page, "削除する設定を選択してください")
            return
        
        name = self.config_dropdown.value
        self.helper.delete_upload_config(name)
        
        # ドロップダウンを更新
        self.config_dropdown.options = [ft.dropdown.Option(name) for name in self.helper.upload_configs.keys()]
        self.config_dropdown.value = None
        
        # フィールドをクリア
        self.app_id_field.value = ""
        self.depot_id_field.value = ""
        self.branch_field.value = ""
        self.upload_description_field.value = ""
        self.content_path_field.value = ""
        
        # ボタン状態を更新
        self._update_button_states()
        
        self.page.update()
        self._log_message(f"設定を削除しました: {name}")
        
        if self.on_config_changed:
            self.on_config_changed()
    
    def show_new_config_dialog(self):
        """新規設定作成ダイアログを表示"""
        fields = ConfigDialogBuilder.build_config_fields()
        
        # Steamページボタンの設定
        def update_steam_buttons(build_btn, depot_btn, enabled):
            build_btn.disabled = not enabled
            depot_btn.disabled = not enabled
            dlg.update()
        
        steam_buttons = DialogBuilder.create_steam_page_buttons(
            fields['app_id'], 
            update_steam_buttons
        )
        
        # フォルダ選択ボタン
        folder_picker_btn = DialogBuilder.create_folder_picker(fields['content_path'], None)
        
        # ダイアログコンテンツ
        content = ConfigDialogBuilder.build_config_dialog_content(
            fields, folder_picker_btn, steam_buttons
        )
        
        def create_config(e):
            # 必須フィールドチェック
            if not fields['name'].value:
                DialogBuilder.show_error_dialog(self.page, "設定名は必須です！")
                return
                
            if not fields['app_id'].value or not fields['depot_id'].value:
                DialogBuilder.show_error_dialog(self.page, "App IDとDepot IDは必須です！")
                return
            
            # 設定を作成
            config = {
                "app_id": fields['app_id'].value,
                "depot_id": fields['depot_id'].value,
                "branch": fields['branch'].value,
                "description": fields['description'].value,
                "content_path": fields['content_path'].value
            }
            
            self.helper.save_upload_config(fields['name'].value, config)
            
            # ドロップダウンを更新
            self.config_dropdown.options = [ft.dropdown.Option(name) for name in self.helper.upload_configs.keys()]
            self.config_dropdown.value = fields['name'].value
            
            # 新しい設定を読み込む
            self.load_upload_config()
            
            DialogBuilder._close_dialog(self.page, dlg)
            self._log_message(f"新規設定を作成しました: {fields['name'].value}")
            
            if self.on_config_changed:
                self.on_config_changed()
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("新規設定"),
            content=content,
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: DialogBuilder._close_dialog(self.page, dlg)),
                ft.TextButton("作成", on_click=create_config)
            ]
        )
        
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
    
    def show_edit_config_dialog(self):
        """設定編集ダイアログを表示"""
        if not self.config_dropdown.value:
            return
        
        current_config = self.helper.upload_configs.get(self.config_dropdown.value, {})
        current_config['name'] = self.config_dropdown.value
        
        fields = ConfigDialogBuilder.build_config_fields(current_config, readonly_name=True)
        
        # Steamページボタンの設定
        def update_steam_buttons(build_btn, depot_btn, enabled):
            build_btn.disabled = not enabled
            depot_btn.disabled = not enabled
            dlg.update()
        
        steam_buttons = DialogBuilder.create_steam_page_buttons(
            fields['app_id'], 
            update_steam_buttons
        )
        
        # 初期状態を設定
        if current_config.get("app_id"):
            steam_buttons[0].disabled = False
            steam_buttons[1].disabled = False
        
        # フォルダ選択ボタン
        folder_picker_btn = DialogBuilder.create_folder_picker(fields['content_path'], None)
        
        # ダイアログコンテンツ
        content = ConfigDialogBuilder.build_config_dialog_content(
            fields, folder_picker_btn, steam_buttons
        )
        
        def save_config(e):
            # 必須フィールドチェック
            if not fields['app_id'].value or not fields['depot_id'].value:
                DialogBuilder.show_error_dialog(self.page, "App IDとDepot IDは必須です！")
                return
            
            # 設定を更新
            config = {
                "app_id": fields['app_id'].value,
                "depot_id": fields['depot_id'].value,
                "branch": fields['branch'].value,
                "description": fields['description'].value,
                "content_path": fields['content_path'].value
            }
            
            self.helper.save_upload_config(self.config_dropdown.value, config)
            
            # 設定を再読み込み
            self.load_upload_config()
            
            DialogBuilder._close_dialog(self.page, dlg)
            self._log_message(f"設定を更新しました: {self.config_dropdown.value}")
            
            if self.on_config_changed:
                self.on_config_changed()
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("設定を編集"),
            content=content,
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: DialogBuilder._close_dialog(self.page, dlg)),
                ft.TextButton("保存", on_click=save_config)
            ]
        )
        
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
    
    def _open_steam_page_for_config(self, page_type):
        """選択中の設定のSteamページを開く"""
        if self.config_dropdown.value and self.app_id_field.value:
            SteamPageOpener.open_page(page_type, self.app_id_field.value)
    
    def _update_button_states(self):
        """ボタンの有効/無効状態を更新"""
        has_config = bool(self.config_dropdown.value)
        has_app_id = bool(self.app_id_field.value)
        
        self.delete_config_button.disabled = not has_config
        self.edit_config_button.disabled = not has_config
        self.config_build_page_btn.disabled = not (has_config and has_app_id)
        self.config_depot_page_btn.disabled = not (has_config and has_app_id)
    
    def _log_message(self, message: str):
        """ログメッセージ出力"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def update_controls_state(self, logged_in: bool):
        """ログイン状態に応じてコントロールを更新"""
        # 設定コントロールは常に使用可能
        self.config_dropdown.disabled = False
        self.new_config_button.disabled = False
        
        # その他のボタン状態を更新
        self._update_button_states()