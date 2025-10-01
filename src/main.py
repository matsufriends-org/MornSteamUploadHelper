#!/usr/bin/env python3
"""
Morn Steam Upload Helper

A GUI application to simplify the Steam game upload process using SteamCMD.
This tool helps developers automate the process of uploading game builds to Steam.

Features:
- GUI interface for SteamCMD operations
- Save and manage multiple upload configurations
- Automatic VDF file generation
- Cross-platform support (Windows, macOS, Linux)

Security Note:
This application passes credentials to SteamCMD. For enhanced security,
it's recommended to use Steam Guard mobile authentication.

Author: MornSteamUploadHelper Contributors
License: Unlicense (Public Domain)
"""

import flet as ft
import subprocess
import json
import os
from pathlib import Path
import platform
import threading
import time
from datetime import datetime

# Import our modules
from constants import *
from steam_upload_helper import SteamUploadHelper
from utils import *
from dialogs import *
from console_monitor import start_console_monitor

def main(page: ft.Page):
    page.title = APP_NAME
    page.window.width = WINDOW_WIDTH
    page.window.height = WINDOW_HEIGHT
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO
    
    helper = SteamUploadHelper()
    
    # Login state management
    login_status = ft.Text("未ログイン", color=ft.Colors.RED, weight=ft.FontWeight.BOLD)
    
    # UI Components
    username_field = ft.TextField(
        label="Steam ユーザー名 *",
        value=helper.settings.get("username", ""),
        width=300,
        autofocus=True
    )
    
    password_field = ft.TextField(
        label="パスワード *",
        password=True,
        can_reveal_password=True,
        width=200
    )
    
    steam_guard_field = ft.TextField(
        label="Steam Guard コード (任意)",
        width=250
    )
    
    # Upload configuration fields
    config_dropdown = ft.Dropdown(
        label="アップロード設定",
        hint_text="設定を選択...",
        width=300,
        options=[ft.dropdown.Option(name) for name in helper.upload_configs.keys()],
        on_change=lambda e: load_upload_config(e)
    )
    
    
    app_id_field = ft.Text(value="", size=14)
    depot_id_field = ft.Text(value="", size=14)
    branch_field = ft.Text(value="", size=14)
    upload_description_field = ft.Text(value="", size=14, expand=True)
    content_path_field = ft.Text(value="", size=14, expand=True)
    
    def open_content_folder():
        if content_path_field.value and os.path.exists(content_path_field.value):
            if platform.system() == "Darwin":  # macOS
                subprocess.run(["open", content_path_field.value])
            elif platform.system() == "Windows":
                subprocess.run(["explorer", content_path_field.value])
            else:  # Linux
                subprocess.run(["xdg-open", content_path_field.value])
        else:
            log_message("コンテンツパスが設定されていないか、存在しません")
    
    steamcmd_path_text = ft.Text(
        value=helper.settings.get("steamcmd_path", "SteamCMDが選択されていません"),
        size=12
    )
    
    build_output_path_text = ft.Text(
        value=helper.settings.get("build_output_path", "未設定"),
        size=12
    )
    
    # Output log removed - using console output only
    
    progress_bar = ft.ProgressBar(width=740, visible=False)
    
    # Buttons
    login_in_progress = False
    
    def login_button_click(e):
        nonlocal login_in_progress
        if login_in_progress:
            log_message("ログイン処理中...")
            return
        login_in_progress = True
        try:
            login_to_steam_console(e)
        finally:
            login_in_progress = False
    
    login_button = ft.ElevatedButton(
        "コンソールを開いて自動ログイン",
        icon=ft.Icons.TERMINAL,
        on_click=login_button_click
    )
    
    # Error message text for login button
    login_error_text = ft.Text(
        "",
        size=11,
        color=ft.Colors.ERROR,
        visible=False
    )
    
    def check_content_builder_paths():
        """Check if ContentBuilder and SteamCMD are properly configured"""
        content_builder_path = helper.settings.get("content_builder_path")
        if not content_builder_path:
            login_button.disabled = True
            login_error_text.value = "ContentBuilderフォルダが設定されていません。基本設定から設定してください。"
            login_error_text.visible = True
            return False
            
        # Check OS-specific steamcmd
        steamcmd_path = None
        if platform.system() == "Darwin":  # macOS
            steamcmd_path = os.path.join(content_builder_path, "builder_osx", "steamcmd.sh")
        elif platform.system() == "Windows":
            steamcmd_path = os.path.join(content_builder_path, "builder", "steamcmd.exe")
        else:  # Linux
            steamcmd_path = os.path.join(content_builder_path, "builder_linux", "steamcmd.sh")
            
        if not steamcmd_path or not os.path.exists(steamcmd_path):
            login_button.disabled = True
            login_error_text.value = f"SteamCMDが見つかりません: {steamcmd_path if steamcmd_path else 'None'}"
            login_error_text.visible = True
            return False
            
        # All good
        login_button.disabled = False
        login_error_text.visible = False
        return True
    
    # Initial check
    check_content_builder_paths()
    
    confirm_login_button = ft.ElevatedButton(
        "ログインチェック",
        icon=ft.Icons.CHECK,
        on_click=lambda e: confirm_login_success(e),
        visible=False
    )
    
    
    # Removed auto/manual select buttons - ContentBuilder path handles this now
    
    
    reset_output_button = ft.ElevatedButton(
        "リセット",
        on_click=lambda e: reset_build_output_folder(e),
        disabled=False
    )
    
    manual_select_output_button = ft.ElevatedButton(
        "手動選択",
        on_click=lambda e: select_build_output_folder(e),
        disabled=False
    )
    
    
    new_config_button = ft.ElevatedButton(
        "新規設定",
        on_click=lambda e: show_new_config_dialog(),
        icon=ft.Icons.ADD,
        disabled=True
    )
    
    edit_config_button = ft.ElevatedButton(
        "設定を編集",
        on_click=lambda e: show_edit_config_dialog(),
        icon=ft.Icons.EDIT,
        disabled=True
    )
    
    delete_config_button = ft.ElevatedButton(
        "削除",
        on_click=lambda e: delete_current_config(e),
        icon=ft.Icons.DELETE,
        disabled=True
    )
    
    # Steam page buttons for selected config
    config_build_page_btn = ft.ElevatedButton(
        "ビルドページ",
        icon=ft.Icons.OPEN_IN_NEW,
        disabled=True,
        on_click=lambda e: open_steam_page_for_config("builds")
    )
    
    config_depot_page_btn = ft.ElevatedButton(
        "デポページ",
        icon=ft.Icons.OPEN_IN_NEW,
        disabled=True,
        on_click=lambda e: open_steam_page_for_config("depots")
    )
    
    def open_steam_page_for_config(page_type):
        if config_dropdown.value and app_id_field.value:
            url = f"https://partner.steamgames.com/apps/{page_type}/{app_id_field.value}"
            webbrowser.open(url)
            log_message(f"Steam {page_type} ページを開きました: {url}")
    
    # Upload prerequisites status
    login_status_text = ft.Text(
        "❌ コンソールを開いてログインしている",
        size=14
    )
    
    config_status_text = ft.Text(
        "❌ アップロード設定を選択している",
        size=14
    )
    
    def update_upload_button():
        # Update status icons
        is_logged_in = helper.is_logged_in
        has_config = bool(config_dropdown.value)
        
        login_status_text.value = f"{'✅' if is_logged_in else '❌'} コンソールを開いてログインしている"
        config_status_text.value = f"{'✅' if has_config else '❌'} アップロード設定を選択している"
        
        # Enable upload button only when both conditions are met
        upload_button.disabled = not (is_logged_in and has_config)
        page.update()
    
    upload_button = ft.ElevatedButton(
        "Steamにアップロード",
        on_click=lambda e: run_upload(e),
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
        disabled=True  # Enabled after login
    )
    
    
    def log_message(message):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def confirm_login_success(e):
        """Manually confirm login success when auto-detection fails"""
        if helper.steamcmd_terminal:
            helper.is_logged_in = True
            login_status.value = f"{username_field.value} としてログイン中"
            login_status.color = ft.Colors.GREEN
            enable_controls(True)
            log_message("ログインが手動で確認されました！")
            confirm_login_button.visible = False
            # Save username
            helper.settings["username"] = username_field.value
            helper.save_settings()
            # Start console monitor
            start_console_monitor()
            page.update()
    
    def enable_controls(enabled=True):
        # Configuration controls are always available
        config_dropdown.disabled = False
        new_config_button.disabled = False
        
        # These buttons only work with a selected configuration
        if config_dropdown.value:
            delete_config_button.disabled = False
            edit_config_button.disabled = False
            # Enable Steam page buttons if App ID exists
            if app_id_field.value:
                config_build_page_btn.disabled = False
                config_depot_page_btn.disabled = False
            else:
                config_build_page_btn.disabled = True
                config_depot_page_btn.disabled = True
        else:
            delete_config_button.disabled = True
            edit_config_button.disabled = True
            config_build_page_btn.disabled = True
            config_depot_page_btn.disabled = True
        
        # Update upload button and status indicators
        update_upload_button()
        
        # System settings (always available - no longer dependent on login)
        # select_steamcmd_button.disabled = not enabled  # Commented out to keep always enabled
        # select_output_button.disabled = not enabled    # Commented out to keep always enabled
        
        page.update()
    
    def load_upload_config(e):
        if not config_dropdown.value:
            return
        
        config = helper.upload_configs.get(config_dropdown.value, {})
        app_id_field.value = config.get("app_id", "")
        depot_id_field.value = config.get("depot_id", "")
        branch_field.value = config.get("branch", "")
        upload_description_field.value = config.get("description", "")
        
        # Update content path if saved
        if "content_path" in config and config["content_path"]:
            content_path_field.value = config["content_path"]
        else:
            content_path_field.value = ""
        
        # Update control states after loading configuration
        enable_controls(helper.is_logged_in)
        
        page.update()
        log_message(f"設定を読み込みました: {config_dropdown.value}")
    
    def delete_current_config(e):
        if not config_dropdown.value:
            show_error_dialog("削除する設定を選択してください")
            return
        
        name = config_dropdown.value
        helper.delete_upload_config(name)
        
        # Update dropdown
        config_dropdown.options = [ft.dropdown.Option(name) for name in helper.upload_configs.keys()]
        config_dropdown.value = None
        
        # Clear fields
        app_id_field.value = ""
        depot_id_field.value = ""
        branch_field.value = ""
        upload_description_field.value = ""
        content_path_field.value = ""
        
        # Update control states after deletion
        enable_controls(helper.is_logged_in)
        
        page.update()
        log_message(f"設定を削除しました: {name}")
    
    def show_error_dialog(message):
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("エラー"),
            content=ft.Text(message),
            actions=[
                ft.TextButton("OK", on_click=lambda e: close_dialog(dlg))
            ]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()
    
    def close_dialog(dlg):
        dlg.open = False
        page.update()
    
    def show_new_config_dialog():
        new_config_name = ft.TextField(
            label="設定名 *",
            autofocus=True
        )
        new_app_id = ft.TextField(
            label="App ID *",
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="SteamのアプリケーションID",
            on_change=lambda e: update_steam_buttons_new(e)
        )
        new_depot_id = ft.TextField(
            label="Depot ID *",
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="コンテンツを格納するデポットID"
        )
        new_branch = ft.TextField(
            label="ブランチ",
            hint_text="空欄時は手動承認が必要"
        )
        new_description = ft.TextField(
            label="アップロード説明 *",
            multiline=True,
            min_lines=2,
            max_lines=3
        )
        new_content_path = ft.TextField(
            label="コンテンツパス *",
            hint_text="コンテンツフォルダへのパス",
            width=300
        )
        
        def select_folder_for_dialog(e):
            def on_folder_selected(e: ft.FilePickerResultEvent):
                if e.path:
                    new_content_path.value = e.path
                    dlg.update()
            
            folder_picker = ft.FilePicker(on_result=on_folder_selected)
            page.overlay.append(folder_picker)
            page.update()
            folder_picker.get_directory_path(dialog_title="コンテンツフォルダを選択")
        
        select_path_btn = ft.IconButton(
            ft.Icons.FOLDER_OPEN,
            on_click=select_folder_for_dialog,
            tooltip="フォルダを選択"
        )
        
        # Steam page buttons
        build_page_btn = ft.ElevatedButton(
            "ビルドページを開く",
            disabled=True,
            on_click=lambda e: open_steam_page("builds", new_app_id.value) if new_app_id.value else None
        )
        
        depot_page_btn = ft.ElevatedButton(
            "デポページを開く",
            disabled=True,
            on_click=lambda e: open_steam_page("depots", new_app_id.value) if new_app_id.value else None
        )
        
        def update_steam_buttons_new(e):
            enabled = bool(new_app_id.value and new_app_id.value.strip())
            build_page_btn.disabled = not enabled
            depot_page_btn.disabled = not enabled
            dlg.update()
        
        def open_steam_page(page_type, app_id):
            if app_id:
                url = f"https://partner.steamgames.com/apps/{page_type}/{app_id}"
                webbrowser.open(url)
                log_message(f"Steam {page_type} ページを開きました: {url}")
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("新規設定"),
            content=ft.Column([
                new_config_name,
                new_app_id,
                ft.Row([build_page_btn, depot_page_btn]),
                new_depot_id,
                new_branch,
                ft.Text("• 入力時は自動的にそのブランチに反映されます", size=11, color=ft.Colors.GREY),
                ft.Text("• 'public'と入力するとデフォルトブランチとして公開", size=11, color=ft.Colors.GREY),
                ft.Container(height=5),
                new_description,
                ft.Row([
                    new_content_path,
                    select_path_btn
                ]),
            ], height=500, width=400, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: close_dialog(dlg)),
                ft.TextButton("作成", on_click=lambda e: create_new_config(
                    dlg, new_config_name.value, new_app_id.value, new_depot_id.value, 
                    new_branch.value, new_description.value, new_content_path.value
                ))
            ]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()
    
    def create_new_config(dlg, name, app_id, depot_id, branch, description, content_path):
        if not name:
            return
        
        config = {
            "app_id": app_id,
            "depot_id": depot_id,
            "branch": branch,
            "description": description,
            "content_path": content_path
        }
        
        helper.save_upload_config(name, config)
        
        # Update dropdown
        config_dropdown.options = [ft.dropdown.Option(name) for name in helper.upload_configs.keys()]
        config_dropdown.value = name
        
        # Load the new config
        load_upload_config(None)
        
        close_dialog(dlg)
        log_message(f"新規設定を作成しました: {name}")
    
    def show_edit_config_dialog():
        if not config_dropdown.value:
            return
        
        current_config = helper.upload_configs.get(config_dropdown.value, {})
        
        edit_config_name = ft.TextField(
            label="設定名",
            value=config_dropdown.value,
            read_only=True,
            autofocus=True
        )
        edit_app_id = ft.TextField(
            label="App ID *",
            value=current_config.get("app_id", ""),
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="SteamのアプリケーションID",
            on_change=lambda e: update_steam_buttons_edit(e)
        )
        edit_depot_id = ft.TextField(
            label="Depot ID *",
            value=current_config.get("depot_id", ""),
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="コンテンツを格納するデポットID"
        )
        edit_branch = ft.TextField(
            label="ブランチ",
            value=current_config.get("branch", ""),
            hint_text="空欄時は手動承認が必要"
        )
        edit_description = ft.TextField(
            label="アップロード説明 *",
            value=current_config.get("description", ""),
            multiline=True,
            min_lines=2,
            max_lines=3
        )
        edit_content_path = ft.TextField(
            label="コンテンツパス *",
            value=current_config.get("content_path", ""),
            hint_text="コンテンツフォルダへのパス",
            width=300
        )
        
        def select_folder_for_edit(e):
            def on_folder_selected(e: ft.FilePickerResultEvent):
                if e.path:
                    edit_content_path.value = e.path
                    dlg.update()
            
            folder_picker = ft.FilePicker(on_result=on_folder_selected)
            page.overlay.append(folder_picker)
            page.update()
            folder_picker.get_directory_path(dialog_title="コンテンツフォルダを選択")
        
        select_path_btn = ft.IconButton(
            ft.Icons.FOLDER_OPEN,
            on_click=select_folder_for_edit,
            tooltip="フォルダを選択"
        )
        
        # Steam page buttons for edit dialog
        edit_build_page_btn = ft.ElevatedButton(
            "ビルドページを開く",
            disabled=not bool(current_config.get("app_id")),
            on_click=lambda e: open_steam_page_edit("builds", edit_app_id.value) if edit_app_id.value else None
        )
        
        edit_depot_page_btn = ft.ElevatedButton(
            "デポページを開く",
            disabled=not bool(current_config.get("app_id")),
            on_click=lambda e: open_steam_page_edit("depots", edit_app_id.value) if edit_app_id.value else None
        )
        
        def update_steam_buttons_edit(e):
            enabled = bool(edit_app_id.value and edit_app_id.value.strip())
            edit_build_page_btn.disabled = not enabled
            edit_depot_page_btn.disabled = not enabled
            dlg.update()
        
        def open_steam_page_edit(page_type, app_id):
            if app_id:
                url = f"https://partner.steamgames.com/apps/{page_type}/{app_id}"
                webbrowser.open(url)
                log_message(f"Steam {page_type} ページを開きました: {url}")
        
        def save_edited_config(e):
            # Validate inputs
            if not edit_app_id.value or not edit_depot_id.value:
                show_error_dialog("App IDとDepot IDは必須です！")
                return
            
            # Update config
            config = {
                "app_id": edit_app_id.value,
                "depot_id": edit_depot_id.value,
                "branch": edit_branch.value,
                "description": edit_description.value,
                "content_path": edit_content_path.value
            }
            
            helper.save_upload_config(config_dropdown.value, config)
            
            # Reload the configuration
            load_upload_config(None)
            
            close_dialog(dlg)
            log_message(f"設定を更新しました: {config_dropdown.value}")
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("設定を編集"),
            content=ft.Container(
                content=ft.Column([
                    edit_config_name,
                    edit_app_id,
                    ft.Row([edit_build_page_btn, edit_depot_page_btn]),
                    edit_depot_id,
                    edit_branch,
                    ft.Text("• 入力時は自動的にそのブランチに反映されます", size=11, color=ft.Colors.GREY),
                    ft.Text("• 'public'と入力するとデフォルトブランチとして公開", size=11, color=ft.Colors.GREY),
                    ft.Container(height=5),
                    edit_description,
                    ft.Row([edit_content_path, select_path_btn])
                ], tight=True),
                width=400,
                height=450
            ),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: close_dialog(dlg)),
                ft.TextButton("保存", on_click=save_edited_config),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        page.overlay.append(dlg)
        dlg.open = True
        page.update()
    
    def show_2fa_dialog():
        auth_code_field = ft.TextField(
            label="Steam Guardコードを入力（任意）",
            autofocus=True,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        waiting_text = ft.Text("モバイルアプリでの承認を待っています...", visible=False)
        progress_ring = ft.ProgressRing(width=16, height=16, stroke_width=2, visible=False)
        
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
        page.overlay.append(dlg)
        dlg.open = True
        page.update()
        return dlg, auth_code_field
    
    def wait_for_mobile_approval(dlg, waiting_text, progress_ring):
        waiting_text.visible = True
        progress_ring.visible = True
        page.update()
        # Set flag to continue monitoring the login process
        helper.waiting_for_mobile_2fa = True
        close_dialog(dlg)
        # Continue the login process
        continue_2fa_login()
    
    def cancel_2fa(dlg):
        helper.waiting_for_mobile_2fa = False
        close_dialog(dlg)
    
    def submit_2fa_code(code, dlg):
        if code:
            helper.steam_guard_code = code
            close_dialog(dlg)
            # Send the code to the existing process if available
            if hasattr(helper, 'steamcmd_2fa_process') and helper.steamcmd_2fa_process:
                try:
                    helper.steamcmd_2fa_process.stdin.write(f"{code}\n")
                    helper.steamcmd_2fa_process.stdin.flush()
                    continue_2fa_login()
                except:
                    # If that fails, retry login with code
                    login_to_steam(None)
            else:
                # Retry login with 2FA code
                login_to_steam(None)
    
    def continue_2fa_login():
        """Continue monitoring the existing SteamCMD process for 2FA"""
        if not hasattr(helper, 'steamcmd_2fa_process') or not helper.steamcmd_2fa_process:
            return
        
        process = helper.steamcmd_2fa_process
        login_status.value = "2FA承認を待っています..."
        login_status.color = ft.Colors.ORANGE
        page.update()
        
        # Run in separate thread to avoid blocking UI
        import threading
        
        def monitor_process():
            try:
                # Platform-specific non-blocking read
                if platform.system() != "Windows":
                    # Use select for non-blocking read on Unix-like systems
                    import select
                    import fcntl
                    import os as os_module
                    
                    # Make stdout non-blocking
                    fd = process.stdout.fileno()
                    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
                    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os_module.O_NONBLOCK)
                    
                    timeout_counter = 0
                    while timeout_counter < 60:  # 60 second timeout
                        # Check if there's data to read
                        ready, _, _ = select.select([process.stdout], [], [], 1.0)
                        
                        if ready:
                            try:
                                line = process.stdout.readline()
                                if line:
                                    line = line.strip()
                                    if line:
                                        log_message(line)
                                    if "Logged in OK" in line or "Logged in successfully" in line or "Logged in as" in line:
                                        helper.is_logged_in = True
                                        login_status.value = f"{username_field.value} としてログイン中"
                                        login_status.color = ft.Colors.GREEN
                                        enable_controls(True)
                                        
                                        # Save username
                                        helper.settings["username"] = username_field.value
                                        helper.save_settings()
                                        
                                        log_message("2FA認証後、ログインに成功しました！")
                                        page.update()
                                        break
                                    elif "FAILED" in line or "Login Failure" in line:
                                        log_message("2FA verification failed")
                                        page.sync()
                                        show_error_dialog("2FA verification failed. Please try again.")
                                        break
                            except Exception:
                                pass
                            timeout_counter = 0  # Reset timeout when we get data
                        else:
                            timeout_counter += 1
                            
                        # Check process status
                        if process.poll() is not None:
                            break
                else:
                    # Windows: Use threading and queue for non-blocking read
                    import queue
                    import threading
                    
                    output_queue = queue.Queue()
                    
                    def read_output(proc, q):
                        try:
                            for line in iter(proc.stdout.readline, ''):
                                if line:
                                    q.put(line.strip())
                        except Exception:
                            pass
                    
                    reader_thread = threading.Thread(target=read_output, args=(process, output_queue))
                    reader_thread.daemon = True
                    reader_thread.start()
                    
                    timeout_counter = 0
                    while timeout_counter < 60:  # 60 second timeout
                        try:
                            line = output_queue.get(timeout=1.0)
                            if line:
                                log_message(line)
                                    
                            timeout_counter = 0  # Reset timeout when we get data
                                    
                            if "Logged in OK" in line or "Logged in successfully" in line or "Logged in as" in line:
                                helper.is_logged_in = True
                                login_status.value = f"{username_field.value} としてログイン中"
                                login_status.color = ft.Colors.GREEN
                                enable_controls(True)
                                
                                # Save username
                                helper.settings["username"] = username_field.value
                                helper.save_settings()
                                
                                log_message("2FA認証後、ログインに成功しました！")
                                page.update()
                                break
                            elif "FAILED" in line or "Login Failure" in line:
                                log_message("2FA verification failed")
                                page.sync()
                                show_error_dialog("2FA verification failed. Please try again.")
                                break
                        except queue.Empty:
                            timeout_counter += 1
                    
                        # Check if process is still alive
                        if process.poll() is not None:
                            break
                
                if timeout_counter >= 60:
                    log_message("2FA timeout")
                    process.terminate()
                    process.wait()
                    page.sync()
                    show_error_dialog("2FA verification timeout. Please try again.")
                    
            except Exception as ex:
                log_message(f"Error during 2FA: {str(ex)}")
            finally:
                helper.steamcmd_2fa_process = None
                progress_bar.visible = False
                login_button.disabled = False
                page.update()
        
        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=monitor_process, daemon=True)
        monitor_thread.start()
    
    def cleanup_temp_scripts():
        """Remove any temporary script files containing credentials."""
        try:
            # Clean up all possible temporary script paths
            temp_scripts = [
                Path("./configs/steamcmd_session.sh"),
                Path("./configs/steamcmd_session.bat"),
                Path("./configs/steamcmd_login.sh"),
                Path("./configs/steamcmd_login.bat")
            ]
            
            for script_path in temp_scripts:
                if script_path.exists():
                    script_path.unlink()
                    log_message(f"一時スクリプトファイルを削除: {script_path.name}")
        except Exception as e:
            log_message(f"警告: 一時スクリプトファイルの削除エラー: {e}")
    
    def start_console_monitor():
        """Start monitoring the console to detect if it's closed"""
        if helper.console_monitor_thread and helper.console_monitor_thread.is_alive():
            return  # Already monitoring
        
        def monitor_console():
            log_message("コンソール監視を開始しました...")
            monitor_count = 0
            
            while helper.is_logged_in and helper.steamcmd_terminal:
                monitor_count += 1
                if monitor_count % 5 == 0:  # Log every 10 seconds
                    log_message(f"コンソール監視中... (チェック #{monitor_count})")
                # Check if console is still open based on platform
                console_closed = False
                
                if platform.system() == "Darwin":  # macOS
                    # Check if Terminal has any windows with steamcmd
                    try:
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
                    except Exception as e:
                        log_message(f"macOS コンソールチェックエラー: {e}")
                        
                elif platform.system() == "Windows":
                    # Check if cmd window with steamcmd is still open
                    try:
                        # Check for steamcmd.exe process
                        result = subprocess.run(
                            ['tasklist', '/FI', 'IMAGENAME eq steamcmd.exe'],
                            capture_output=True, text=True
                        )
                        
                        # Also check for cmd windows with our script
                        cmd_result = subprocess.run(
                            ['tasklist', '/V', '/FI', 'IMAGENAME eq cmd.exe'],
                            capture_output=True, text=True
                        )
                        
                        has_steamcmd = "steamcmd.exe" in result.stdout
                        has_cmd_with_steam = "SteamCMD" in cmd_result.stdout or "steamcmd_session" in cmd_result.stdout
                        
                        if not has_steamcmd and not has_cmd_with_steam:
                            console_closed = True
                            log_message(f"Windows: SteamCMDコンソールが見つかりません (steamcmd.exe: {has_steamcmd}, cmd: {has_cmd_with_steam})")
                        else:
                            if monitor_count % 10 == 0:
                                log_message(f"Windows: SteamCMDコンソール検出 (steamcmd.exe: {has_steamcmd}, cmd: {has_cmd_with_steam})")
                    except Exception as e:
                        log_message(f"Windows コンソールチェックエラー: {e}")
                
                if console_closed:
                    log_message("コンソールが閉じられました！ログイン状態をリセットしています...")
                    
                    # Reset login state
                    helper.is_logged_in = False
                    helper.steamcmd_terminal = False
                    login_status.value = "未ログイン"
                    login_status.color = ft.Colors.RED
                    
                    # Disable upload controls
                    enable_controls(False)
                    
                    # Re-enable login button
                    login_button.disabled = False
                    progress_bar.visible = False
                    
                    page.update()
                    break
                
                # Check every 2 seconds
                time.sleep(2)
            
            log_message("コンソール監視を停止しました。")
            helper.console_monitor_thread = None
            log_message(f"監視終了理由: is_logged_in={helper.is_logged_in}, steamcmd_terminal={helper.steamcmd_terminal}")
        
        # Start monitoring thread
        helper.console_monitor_thread = threading.Thread(target=monitor_console, daemon=True)
        helper.console_monitor_thread.start()
        log_message(f"コンソール監視スレッドを開始しました (thread alive: {helper.console_monitor_thread.is_alive()})")
    
    def login_to_steam_console(e):
        # Prevent multiple console openings
        if helper.steamcmd_terminal:
            log_message("Steamコンソールは既に開いています")
            return
        
        # Mark as opening to prevent duplicates
        helper.steamcmd_terminal = True
        
        # Disable button immediately
        login_button.disabled = True
        page.update()
            
        if not username_field.value or not password_field.value:
            show_error_dialog("ユーザー名とパスワードの両方を入力してください")
            login_button.disabled = False
            helper.steamcmd_terminal = False
            page.update()
            return
        
        steamcmd_path = helper.settings.get("steamcmd_path")
        if not steamcmd_path:
            log_message("エラー: ContentBuilderフォルダが設定されていません。")
            show_error_dialog("ContentBuilderフォルダが設定されていません。基本設定からContentBuilderフォルダを選択してください。")
            login_button.disabled = False
            helper.steamcmd_terminal = False
            page.update()
            return
        
        progress_bar.visible = True
        page.update()
        
        try:
            log_message("Steamにログインを試みています...")
            log_message(f"SteamCMDを使用: {steamcmd_path}")
            
            # Ensure steamcmd_path is set
            if not steamcmd_path:
                log_message("エラー: SteamCMDパスが設定されていません")
                return
            
            # Make sure steamcmd is executable on Unix systems
            if platform.system() != "Windows" and steamcmd_path:
                try:
                    os.chmod(steamcmd_path, 0o755)
                    # Also make the actual steamcmd binary executable if using the SDK version
                    if "builder_osx" in steamcmd_path:
                        steamcmd_binary = os.path.join(os.path.dirname(steamcmd_path), "steamcmd")
                        if os.path.exists(steamcmd_binary):
                            os.chmod(steamcmd_binary, 0o755)
                            log_message(f"steamcmdバイナリを実行可能にしました: {steamcmd_binary}")
                except Exception as chmod_error:
                    log_message(f"警告: 実行権限を設定できませんでした: {chmod_error}")
            
            # Add environment variables to force fresh login
            env = os.environ.copy()
            env['HOME'] = os.path.expanduser('~')
            
            # Open in terminal and keep it open
            steamcmd_terminal_path = None
            
            if platform.system() == "Darwin":  # macOS
                # Convert to absolute path if relative
                abs_steamcmd_path = os.path.abspath(steamcmd_path)
                
                # Build login command
                login_cmd = f"login {username_field.value} {password_field.value}"
                if steam_guard_field.value:
                    login_cmd += f" {steam_guard_field.value}"
                
                # Create a script that keeps the terminal open and auto-login
                script_content = f'''#!/bin/bash
echo "SteamCMD コンソール - このウィンドウを閉じないでください"
echo "このコンソールはアップロードに使用されます"
echo ""
cd "{os.path.dirname(abs_steamcmd_path)}"

# Start SteamCMD with login command
echo "SteamCMDを起動してログインしています..."
echo ""

# Create a temporary file to capture output
TEMP_LOG="/tmp/steamcmd_login_$$.log"

# Run SteamCMD with login command but stay in console
"{abs_steamcmd_path}" +{login_cmd}
'''
                
                script_path = Path("./configs/steamcmd_session.sh")
                script_path.parent.mkdir(exist_ok=True)
                with open(script_path, 'w') as f:
                    f.write(script_content)
                os.chmod(script_path, 0o755)
                
                # Open in Terminal and keep it open
                # Use 'open' command to avoid extra window
                subprocess.run(['open', '-a', 'Terminal', script_path])
                
                # Store the terminal reference
                helper.steamcmd_terminal = True
                
                log_message("SteamCMDコンソールが開きました。自動でログインしています...")
                log_message("ログインが完了するまでお待ちください。")
                log_message("Steam Guardコードの入力を求められた場合は、ターミナルに入力してください。")
                log_message("ログインに成功すると、コンソールはアップロード用に開いたままになります。")
                
                # Don't enable controls yet - wait for actual login
                helper.is_logged_in = False
                login_status.value = "Steamコンソールが開きました - ログインを待っています..."
                login_status.color = ft.Colors.ORANGE
                enable_controls(False)
                
                # Test button is always enabled, no need to update
                
                login_button.disabled = True
                
                # Start a thread to monitor for login status
                def monitor_login_status():
                    import time
                    time.sleep(3)  # Wait a bit for login to start
                    
                    # Keep checking until login succeeds or fails (max 60 seconds)
                    check_count = 0
                    max_checks = 30  # 30 * 2 seconds = 60 seconds max
                    while helper.steamcmd_terminal and not helper.is_logged_in and check_count < max_checks:
                        try:
                            # First check if Terminal is still open
                            window_check = subprocess.run(
                                ['osascript', '-e', 'tell application "Terminal" to count windows'],
                                capture_output=True, text=True
                            )
                            
                            if window_check.returncode != 0 or window_check.stdout.strip() == "0":
                                # Terminal closed
                                log_message("コンソールが閉じられました！")
                                helper.is_logged_in = False
                                helper.steamcmd_terminal = False
                                login_status.value = "未ログイン"
                                login_status.color = ft.Colors.RED
                                login_button.disabled = False
                                enable_controls(False)
                                confirm_login_button.visible = False
                                page.update()
                                break
                            
                            # Check Terminal window content
                            check_script = '''
                            tell application "Terminal"
                                set loginStatus to "unknown"
                                set windowFound to false
                                set windowCount to count windows
                                
                                if windowCount = 0 then
                                    return "console_closed"
                                end if
                                
                                try
                                    repeat with w in windows
                                        try
                                            set tabContent to contents of selected tab of w
                                            if tabContent contains "steamcmd" or tabContent contains "Steam>" then
                                                set windowFound to true
                                                if tabContent contains "Rate Limit Exceeded" then
                                                    set loginStatus to "rate_limited"
                                                    exit repeat
                                                else if tabContent contains "FAILED" and tabContent contains "Login Failure" then
                                                    set loginStatus to "failed"
                                                    exit repeat
                                                else if tabContent contains "Waiting for user info...OK" then
                                                    -- Login completed successfully
                                                    set loginStatus to "logged_in"
                                                    exit repeat
                                                end if
                                            end if
                                        on error
                                            -- Window closed while checking, continue to next
                                        end try
                                    end repeat
                                on error
                                    return "console_closed"
                                end try
                                
                                if not windowFound then
                                    return "console_closed"
                                end if
                                return loginStatus
                            end tell
                            '''
                            result = subprocess.run(
                                ['osascript', '-e', check_script],
                                capture_output=True, text=True
                            )
                            
                            status = result.stdout.strip()
                            
                            # Also check if steamcmd process is still running
                            ps_check = subprocess.run(
                                ['ps', 'aux'], 
                                capture_output=True, text=True
                            )
                            has_steamcmd_process = 'steamcmd' in ps_check.stdout.lower()
                            
                            # If no window found or no steamcmd process, consider it closed
                            if status == "console_closed" or (status == "unknown" and not has_steamcmd_process):
                                log_message("コンソールウィンドウが見つかりません！")
                                helper.is_logged_in = False
                                helper.steamcmd_terminal = False
                                login_status.value = "未ログイン"
                                login_status.color = ft.Colors.RED
                                login_button.disabled = False
                                enable_controls(False)
                                confirm_login_button.visible = False
                                page.update()
                                break
                            
                            # Debug logging
                            if check_count % 5 == 0:  # Log every 10 seconds
                                log_message(f"ログインチェック #{check_count}: ステータス = {status}")
                                log_message(f"デバッグ: ウィンドウ数 = {window_check.stdout.strip()}, steamcmdプロセス = {has_steamcmd_process}, AppleScript結果 = {result.stdout[:100] if result.stdout else 'None'}")
                            
                            if status == "rate_limited":
                                helper.is_logged_in = False
                                helper.steamcmd_terminal = False
                                login_status.value = "ログイン失敗 - レート制限"
                                login_status.color = ft.Colors.RED
                                login_button.disabled = False
                                enable_controls(False)
                                log_message("レート制限によりログインに失敗しました。5-10分待ってください。")
                                show_error_dialog("レート制限を超えました！5-10分待ってから再試行してください。")
                                break
                            elif status == "logged_in":
                                helper.is_logged_in = True
                                login_status.value = f"{username_field.value} としてログイン中"
                                login_status.color = ft.Colors.GREEN
                                enable_controls(True)
                                log_message("Steamログインが正常に完了しました！")
                                # Save username (NOT password)
                                helper.settings["username"] = username_field.value
                                helper.save_settings()
                                
                                # Clean up temporary script files for security
                                cleanup_temp_scripts()
                                
                                # Clear password field for security
                                password_field.value = ""
                                steam_guard_field.value = ""
                                page.update()
                                
                                # Start console monitor after successful login
                                start_console_monitor()
                                break
                            elif status == "failed":
                                helper.is_logged_in = False
                                helper.steamcmd_terminal = False
                                login_status.value = "ログイン失敗"
                                login_status.color = ft.Colors.RED
                                login_button.disabled = False
                                enable_controls(False)
                                log_message("ログインに失敗しました。資格情報を確認してください。")
                                show_error_dialog("ログインに失敗しました。ユーザー名とパスワードを確認してください。")
                                cleanup_temp_scripts()  # Clean up on failure
                                break
                        except Exception as e:
                            log_message(f"ログイン監視エラー: {e}")
                            pass
                        
                        time.sleep(2)  # Check every 2 seconds
                        check_count += 1
                        page.update()
                    
                    if check_count >= max_checks and not helper.is_logged_in:
                        log_message("ログイン監視がタイムアウトしました。手動でログインを確認する必要があるかもしれません。")
                        login_status.value = "ログインタイムアウト - コンソールを確認してください"
                        login_status.color = ft.Colors.ORANGE
                        confirm_login_button.visible = True
                        # Start console monitor even during login check
                        start_console_monitor()
                    
                    page.update()
                
                threading.Thread(target=monitor_login_status, daemon=True).start()
                
                page.update()
                return
            elif platform.system() == "Windows":
                # Convert to absolute path if relative
                abs_steamcmd_path = os.path.abspath(steamcmd_path)
                
                # Build login command
                login_cmd = f"login {username_field.value} {password_field.value}"
                if steam_guard_field.value:
                    login_cmd += f" {steam_guard_field.value}"
                
                # Similar for Windows
                script_content = f'''@echo off
echo SteamCMD コンソール - このウィンドウを閉じないでください
echo このコンソールはアップロードに使用されます
echo.
cd /d "{os.path.dirname(abs_steamcmd_path)}"
echo SteamCMDを起動してログインしています...
echo.
"{abs_steamcmd_path}" +{login_cmd}
pause
'''
                
                script_path = Path("./configs/steamcmd_session.bat")
                script_path.parent.mkdir(exist_ok=True)
                with open(script_path, 'w') as f:
                    f.write(script_content)
                
                subprocess.Popen(['start', 'cmd', '/k', str(script_path)], shell=True)
                
                helper.steamcmd_terminal = True
                log_message("SteamCMDコンソールが開きました。コマンドウィンドウでログインしてください。")
                log_message("使用方法: +login ユーザー名 パスワード [Steam Guardコード]")
                log_message("ログイン後、アップロード用にコンソールを開いたままにしてください。")
                
                helper.is_logged_in = False
                login_status.value = "Steamコンソールが開きました - ログインを待っています..."
                login_status.color = ft.Colors.ORANGE
                enable_controls(False)
                
                # Test button is always enabled, no need to update
                
                login_button.disabled = True
                
                # Start console monitoring thread
                start_console_monitor()
                
                # Start a thread to monitor for successful login
                def monitor_login_status():
                    import time
                    time.sleep(3)  # Wait a bit for login to start
                    
                    # Check for rate limit error
                    rate_limit_detected = False
                    for i in range(10):  # Check for 10 seconds
                        try:
                            # Check if Terminal window contains rate limit error
                            check_script = '''
                            tell application "Terminal"
                                set rateLimit to false
                                try
                                    repeat with w in windows
                                        if (contents of selected tab of w) contains "Rate Limit Exceeded" then
                                            set rateLimit to true
                                            exit repeat
                                        end if
                                    end repeat
                                end try
                                return rateLimit
                            end tell
                            '''
                            result = subprocess.run(
                                ['osascript', '-e', check_script],
                                capture_output=True, text=True
                            )
                            if result.stdout.strip() == "true":
                                rate_limit_detected = True
                                break
                        except:
                            pass
                        time.sleep(1)
                    
                    if rate_limit_detected:
                        # Handle rate limit error
                        helper.is_logged_in = False
                        helper.steamcmd_terminal = False
                        login_status.value = "ログイン失敗 - レート制限"
                        login_status.color = ft.Colors.RED
                        login_button.disabled = False
                        log_message("Login failed due to rate limit. Please wait 5-10 minutes.")
                        show_error_dialog("Rate limit exceeded! Please wait 5-10 minutes before trying again.")
                    elif helper.steamcmd_terminal:
                        # Don't assume success - keep monitoring
                        # User needs to actually complete login
                        pass
                    
                    page.update()
                
                threading.Thread(target=monitor_login_status, daemon=True).start()
                
                page.update()
                return
            else:  # Linux
                # Convert to absolute path if relative
                abs_steamcmd_path = os.path.abspath(steamcmd_path)
                
                # Build login command
                login_cmd = f"login {username_field.value} {password_field.value}"
                if steam_guard_field.value:
                    login_cmd += f" {steam_guard_field.value}"
                
                # Create a script that keeps the terminal open
                script_content = f'''#!/bin/bash
echo "SteamCMD コンソール - このウィンドウを閉じないでください"
echo "このコンソールはアップロードに使用されます"
echo ""
cd "{os.path.dirname(abs_steamcmd_path)}"

# Start SteamCMD and login (without +quit to stay in console)
echo "SteamCMDを起動してログインしています..."
echo ""
"{abs_steamcmd_path}" +{login_cmd}
'''
                
                script_path = Path("./configs/steamcmd_session.sh")
                script_path.parent.mkdir(exist_ok=True)
                with open(script_path, 'w') as f:
                    f.write(script_content)
                os.chmod(script_path, 0o755)
                
                # Try to open in new terminal
                terminals = ['gnome-terminal', 'konsole', 'xterm']
                for term in terminals:
                    try:
                        if term == 'gnome-terminal':
                            subprocess.Popen([term, '--', str(script_path)])
                        else:
                            subprocess.Popen([term, '-e', str(script_path)])
                        break
                    except:
                        pass
                
                helper.steamcmd_terminal = True
                log_message("SteamCMDコンソールが開きました。手動でログインしてください。")
                log_message("ログインに成功すると、コンソールはアップロード用に開いたままになります。")
                
                helper.is_logged_in = False
                login_status.value = "Steamコンソールが開きました - ログインを待っています..."
                login_status.color = ft.Colors.ORANGE
                enable_controls(False)
                
                login_button.disabled = True
                
                # For Linux, we need manual confirmation of login
                # Don't start console monitoring until confirmed
                
                # Start a thread to monitor for successful login
                def monitor_login_status():
                    import time
                    time.sleep(3)  # Wait a bit for login to start
                    
                    # Check for rate limit error
                    rate_limit_detected = False
                    for i in range(10):  # Check for 10 seconds
                        try:
                            # Check if Terminal window contains rate limit error
                            check_script = '''
                            tell application "Terminal"
                                set rateLimit to false
                                try
                                    repeat with w in windows
                                        if (contents of selected tab of w) contains "Rate Limit Exceeded" then
                                            set rateLimit to true
                                            exit repeat
                                        end if
                                    end repeat
                                end try
                                return rateLimit
                            end tell
                            '''
                            result = subprocess.run(
                                ['osascript', '-e', check_script],
                                capture_output=True, text=True
                            )
                            if result.stdout.strip() == "true":
                                rate_limit_detected = True
                                break
                        except:
                            pass
                        time.sleep(1)
                    
                    if rate_limit_detected:
                        # Handle rate limit error
                        helper.is_logged_in = False
                        helper.steamcmd_terminal = False
                        login_status.value = "ログイン失敗 - レート制限"
                        login_status.color = ft.Colors.RED
                        login_button.disabled = False
                        log_message("Login failed due to rate limit. Please wait 5-10 minutes.")
                        show_error_dialog("Rate limit exceeded! Please wait 5-10 minutes before trying again.")
                    elif helper.steamcmd_terminal:
                        # Don't assume success - keep monitoring
                        # User needs to actually complete login
                        pass
                    
                    page.update()
                
                threading.Thread(target=monitor_login_status, daemon=True).start()
                
                page.update()
                return
        
        except Exception as ex:
            log_message(f"Error during login: {str(ex)}")
            # Reset state on error
            helper.steamcmd_terminal = False
            login_button.disabled = False
            progress_bar.visible = False
            page.update()
    
    # SteamCMD selection functions removed - now handled by ContentBuilder path
    
    def select_build_output_folder(e):
        folder_picker = ft.FilePicker(
            on_result=lambda e: on_build_output_selected(e)
        )
        page.overlay.append(folder_picker)
        page.update()
        folder_picker.get_directory_path(
            dialog_title="ビルド出力フォルダを選択"
        )
    
    def on_build_output_selected(e: ft.FilePickerResultEvent):
        if e.path:
            helper.settings["build_output_path"] = e.path
            build_output_path_text.value = e.path
            helper.save_settings()
            log_message(f"ビルド出力パスを設定しました: {e.path}")
            page.update()
    
    def reset_build_output_folder(e):
        # Remove the build output path setting
        if "build_output_path" in helper.settings:
            del helper.settings["build_output_path"]
            helper.save_settings()
        build_output_path_text.value = "未設定"
        log_message("ビルド出力パスをリセットしました")
        page.update()
    
    def show_system_settings_dialog():
        def close_settings_dialog(dlg):
            dlg.open = False
            page.update()
        
        # ContentBuilder path text
        content_builder_path_text = ft.Text(
            value=helper.settings.get("content_builder_path", "未設定"),
            size=12
        )
        
        def select_content_builder_folder(e):
            def on_folder_selected(e: ft.FilePickerResultEvent):
                if e.path:
                    helper.settings["content_builder_path"] = e.path
                    helper.save_settings()
                    content_builder_path_text.value = e.path
                    
                    # Auto-detect SteamCMD based on OS
                    steamcmd_path = None
                    if platform.system() == "Darwin":  # macOS
                        steamcmd_path = os.path.join(e.path, "builder_osx", "steamcmd.sh")
                    elif platform.system() == "Windows":
                        steamcmd_path = os.path.join(e.path, "builder", "steamcmd.exe")
                    else:  # Linux
                        steamcmd_path = os.path.join(e.path, "builder_linux", "steamcmd.sh")
                    
                    if steamcmd_path and os.path.exists(steamcmd_path):
                        helper.settings["steamcmd_path"] = steamcmd_path
                        helper.save_settings()
                        steamcmd_path_text.value = steamcmd_path
                        log_message(f"SteamCMDが自動検出されました: {steamcmd_path}")
                    else:
                        log_message(f"警告: SteamCMDが見つかりません: {steamcmd_path}")
                    
                    # Re-check paths after update
                    check_content_builder_paths()
                    dlg.update()
                    page.update()
            
            folder_picker = ft.FilePicker(on_result=on_folder_selected)
            page.overlay.append(folder_picker)
            page.update()
            folder_picker.get_directory_path(dialog_title="ContentBuilderフォルダを選択")
        
        select_builder_button = ft.ElevatedButton(
            "フォルダを選択",
            on_click=select_content_builder_folder
        )
            
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("基本設定"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("ContentBuilderフォルダ", size=16, weight=ft.FontWeight.W_500),
                    ft.Text("Steam SDKのtools/ContentBuilderフォルダを指定してください", size=11, color=ft.Colors.GREY),
                    ft.Row([
                        ft.Container(
                            content=content_builder_path_text,
                            expand=True,
                            padding=ft.padding.symmetric(vertical=5)
                        ),
                        select_builder_button
                    ]),
                    ft.Text("SteamCMDパス (自動検出)", size=14, weight=ft.FontWeight.W_500),
                    ft.Container(
                        content=steamcmd_path_text,
                        padding=ft.padding.symmetric(vertical=5)
                    ),
                    ft.Divider(),
                    ft.Text("ビルド出力フォルダ", size=16, weight=ft.FontWeight.W_500),
                    ft.Text("未設定時は ./log フォルダにログが保存されます", size=11, color=ft.Colors.GREY),
                    ft.Row([
                        ft.Container(
                            content=build_output_path_text,
                            expand=True,
                            padding=ft.padding.symmetric(vertical=5)
                        ),
                        reset_output_button,
                        manual_select_output_button
                    ])
                ]),
                width=600,
                height=350
            ),
            actions=[
                ft.TextButton("閉じる", on_click=lambda e: close_settings_dialog(dlg))
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        page.overlay.append(dlg)
        dlg.open = True
        page.update()
    
    upload_in_progress = False
    
    def show_success_dialog(message):
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("成功"),
            content=ft.Text(message),
            actions=[
                ft.TextButton("OK", on_click=lambda e: close_dialog(dlg))
            ]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()
    def run_upload(e):
        nonlocal upload_in_progress
        
        # Prevent multiple clicks
        if upload_in_progress or upload_button.disabled:
            log_message("アップロードが既に実行中です...")
            return
        
        upload_in_progress = True
            
        if not helper.is_logged_in:
            log_message("エラー: まずSteamにログインしてください")
            show_error_dialog("まずログインボタンを使用してSteamにログインしてください")
            upload_in_progress = False
            return
        
        # Additional check - verify Steam console is actually logged in
        if not helper.steamcmd_terminal:
            log_message("エラー: Steamコンソールが開いていません")
            show_error_dialog("Steamコンソールを開いてログインしてください")
            upload_in_progress = False
            return
        
        # Validate inputs
        if not app_id_field.value or not depot_id_field.value:
            log_message("エラー: App IDとDepot IDを入力してください")
            show_error_dialog("App IDとDepot IDの両方を入力してください")
            upload_in_progress = False
            return
        
        if not content_path_field.value:
            log_message("エラー: コンテンツパスを指定してください")
            show_error_dialog("設定でコンテンツパスを指定してください")
            upload_in_progress = False
            return
        
        # Save general settings (not config-specific)
        helper.save_settings()
        
        upload_button.disabled = True
        page.update()
        
        try:
            log_message("Steamアップロードを開始しています...")
            log_message(f"App ID: {app_id_field.value}")
            log_message(f"Depot ID: {depot_id_field.value}")
            log_message(f"ブランチ: {branch_field.value or '未指定（手動承認が必要）'}")
            log_message(f"コンテンツ: {content_path_field.value}")
            
            # Create app build config with description
            description = upload_description_field.value or f"Morn Steam アップロードヘルパーでアップロード - {time.strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Use custom build output path if set, otherwise use default log folder
            if helper.settings.get("build_output_path"):
                build_output = helper.settings["build_output_path"]
                log_message(f"カスタムビルド出力パスを使用: {build_output}")
            else:
                log_folder = Path.cwd() / "log"
                log_folder.mkdir(exist_ok=True)
                build_output = str(log_folder)
                log_message(f"デフォルトビルド出力パスを使用: {build_output}")
            
            # Get the content path and its parent directory
            content_abs_path = os.path.abspath(content_path_field.value)
            content_parent = os.path.dirname(content_abs_path)
            content_folder_name = os.path.basename(content_abs_path)
            
            # Create depot file first
            depot_content = f'''"DepotBuild"
{{
    "DepotID" "{depot_id_field.value}"
    
    "FileMapping"
    {{
        "LocalPath" "*"
        "DepotPath" "."
        "Recursive" "1"
    }}
}}
'''
            
            depot_filename = f"depot_{depot_id_field.value}.vdf"
            depot_path = helper.vdf_dir / depot_filename
            with open(depot_path, 'w') as f:
                f.write(depot_content)
            
            log_message(f"depot設定を作成しました: {depot_path}")
            
            # Create relative path from VDF location to content
            log_message(f"コンテンツ絶対パス: {content_abs_path}")
            log_message(f"VDFディレクトリ: {helper.vdf_dir}")
            
            # Calculate relative path from vdf directory to content
            content_rel_path = os.path.relpath(content_abs_path, helper.vdf_dir)
            log_message(f"相対パス（生）: {content_rel_path}")
            
            # Convert forward slashes to backslashes for Steam
            content_rel_path = content_rel_path.replace('/', '\\')
            
            # Add trailing backslash if not present
            if not content_rel_path.endswith('\\'):
                content_rel_path += '\\'
                
            log_message(f"ContentRoot: {content_rel_path}")
                
            vdf_content = f'''"AppBuild"
{{
    "AppID" "{app_id_field.value}"
    "Desc" "{description}"
    "Preview" "0"
    "Local" ""'''
            
            # Only add setlive if branch is specified
            if branch_field.value:
                vdf_content += f'''
    "SetLive" "{branch_field.value}"'''
            else:
                vdf_content += f'''
    "SetLive" ""'''
            
            # Convert build output path to backslashes if specified
            if build_output:
                build_output_fixed = build_output.replace('/', '\\')
                build_output_line = f'    "BuildOutput" "{build_output_fixed}"'
            else:
                build_output_line = '    "BuildOutput" ""'
            
            vdf_content += f'''
    "ContentRoot" "{content_rel_path}"
{build_output_line}
    "Depots"
    {{
        "{depot_id_field.value}" "{depot_filename}"
    }}
}}
'''
            
            # Save VDF config in vdf directory
            config_path = helper.vdf_dir / f"app_{app_id_field.value}.vdf"
            with open(config_path, 'w') as f:
                f.write(vdf_content)
            
            log_message(f"ビルド設定を作成しました: {config_path}")
            
            log_message("SteamCMDコンテンツビルダーを実行しています...")
            log_message("Steamコンソールウィンドウを確認してください")
            
            # Run the command in the open SteamCMD console
            # Use absolute path for the config file
            abs_config_path = os.path.abspath(config_path)
            upload_command = f'run_app_build "{abs_config_path}"'
            
            if platform.system() == "Darwin":  # macOS
                # Send command directly to Terminal
                try:
                    # Use AppleScript to type the command character by character
                    # First, escape special characters for AppleScript
                    escaped_command = upload_command.replace('\\', '\\\\').replace('"', '\\"')
                    
                    type_script = f'''
tell application "Terminal"
    activate
    -- Find the window with SteamCMD
    set found to false
    repeat with w in windows
        try
            set tabContent to contents of selected tab of w
            if tabContent contains "Steam>" then
                set index of w to 1
                set found to true
                exit repeat
            end if
        end try
    end repeat
    
    if not found then
        return "No Steam console found"
    end if
end tell

delay 0.5

tell application "System Events"
    tell process "Terminal"
        -- Type the command
        keystroke "{escaped_command}"
        delay 0.5
        -- Press Enter
        keystroke return
    end tell
end tell

return "OK"
'''
                    
                    result = subprocess.run(['osascript', '-e', type_script], capture_output=True, text=True)
                    
                    if result.returncode == 0 and "OK" in result.stdout:
                        log_message(f"アップロードコマンドを実行しました: {upload_command}")
                        log_message("Steamコンソールでアップロードを開始しました。進行状況はコンソールで確認してください。")
                    elif "No Steam console found" in result.stdout:
                        log_message("エラー: Steamコンソールウィンドウが見つかりません")
                        log_message("SteamCMDコンソールが開いてログインしていることを確認してください")
                    else:
                        log_message(f"コマンド実行エラー: {result.stderr}")
                        # As a fallback, copy to clipboard
                        subprocess.run(['pbcopy'], input=upload_command.encode())
                        log_message(f"コマンドをクリップボードにコピーしました: {upload_command}")
                        
                except Exception as e:
                    log_message(f"エラー: {e}")
                    # Fallback: copy to clipboard
                    subprocess.run(['pbcopy'], input=upload_command.encode())
                    log_message(f"Command copied to clipboard: {upload_command}")
                    
            elif platform.system() == "Windows":
                # For Windows, copy to clipboard
                try:
                    subprocess.run(['clip'], input=upload_command.encode(), check=True, shell=True)
                    log_message("=" * 50)
                    log_message("アップロードコマンドがクリップボードにコピーされました！")
                    log_message("=" * 50)
                    log_message(f"コマンド: {upload_command}")
                    log_message("")
                    log_message("1. SteamCMDコンソールウィンドウをクリック")
                    log_message("2. Ctrl+Vでコマンドをペースト")
                    log_message("3. Enterキーでアップロードを開始")
                    log_message("=" * 50)
                except:
                    log_message(f"SteamCMDコンソールで実行してください: {upload_command}")
                    
            else:  # Linux
                # For Linux, also fallback to manual
                log_message(f"Please run in SteamCMD console: {upload_command}")
            
        except Exception as ex:
            log_message(f"アップロード中にエラー: {str(ex)}")
        finally:
            upload_button.disabled = False
            upload_in_progress = False
            page.update()
    
    # Build scrollable UI
    content = ft.Column([
        ft.Container(
            content=ft.Row([
                ft.Text("Morn Steam アップロードヘルパー", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                login_status,
                ft.ElevatedButton(
                    "基本設定",
                    icon=ft.Icons.SETTINGS,
                    on_click=lambda e: show_system_settings_dialog()
                )
            ]),
            padding=20
        ),
        
        # 1. Steam Login (First)
        ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("1. Steam ログイン", size=18, weight=ft.FontWeight.W_500),
                        login_error_text,
                        ft.Row([username_field, password_field]),
                        ft.Row([
                            ft.Column([
                                steam_guard_field,
                                ft.Text(
                                    "※ 入力時は自動認証、未入力時はモバイルアプリからの承認が必要です",
                                    size=11,
                                    color=ft.Colors.GREY
                                )
                            ], expand=True),
                            ft.Column([
                                ft.Row([
                                    login_button,
                                    confirm_login_button,
                                ], spacing=5),
                                ft.Row([
                                    ft.Icon(ft.Icons.WARNING, color=ft.Colors.AMBER, size=16),
                                    ft.Text("コンソールは閉じないで！", 
                                           size=12, color=ft.Colors.AMBER, weight=ft.FontWeight.BOLD)
                                ])
                            ], horizontal_alignment=ft.CrossAxisAlignment.END)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ]),
                    padding=15
                )
            ),
            padding=ft.padding.symmetric(horizontal=15, vertical=0)
        ),
        
        # 2. Upload Configuration
        ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("2. アップロード設定", size=18, weight=ft.FontWeight.W_500),
                            ft.Container(expand=True),
                            new_config_button,
                            edit_config_button,
                            delete_config_button
                        ]),
                        ft.Row([
                            config_dropdown,
                            config_build_page_btn,
                            config_depot_page_btn
                        ], spacing=5),
                        ft.Divider(),
                        ft.Row([
                            ft.Text("App ID:", size=14),
                            app_id_field,
                            ft.Text("Depot ID:", size=14),
                            depot_id_field,
                            ft.Text("ブランチ:", size=14),
                            branch_field,
                        ], spacing=10),
                        ft.Row([
                            ft.Text("説明:", size=14),
                            upload_description_field,
                        ], spacing=10),
                        ft.Row([
                            ft.Text("コンテンツパス:", size=14),
                            content_path_field,
                            ft.IconButton(
                                icon=ft.Icons.FOLDER_OPEN,
                                tooltip="フォルダを開く",
                                on_click=lambda e: open_content_folder()
                            )
                        ], spacing=10),
                    ]),
                    padding=15
                )
            ),
            padding=ft.padding.symmetric(horizontal=15, vertical=0)
        ),
        
        # 3. Upload Action
        ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("3. アップロード", size=18, weight=ft.FontWeight.W_500),
                        ft.Row([
                            ft.Container(
                                content=login_status_text,
                                expand=True,
                                alignment=ft.alignment.center_left
                            ),
                            ft.Container(
                                content=config_status_text,
                                expand=True,
                                alignment=ft.alignment.center_left
                            )
                        ]),
                        ft.Container(height=10),
                        ft.Row([
                            upload_button,
                        ], alignment=ft.MainAxisAlignment.CENTER),
                    ]),
                    padding=15
                )
            ),
            padding=ft.padding.symmetric(horizontal=15, vertical=0)
        ),
        
        
    ])
    
    # Add content to page
    page.add(content)
    
    # Initial log message
    log_message("Morn Steam アップロードヘルパーへようこそ")
    log_message("ツールを使用するには、まずSteamにログインしてください")
    
    # Initially disable upload controls until logged in
    enable_controls(False)

if __name__ == "__main__":
    ft.app(target=main)