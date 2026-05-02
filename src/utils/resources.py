"""
WhisperFlow — Resource Path Resolver
Handles path resolution for both development and PyInstaller-bundled environments.
"""

import os
import sys
from pathlib import Path


def resource_path(relative_path: str) -> Path:
    """
    Get absolute path to a resource file.
    Works both in development mode and when packaged with PyInstaller.

    In PyInstaller's --onefile mode, files are extracted to a temp dir
    accessible via sys._MEIPASS.
    """
    try:
        # PyInstaller stores extracted files in _MEIPASS
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        # Running in development mode — use project root
        base_path = Path(__file__).resolve().parent.parent.parent

    return base_path / relative_path


def get_asset_path(filename: str) -> Path:
    """Get path to a file in the assets directory."""
    return resource_path(f"assets/{filename}")


def get_sound_path(filename: str) -> Path:
    """Get path to a sound file."""
    return resource_path(f"assets/sounds/{filename}")
