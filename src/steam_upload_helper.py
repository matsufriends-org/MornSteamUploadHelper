"""
Steam Upload Helper class for managing Steam uploads.
"""

import json
import queue
from pathlib import Path
from .constants import CONFIG_DIR, VDF_DIR


class SteamUploadHelper:
    """
    Main helper class for managing Steam uploads.
    
    This class handles:
    - Configuration storage and retrieval
    - SteamCMD process management
    - Upload configuration management
    """
    
    def __init__(self):
        """Initialize the Steam Upload Helper with default settings."""
        # Configuration directories
        self.configs_dir = Path(CONFIG_DIR)
        self.vdf_dir = Path(VDF_DIR)
        
        # Configuration files
        self.settings_file = self.configs_dir / "settings.json"
        self.upload_configs_file = self.configs_dir / "upload_configs.json"
        
        # Load saved configurations
        self.settings = self.load_settings()
        self.upload_configs = self.load_upload_configs()
        
        # Process management
        self.steamcmd_process = None
        self.steamcmd_cmd_process_id = None  # Windows: cmd.exe process ID
        self.is_logged_in = False
        self.output_queue = queue.Queue()
        self.console_monitor_thread = None
        self.steamcmd_terminal = False
        
        # Create necessary directories
        self.vdf_dir.mkdir(exist_ok=True)
        
    def load_settings(self):
        """Load user settings from JSON file."""
        if self.settings_file.exists():
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_settings(self):
        """Save user settings to JSON file."""
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=2, ensure_ascii=False)
    
    def load_upload_configs(self):
        """Load upload configurations from JSON file."""
        if self.upload_configs_file.exists():
            with open(self.upload_configs_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_upload_configs(self):
        """Save upload configurations to JSON file."""
        self.upload_configs_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.upload_configs_file, 'w', encoding='utf-8') as f:
            json.dump(self.upload_configs, f, indent=2, ensure_ascii=False)
    
    def save_upload_config(self, name, config):
        """Save a single upload configuration."""
        self.upload_configs[name] = config
        self.save_upload_configs()
    
    def delete_upload_config(self, name):
        """Delete an upload configuration."""
        if name in self.upload_configs:
            del self.upload_configs[name]
            self.save_upload_configs()
    
    def create_vdf_file(self, config_name, config):
        """Create VDF files for Steam upload."""
        import os
        import time
        
        # Get required values
        app_id = config.get("app_id", "")
        depot_id = config.get("depot_id", "")
        branch = config.get("branch", "")
        description = config.get("description", f"Morn Steam アップロードヘルパーでアップロード - {time.strftime('%Y-%m-%d %H:%M:%S')}")
        content_path = config.get("content_path", "")
        
        if not all([app_id, depot_id, content_path]):
            return None
        
        # Use custom build output path if set
        if self.settings.get("build_output_path"):
            build_output = self.settings["build_output_path"]
        else:
            log_folder = Path.cwd() / "log"
            log_folder.mkdir(exist_ok=True)
            build_output = str(log_folder)
        
        # Get the content path
        content_abs_path = os.path.abspath(content_path)
        
        # Create depot file first
        depot_content = f'''"DepotBuild"
{{
    "DepotID" "{depot_id}"
    
    "FileMapping"
    {{
        "LocalPath" "*"
        "DepotPath" "."
        "Recursive" "1"
    }}
}}
'''
        
        depot_filename = f"depot_{depot_id}.vdf"
        depot_path = self.vdf_dir / depot_filename
        with open(depot_path, 'w', encoding='utf-8') as f:
            f.write(depot_content)
        
        # Calculate relative path from vdf directory to content
        content_rel_path = os.path.relpath(content_abs_path, self.vdf_dir)
        
        # Convert forward slashes to backslashes for Steam
        content_rel_path = content_rel_path.replace('/', '\\')
        
        # Add trailing backslash if not present
        if not content_rel_path.endswith('\\'):
            content_rel_path += '\\'
        
        # Create app build VDF
        vdf_content = f'''"AppBuild"
{{
    "AppID" "{app_id}"
    "Desc" "{description}"
    "Preview" "0"
    "Local" ""'''
        
        # Only add setlive if branch is specified
        if branch:
            vdf_content += f'''
    "SetLive" "{branch}"'''
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
        "{depot_id}" "{depot_filename}"
    }}
}}
'''
        
        # Save VDF config in vdf directory
        config_path = self.vdf_dir / f"app_{app_id}.vdf"
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(vdf_content)
        
        return str(config_path)