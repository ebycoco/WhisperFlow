# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for WhisperFlow.
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect data files for faster-whisper and groq
datas = []
datas += collect_data_files('faster_whisper')
datas += collect_data_files('ctranslate2')
datas += collect_data_files('customtkinter')

# You should generate proper .ico files and place them in the assets folder
# For now, we assume they exist.
# datas += [('assets/*', 'assets')]

hiddenimports = []
hiddenimports += collect_submodules('pynput')
hiddenimports += collect_submodules('pystray')
hiddenimports += collect_submodules('pyperclip')
hiddenimports += ['PIL._tkinter_finder']

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='WhisperFlow',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False to hide the console window!
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/icon.ico', # Uncomment when you have the icon
)
