"""UI Helper functions for Morn Steam Upload Helper"""

import flet as ft
from pathlib import Path
import webbrowser


class DialogBuilder:
    """共通ダイアログ作成クラス"""
    
    @staticmethod
    def create_text_field(label: str, **kwargs):
        """共通テキストフィールドを作成"""
        return ft.TextField(label=label, **kwargs)
    
    @staticmethod
    def create_steam_page_buttons(app_id_field, enabled_callback=None):
        """Steamページボタンのペアを作成"""
        build_btn = ft.ElevatedButton(
            "ビルドページを開く",
            disabled=True,
            on_click=lambda e: SteamPageOpener.open_page("builds", app_id_field.value) if app_id_field.value else None
        )
        
        depot_btn = ft.ElevatedButton(
            "デポページを開く", 
            disabled=True,
            on_click=lambda e: SteamPageOpener.open_page("depots", app_id_field.value) if app_id_field.value else None
        )
        
        if enabled_callback:
            app_id_field.on_change = lambda e: enabled_callback(build_btn, depot_btn, bool(e.control.value and e.control.value.strip()))
        
        return build_btn, depot_btn
    
    @staticmethod
    def create_folder_picker(target_field, dlg=None):
        """フォルダ選択ボタンとピッカーを作成"""
        def select_folder(e):
            def on_folder_selected(e: ft.FilePickerResultEvent):
                if e.path:
                    target_field.value = e.path
                    if dlg:
                        dlg.update()
                    else:
                        e.page.update()
            
            folder_picker = ft.FilePicker(on_result=on_folder_selected)
            e.page.overlay.append(folder_picker)
            e.page.update()
            folder_picker.get_directory_path(dialog_title="コンテンツフォルダを選択")
        
        return ft.IconButton(
            ft.Icons.FOLDER_OPEN,
            on_click=select_folder,
            tooltip="フォルダを選択"
        )
    
    @staticmethod
    def show_error_dialog(page: ft.Page, message: str):
        """エラーダイアログを表示"""
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("エラー"),
            content=ft.Text(message),
            actions=[
                ft.TextButton("OK", on_click=lambda e: DialogBuilder._close_dialog(page, dlg))
            ]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()
    
    @staticmethod
    def show_success_dialog(page: ft.Page, message: str):
        """成功ダイアログを表示"""
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("成功"),
            content=ft.Text(message),
            actions=[
                ft.TextButton("OK", on_click=lambda e: DialogBuilder._close_dialog(page, dlg))
            ]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()
    
    @staticmethod
    def _close_dialog(page: ft.Page, dlg: ft.AlertDialog):
        """ダイアログを閉じる共通処理"""
        dlg.open = False
        page.update()


class SteamPageOpener:
    """Steamページを開くための共通処理"""
    
    @staticmethod
    def open_page(page_type: str, app_id: str):
        """Steamページを開く"""
        if app_id:
            url = f"https://partner.steamgames.com/apps/{page_type}/{app_id}"
            webbrowser.open(url)
            print(f"Steam {page_type} ページを開きました: {url}")


class ButtonStateManager:
    """ボタンの有効/無効状態を管理"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.buttons = {}
    
    def register_button(self, name: str, button: ft.ElevatedButton, 
                       enabled_condition=None):
        """ボタンを登録"""
        self.buttons[name] = {
            'button': button,
            'condition': enabled_condition
        }
    
    def update_states(self, **context):
        """すべてのボタンの状態を更新"""
        for name, info in self.buttons.items():
            button = info['button']
            condition = info['condition']
            
            if condition:
                button.disabled = not condition(**context)
            
        self.page.update()


class ConfigDialogBuilder:
    """設定ダイアログの共通ビルダー"""
    
    @staticmethod
    def build_config_fields(config=None, readonly_name=False):
        """設定フィールドのセットを作成"""
        fields = {
            'name': ft.TextField(
                label="設定名" + (" *" if not readonly_name else ""),
                value=config.get('name', '') if config else '',
                read_only=readonly_name,
                autofocus=True
            ),
            'app_id': ft.TextField(
                label="App ID *",
                value=config.get('app_id', '') if config else '',
                keyboard_type=ft.KeyboardType.NUMBER,
                hint_text="SteamのアプリケーションID"
            ),
            'depot_id': ft.TextField(
                label="Depot ID *",
                value=config.get('depot_id', '') if config else '',
                keyboard_type=ft.KeyboardType.NUMBER,
                hint_text="コンテンツを格納するデポットID"
            ),
            'branch': ft.TextField(
                label="ブランチ",
                value=config.get('branch', '') if config else '',
                hint_text="空欄時は手動承認が必要"
            ),
            'description': ft.TextField(
                label="アップロード説明 *",
                value=config.get('description', '') if config else '',
                multiline=True,
                min_lines=2,
                max_lines=3
            ),
            'content_path': ft.TextField(
                label="コンテンツパス *",
                value=config.get('content_path', '') if config else '',
                hint_text="コンテンツフォルダへのパス",
                width=300
            )
        }
        
        return fields
    
    @staticmethod
    def build_config_dialog_content(fields, folder_picker_btn, steam_buttons):
        """設定ダイアログのコンテンツを構築"""
        build_btn, depot_btn = steam_buttons
        
        return ft.Container(
            content=ft.Column([
                fields['name'] if 'name' in fields and not fields['name'].read_only else None,
                fields['app_id'],
                ft.Row([build_btn, depot_btn]),
                fields['depot_id'],
                fields['branch'],
                ft.Text("• 入力時は自動的にそのブランチに反映されます", size=11, color=ft.Colors.GREY),
                ft.Text("• 'public'と入力するとデフォルトブランチとして公開", size=11, color=ft.Colors.GREY),
                ft.Container(height=5),
                fields['description'],
                ft.Row([fields['content_path'], folder_picker_btn])
            ], tight=True),
            width=400,
            height=450 if 'name' not in fields or fields['name'].read_only else 500
        )


class PlatformCommands:
    """プラットフォーム固有のコマンドを管理"""
    
    @staticmethod
    def open_folder(path: str):
        """フォルダを開く（プラットフォーム対応）"""
        import platform
        import subprocess
        import os
        
        if not path or not os.path.exists(path):
            return False
            
        if platform.system() == "Darwin":  # macOS
            subprocess.run(["open", path])
        elif platform.system() == "Windows":
            subprocess.run(["explorer", path])
        else:  # Linux
            subprocess.run(["xdg-open", path])
        
        return True