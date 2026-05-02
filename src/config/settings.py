"""
WhisperFlow — Settings Manager
Handles persistent application configuration stored as JSON in %APPDATA%.
"""

import json
import os
from pathlib import Path
from typing import Any, Optional

from src.utils.logger import get_logger

logger = get_logger("Settings")


# Default settings
DEFAULTS = {
    "hotkey": "ctrl+shift+space",
    "activation_mode": "hold",         # "hold" or "toggle"
    "engine": "local",                  # "local" or "groq"
    "model": "tiny",                    # tiny, base, small, medium, large-v3
    "language": "auto",                 # "auto" for auto-detect, or ISO code
    "groq_api_key": "",
    "microphone_index": None,           # None = system default
    "auto_start": False,                # Start with Windows
    "sound_enabled": True,              # Play start/stop sounds
    "filler_removal": True,             # Remove "um", "uh", etc.
    "auto_punctuation": True,           # Auto-add punctuation
    "overlay_enabled": True,            # Show floating overlay
    "overlay_position": "bottom_center",
    "theme": "dark",
    "log_level": "INFO",
}


def get_app_data_dir() -> Path:
    """Returns the WhisperFlow application data directory."""
    app_data = os.environ.get("APPDATA", os.path.expanduser("~"))
    path = Path(app_data) / "WhisperFlow"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_models_dir() -> Path:
    """Returns the directory where Whisper models are cached."""
    path = get_app_data_dir() / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_logs_dir() -> Path:
    """Returns the directory for log files."""
    path = get_app_data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


class Settings:
    """Manages application settings with JSON persistence."""

    def __init__(self):
        self._file_path = get_app_data_dir() / "settings.json"
        self._data: dict = {}
        self.load()

    def load(self):
        """Load settings from disk, merging with defaults."""
        self._data = dict(DEFAULTS)
        if self._file_path.exists():
            try:
                with open(self._file_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self._data.update(saved)
            except (json.JSONDecodeError, IOError):
                pass  # Corrupted file — use defaults

    def save(self):
        """Persist current settings to disk."""
        try:
            with open(self._file_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"[Settings] Failed to save: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any):
        """Set a setting value and save."""
        self._data[key] = value
        self.save()

    def reset(self):
        """Reset all settings to defaults."""
        self._data = dict(DEFAULTS)
        self.save()

    @property
    def hotkey(self) -> str:
        return self._data.get("hotkey", DEFAULTS["hotkey"])

    @property
    def activation_mode(self) -> str:
        return self._data.get("activation_mode", DEFAULTS["activation_mode"])

    @property
    def engine(self) -> str:
        return self._data.get("engine", DEFAULTS["engine"])

    @property
    def model(self) -> str:
        return self._data.get("model", DEFAULTS["model"])

    @property
    def language(self) -> str:
        return self._data.get("language", DEFAULTS["language"])

    @property
    def groq_api_key(self) -> str:
        return self._data.get("groq_api_key", "")

    @property
    def microphone_index(self) -> Optional[int]:
        return self._data.get("microphone_index")

    @property
    def sound_enabled(self) -> bool:
        return self._data.get("sound_enabled", True)

    @property
    def filler_removal(self) -> bool:
        return self._data.get("filler_removal", True)

    @property
    def overlay_enabled(self) -> bool:
        return self._data.get("overlay_enabled", True)

    @property
    def auto_punctuation(self) -> bool:
        return self._data.get("auto_punctuation", True)

    @property
    def auto_start(self) -> bool:
        return self._data.get("auto_start", False)

    def set_auto_start(self, enabled: bool):
        """Enable or disable auto-start with Windows using Registry."""
        self.set("auto_start", enabled)
        
        import winreg
        import sys
        
        app_name = "WhisperFlow"
        # Get the path to the executable or the python script
        if getattr(sys, 'frozen', False):
            # Running as bundled exe
            app_path = f'"{sys.executable}"'
        else:
            # Running as script
            app_path = f'"{sys.executable}" -m src.main'
            
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            if enabled:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
            logger.info(f"Auto-start {'enabled' if enabled else 'disabled'}")
        except Exception as e:
            logger.error(f"Failed to update auto-start registry key: {e}")

    def to_dict(self) -> dict:
        """Return a copy of all settings."""
        return dict(self._data)
