"""
Steam Upload Helper class for managing Steam uploads.
"""

import json
import queue
from pathlib import Path
from constants import CONFIG_DIR, VDF_DIR


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