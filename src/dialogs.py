"""
Dialog functions for Morn Steam Upload Helper.
"""

import flet as ft
from utils import open_steam_page, log_message


def show_error_dialog(page, message):
    """Show an error dialog with the given message."""
    def close_dialog(e):
        error_dialog.open = False
        page.update()
    
    error_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("エラー"),
        content=ft.Text(message),
        actions=[ft.TextButton("閉じる", on_click=close_dialog)],
        actions_alignment=ft.MainAxisAlignment.END
    )
    
    page.overlay.append(error_dialog)
    error_dialog.open = True
    page.update()


def show_success_dialog(page, title, message):
    """Show a success dialog with custom title and message."""
    def close_dialog(e):
        dialog.open = False
        page.update()
    
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(title),
        content=ft.Text(message),
        actions=[ft.TextButton("OK", on_click=close_dialog)],
        actions_alignment=ft.MainAxisAlignment.END
    )
    
    page.overlay.append(dialog)
    dialog.open = True
    page.update()


def create_config_dialog(page, title, config_data, on_save, on_close):
    """Create a configuration dialog (used for both new and edit)."""
    # Create dialog fields
    dialog_fields = {
        'name': ft.TextField(label="設定名 *", value=config_data.get('name', ''), autofocus=True),
        'app_id': ft.TextField(label="App ID *", value=config_data.get('app_id', '')),
        'depot_id': ft.TextField(label="Depot ID *", value=config_data.get('depot_id', '')),
        'content_path': ft.TextField(label="コンテンツフォルダ *", value=config_data.get('content_path', ''), read_only=True),
        'build_output': ft.TextField(label="ビルド出力パス", value=config_data.get('build_output', '')),
        'branch': ft.TextField(label="ブランチ", value=config_data.get('branch', 'beta')),
        'description': ft.TextField(
            label="説明（任意）",
            value=config_data.get('description', ''),
            multiline=True,
            min_lines=2,
            max_lines=3
        )
    }
    
    # Create steam page buttons
    steam_buttons = ft.Row([
        ft.ElevatedButton(
            "ストアページ",
            icon=ft.Icons.OPEN_IN_NEW,
            on_click=lambda e: open_steam_page("store", dialog_fields['app_id'].value)
        ),
        ft.ElevatedButton(
            "パートナーページ",
            icon=ft.Icons.OPEN_IN_NEW,
            on_click=lambda e: open_steam_page("partner", dialog_fields['app_id'].value)
        ),
    ])
    
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(title),
        content=ft.Container(
            content=ft.Column([
                dialog_fields['name'],
                dialog_fields['app_id'],
                steam_buttons,
                dialog_fields['depot_id'],
                dialog_fields['content_path'],
                dialog_fields['build_output'],
                dialog_fields['branch'],
                dialog_fields['description']
            ], tight=True, scroll=ft.ScrollMode.AUTO),
            width=500,
            height=450
        ),
        actions=[
            ft.TextButton("キャンセル", on_click=on_close),
            ft.ElevatedButton(
                "保存",
                on_click=lambda e: on_save(dialog_fields)
            )
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )
    
    return dialog, dialog_fields


def show_two_factor_dialog(page, on_submit):
    """Show 2FA authentication dialog."""
    code_field = ft.TextField(
        label="Steam Guard コード",
        hint_text="6桁のコードを入力",
        autofocus=True,
        keyboard_type=ft.KeyboardType.NUMBER,
        max_length=6
    )
    
    def handle_submit(e):
        if code_field.value and len(code_field.value) >= 5:
            on_submit(code_field.value)
            dialog.open = False
            page.update()
    
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("二段階認証"),
        content=ft.Container(
            content=ft.Column([
                ft.Text("Steam Guardの認証コードを入力してください"),
                code_field
            ], tight=True),
            width=300
        ),
        actions=[
            ft.TextButton("キャンセル", on_click=lambda e: close_dialog()),
            ft.ElevatedButton("送信", on_click=handle_submit)
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )
    
    def close_dialog():
        dialog.open = False
        page.update()
    
    page.overlay.append(dialog)
    dialog.open = True
    page.update()
    
    return dialog