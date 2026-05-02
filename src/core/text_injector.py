"""
WhisperFlow — Text Injector
Injects transcribed text into the active input field using clipboard + Ctrl+V.
"""

import time
import threading

import pyperclip
from pynput.keyboard import Controller, Key

from src.utils.logger import get_logger

logger = get_logger("TextInjector")

_keyboard = Controller()
_lock = threading.Lock()


def inject_text(text: str, restore_clipboard: bool = True):
    """
    Inject text into the currently focused input field.

    Uses clipboard + Ctrl+V approach for speed and reliability.
    Optionally restores the original clipboard content afterwards.

    Args:
        text: The text to inject
        restore_clipboard: Whether to restore the original clipboard content
    """
    if not text or not text.strip():
        logger.warning("Empty text, nothing to inject")
        return

    with _lock:
        original_clipboard = None

        try:
            # 1. Save original clipboard content
            if restore_clipboard:
                try:
                    original_clipboard = pyperclip.paste()
                except Exception:
                    original_clipboard = None

            # 2. Copy transcribed text to clipboard
            pyperclip.copy(text)

            # Small delay to ensure clipboard is updated and UI focus returns to target
            time.sleep(0.15)

            # 3. Ensure all modifiers are released before Ctrl+V
            # This is critical if the user is still holding Shift or Alt from the hotkey
            for mod in [Key.shift, Key.shift_r, Key.alt, Key.alt_l, Key.alt_gr, Key.ctrl, Key.ctrl_r]:
                _keyboard.release(mod)

            # 4. Simulate Ctrl+V to paste
            with _keyboard.pressed(Key.ctrl):
                _keyboard.tap('v')

            logger.info(f"[SUCCESS] Injected {len(text)} characters into active field")

            # 4. Restore original clipboard after a delay
            if restore_clipboard and original_clipboard is not None:
                time.sleep(0.3)
                try:
                    pyperclip.copy(original_clipboard)
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"[ERROR] Text injection failed: {e}")


def inject_text_async(text: str, restore_clipboard: bool = True):
    """Inject text in a background thread to avoid blocking."""
    thread = threading.Thread(
        target=inject_text,
        args=(text, restore_clipboard),
        daemon=True,
    )
    thread.start()
