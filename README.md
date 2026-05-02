# WhisperFlow 🎙️

An open-source AI voice dictation app for Windows, inspired by Wispr Flow. 

WhisperFlow lives in your system tray. Just press and hold `Ctrl+Shift+Space`, speak naturally, and the transcribed text will be magically typed into whatever application you're currently using.

## Features

- **Global Hotkey:** Works anywhere, in any application.
- **Dual Engines:** Choose between local, privacy-first transcription (`faster-whisper`) or ultra-fast cloud transcription (Groq API).
- **Auto-Cleaning:** Automatically removes filler words ("um", "uh") and adds punctuation.
- **Floating Overlay:** Sleek, dark-mode visual feedback while you speak.
- **Lightweight:** Pure Python implementation, no heavy Electron framework.

## Installation for Development

1. **Prerequisites:** 
   - Python 3.10+
   - A working microphone

2. **Clone and setup:**
   ```bash
   git clone <repo_url>
   cd whisper
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *Note for Windows users:* If you have trouble installing `PyAudio`, you may need to install it via pipwin: `pip install pipwin && pipwin install pyaudio`.

4. **Run the app:**
   ```bash
   python -m src.main
   ```

## Usage

1. Launch the app. You'll see the WhisperFlow icon in your system tray.
2. Click inside any text field (Notepad, browser, IDE, etc.).
3. Press `Ctrl+Shift+Space` (default toggle mode: press once to start, speak, press again to stop).
4. Watch the text appear!

You can right-click the tray icon to open Settings and configure the hotkey, activation mode, transcription engine, and microphone.

## Building the Executable

To package WhisperFlow into a standalone `.exe`:

```bash
pip install pyinstaller
pyinstaller whisperflow.spec
```

The resulting executable will be in the `dist/` directory.
