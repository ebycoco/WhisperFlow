# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

WhisperFlow is a Windows system-tray voice dictation app (Python, no Electron). It listens for a global
hotkey, records audio, transcribes it (local `faster-whisper` or cloud Groq API), cleans the text, and
injects it into whatever field the user is focused on via clipboard + Ctrl+V.

## Commands

```bash
# Setup
python -m venv venv
venv\Scripts\activate          # PowerShell: venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run from source
python -m src.main

# Build the standalone .exe (PyInstaller)
pip install pyinstaller
pyinstaller whisperflow.spec
# output: dist/WhisperFlow.exe
```

There is no test suite, linter, or formatter configured in this repo — don't assume `pytest`/`ruff`/etc.
exist. CI (`.github/workflows/build.yml`) builds the exe on a `v*` tag push or a manual
`workflow_dispatch`, and uploads it as a GitHub Release asset (via `--onefile --windowed`, not the
`.spec` file used locally).

On Windows, if `PyAudio`/`sounddevice` install fails, `pip install pipwin && pipwin install pyaudio` per
the README.

## Architecture

**Entry point → orchestrator.** `src/main.py` sets up logging/multiprocessing then hands off to
`src/app.py::App`, which owns every subsystem and wires callbacks between them. There is no event bus —
components talk to each other only through constructor-injected callbacks owned by `App`. When adding a
feature, it almost always means adding a callback wire-up in `App.__init__`/`App.start`, not a new global.

**Two separate UI threading models — don't conflate them.** `App.start()` runs a `while True` polling
loop (`_command_queue`, 0.1s timeout) on the main thread. The login window and settings window
(`customtkinter`) are created transiently *on this main thread* only, in response to string commands
(`"show_settings"`, `"show_login"`, `"quit"`) that background threads (hotkey listener, audio callback,
transcription) push onto `_command_queue` — they never touch these two windows directly. The floating
overlay (`DictationOverlay`) is different: it owns its own persistent `tk.Tk()` root running its own
`mainloop()` on a *dedicated background thread* (started in `overlay.start()`), and background threads
call `self.overlay.show(...)`/`.hide()` on it **directly** (see `App.start_dictation`/`stop_dictation`/
`_process_audio`) — cross-thread safety there comes from `overlay.py` marshaling internally via
`self._root.after(0, ...)`, not from `_command_queue`. When adding new UI: a window that must share state
with login/settings belongs on the main thread via `_command_queue`; a self-contained always-on-top
display like the overlay can own its own thread instead, following `DictationOverlay`'s pattern.

**Dictation pipeline** (`App.start_dictation` → `stop_dictation` → `_process_audio`):
1. Hotkey fires (`HotkeyManager`, hold or toggle mode) → `AudioRecorder.start()` streams mic audio via
   `sounddevice` into an int16 numpy buffer on a background thread.
2. Hotkey releases/toggles off → `AudioRecorder.stop()` returns the buffer; audio under 0.5s is dropped.
3. `_process_audio` runs in its own thread: transcribe → `TextCleaner.clean()` (strips filler words,
   fixes spacing/punctuation, capitalizes) → save to Supabase → show overlay success → `inject_text_async`
   (clipboard swap + simulated Ctrl+V via `pynput`, original clipboard restored after a delay).
4. UI state (tray icon, floating overlay) is updated at each stage and reset on a timed delay so
   transitions don't feel abrupt.

**Transcription engines are pluggable** via `BaseTranscriber` (`src/core/transcriber.py`) +
`TranscriberFactory.create(engine_type, ...)`. Two implementations:
- `WhisperEngine` (local, `faster-whisper`): lazy-loads the model on first use, auto-detects CUDA (falls
  back to CPU int8), model files cached under `%APPDATA%/WhisperFlow/models`.
- `GroqEngine` (cloud): converts the numpy buffer to WAV bytes and calls the Groq Whisper API; requires
  an API key from Settings.

Adding a third engine means implementing `BaseTranscriber` and registering it in
`TranscriberFactory.create`.

**Settings** (`src/config/settings.py`) persist as JSON at `%APPDATA%/WhisperFlow/settings.json`, merged
over a `DEFAULTS` dict so missing/new keys don't break old config files. Accessed via typed `@property`
getters on `Settings`, not raw dict access, from the rest of the app. `set_auto_start()` writes directly
to the Windows registry (`HKCU\...\Run`) — Windows-only, no cross-platform guard.

**Auth/cloud sync** (`src/core/supabase_client.py`) is a singleton (`__new__` override) wrapping the
Supabase Python client. The app requires login before the hotkey listener is started (see
`App._on_login_success`); every transcription is saved to a `transcriptions` table keyed by user id.
There's no local-only/offline mode — logout re-shows the login window and pauses the hotkey.

**Packaging note:** `whisperflow.spec` currently has empty `datas=[]`, so `assets/` (icons, sounds) is
not bundled into the onefile exe — `src/utils/resources.py::resource_path()` resolves paths against
`sys._MEIPASS` in frozen mode vs. the project root in dev mode, but the spec doesn't actually copy the
assets there. Keep this in mind if touching packaging or asset loading.
