"""
WhisperFlow — Main Application Orchestrator
Coordinates hotkeys, audio recording, transcription, and UI.
"""

import threading
import time
import queue
from typing import Optional

from src.config.settings import Settings
from src.core.audio_recorder import AudioRecorder
from src.core.transcriber import TranscriberFactory, BaseTranscriber
from src.core.text_cleaner import TextCleaner
from src.core.text_injector import inject_text_async
from src.hotkey.hotkey_manager import HotkeyManager
from src.core.supabase_client import SupabaseManager
from src.ui.login_window import LoginWindow
from src.ui.tray_icon import TrayIcon
from src.ui.overlay import DictationOverlay
from src.ui.settings_window import SettingsWindow
from src.utils.logger import get_logger

logger = get_logger("App")


class App:
    """Main application orchestrator."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.is_running = False
        self._command_queue = queue.Queue()

        # Backend components
        self.supabase = SupabaseManager()
        self.login_window = None

        # Core components
        self.recorder = AudioRecorder(device_index=self.settings.microphone_index)
        self.transcriber: Optional[BaseTranscriber] = None
        self.cleaner = TextCleaner(
            remove_fillers=self.settings.filler_removal,
            auto_punctuation=self.settings.auto_punctuation,
        )

        # UI components
        self.overlay = DictationOverlay()
        self.tray = TrayIcon(
            on_settings=self._on_tray_settings,
            on_pause=self.toggle_pause,
            on_logout=self._on_tray_logout,
            on_quit=self._on_tray_quit,
        )

        self.settings_window = SettingsWindow(
            settings=self.settings, 
            on_save=self._on_settings_saved
        )
        
        # Hotkey manager
        self.hotkey_manager = HotkeyManager(
            hotkey=self.settings.hotkey,
            mode=self.settings.activation_mode,
            on_activate=self.start_dictation,
            on_deactivate=self.stop_dictation,
        )

    def start(self):
        """Start all background components."""
        # 1. Start UI foundations
        self.tray.start()
        self.overlay.start()

        # 2. Check Auth
        if not self.supabase.is_logged_in():
            logger.info("User not logged in, showing login window")
            self._command_queue.put("show_login")
        else:
            self._on_login_success()

        # Main thread loop for GUI commands (must be in main thread for Tkinter)
        try:
            while True:
                try:
                    # Check for commands from other threads (timeout to keep CPU low)
                    command = self._command_queue.get(timeout=0.1)
                    if command == "show_settings":
                        logger.info("Opening settings window...")
                        self.settings_window.show()
                    elif command == "show_login":
                        if not self.login_window:
                            self.login_window = LoginWindow(on_success_callback=self._on_login_success)
                        self.login_window.deiconify()
                    elif command == "quit":
                        break
                except queue.Empty:
                    pass
                time.sleep(0.01)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def _on_login_success(self):
        """Callback when user is authenticated."""
        logger.info("Authentication successful, enabling hotkeys")
        self.is_running = True
        
        # Start hotkey listener only after login
        self.hotkey_manager.start()
        
        # Initialize transcriber
        self._init_transcriber()
        
        logger.info("[SUCCESS] WhisperFlow is ready!")

    def _on_tray_settings(self):
        """Callback from tray icon to show settings."""
        self._command_queue.put("show_settings")

    def _on_tray_logout(self):
        """Callback from tray icon to logout."""
        logger.info("Logging out...")
        self.supabase.logout()
        self.is_running = False
        self.hotkey_manager.pause()
        self._command_queue.put("show_login")

    def _on_tray_quit(self):
        """Callback from tray icon to quit."""
        self._command_queue.put("quit")

    def _init_transcriber(self):
        """Initialize the selected transcription engine."""
        engine_type = self.settings.engine
        logger.info(f"Initializing transcriber: {engine_type}")
        
        try:
            self.transcriber = TranscriberFactory.create(
                engine_type,
                model=self.settings.model,
                api_key=self.settings.groq_api_key,
            )
            logger.info(f"Transcriber ready: {self.transcriber.get_name()}")
        except Exception as e:
            logger.error(f"Failed to initialize transcriber: {e}")
            self.overlay.show("error", "Engine Init Failed")

    def start_dictation(self):
        """Handle hotkey activation: start recording."""
        if not self.is_running or self.recorder.is_recording:
            return

        logger.info("▶️ Starting dictation")
        self.tray.set_state("recording")
        
        if self.settings.overlay_enabled:
            self.overlay.show("listening")

        self.recorder.start()

    def stop_dictation(self):
        """Handle hotkey deactivation: stop recording and process."""
        if not self.recorder.is_recording:
            return

        logger.info("⏹️ Stopping dictation")
        
        if self.settings.overlay_enabled:
            self.overlay.show("processing")
            
        self.tray.set_state("processing")

        # Stop recording and get audio data
        audio_data = self.recorder.stop()

        if audio_data is None or len(audio_data) < 8000:  # < 0.5s of audio
            logger.warning("Audio too short or empty, ignoring.")
            self._reset_ui()
            return

        # Process transcription in a background thread
        threading.Thread(
            target=self._process_audio, 
            args=(audio_data,), 
            daemon=True
        ).start()

    def _process_audio(self, audio_data):
        """Process the captured audio: transcribe, clean, inject."""
        if not self.transcriber:
            logger.error("No transcriber available")
            self.overlay.show("error", "No Engine")
            self._reset_ui(delay=2.0)
            return

        try:
            # 1. Transcribe
            logger.info("Transcribing audio...")
            raw_text = self.transcriber.transcribe(
                audio_data, language=self.settings.language
            )

            if not raw_text:
                logger.info("No speech detected.")
                self._reset_ui()
                return

            # 2. Clean
            clean_text = self.cleaner.clean(raw_text)

            # 3. Save to Cloud
            self.supabase.save_transcription(
                text=clean_text,
                language=self.settings.language,
                duration=len(audio_data) / 16000, # Assuming 16kHz
                engine=self.settings.engine
            )

            # 4. Success UI feedback
            if self.settings.overlay_enabled:
                self.overlay.show("success")
            
            # Small delay to let overlay finish any transitions and focus to return
            time.sleep(0.2)
            if self.settings.overlay_enabled:
                self.overlay.hide()

            # 4. Inject
            logger.info(f"Injecting text: '{clean_text}'")
            inject_text_async(clean_text + " ")  # Add trailing space for fluency
                
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            if self.settings.overlay_enabled:
                self.overlay.show("error")
        finally:
            self._reset_ui(delay=1.5)

    def _reset_ui(self, delay=0.0):
        """Reset UI to idle state, optionally after a delay."""
        def do_reset():
            self.tray.set_state("idle")
            # Overlay auto-hides on success/error, but force hide if needed
            if not self.settings.overlay_enabled:
                self.overlay.hide()
                
        if delay > 0:
            threading.Timer(delay, do_reset).start()
        else:
            do_reset()

    def show_settings(self):
        """Open the settings window."""
        # Pause hotkey while settings are open to avoid accidental triggers
        self.hotkey_manager.pause()
        
        self.settings_window.show()
        
        self.hotkey_manager.resume()

    def _on_settings_saved(self):
        """Apply new settings."""
        # Stop recording if active during settings change
        if self.recorder.is_recording:
            self.stop_dictation()
            
        # Re-init transcriber if engine or model changed
        self._init_transcriber()
        
        # Update hotkey manager
        self.hotkey_manager.update_hotkey(
            self.settings.hotkey, 
            mode=self.settings.activation_mode
        )
        
        # Update cleaner
        self.cleaner.remove_fillers = self.settings.filler_removal
        self.cleaner.auto_punctuation = self.settings.auto_punctuation
        
        # Update recorder device
        self.recorder = AudioRecorder(device_index=self.settings.microphone_index)

    def toggle_pause(self, is_paused: bool):
        """Toggle hotkey pause state."""
        if is_paused:
            self.hotkey_manager.pause()
            self.tray.set_state("idle")  # Keep it simple for now
        else:
            self.hotkey_manager.resume()

    def stop(self):
        """Clean shutdown of the application."""
        logger.info("Shutting down WhisperFlow...")
        self.is_running = False
        
        if self.recorder.is_recording:
            self.recorder.stop()
            
        self.hotkey_manager.stop()
        self.tray.stop()
        self.overlay.stop()
