"""
WhisperFlow — Hotkey Manager
Global keyboard shortcut listener using pynput.
Supports both Hold (press-and-hold) and Toggle (press-to-start/press-to-stop) modes.
"""

import threading
from typing import Callable, Optional, Set
from pynput import keyboard

from src.utils.logger import get_logger

logger = get_logger("HotkeyManager")


# Map string names to pynput Key objects
KEY_MAP = {
    "ctrl": keyboard.Key.ctrl_l,
    "shift": keyboard.Key.shift_l,
    "alt": keyboard.Key.alt_l,
    "space": keyboard.Key.space,
    "tab": keyboard.Key.tab,
    "enter": keyboard.Key.enter,
    "insert": keyboard.Key.insert,
    "f1": keyboard.Key.f1,
    "f2": keyboard.Key.f2,
    "f3": keyboard.Key.f3,
    "f4": keyboard.Key.f4,
    "f5": keyboard.Key.f5,
    "f6": keyboard.Key.f6,
    "f7": keyboard.Key.f7,
    "f8": keyboard.Key.f8,
    "f9": keyboard.Key.f9,
    "f10": keyboard.Key.f10,
    "f11": keyboard.Key.f11,
    "f12": keyboard.Key.f12,
}


def parse_hotkey(hotkey_string: str) -> Set:
    """
    Parse a hotkey string like 'ctrl+shift+space' into a set of pynput keys.
    """
    keys = set()
    parts = [p.strip().lower() for p in hotkey_string.split("+")]

    for part in parts:
        if part in KEY_MAP:
            keys.add(KEY_MAP[part])
        elif len(part) == 1:
            # Single character key
            keys.add(keyboard.KeyCode.from_char(part))
        else:
            logger.warning(f"Unknown key: '{part}'")

    return keys


class HotkeyManager:
    """
    Manages global hotkey detection.

    Modes:
      - "toggle": First press starts, second press stops.
      - "hold": Press-and-hold starts, release stops.
    """

    def __init__(
        self,
        hotkey: str = "ctrl+shift+space",
        mode: str = "toggle",
        on_activate: Optional[Callable] = None,
        on_deactivate: Optional[Callable] = None,
    ):
        self._hotkey_string = hotkey
        self._hotkey_keys = parse_hotkey(hotkey)
        self._mode = mode
        self._on_activate = on_activate
        self._on_deactivate = on_deactivate

        self._pressed_keys: Set = set()
        self._is_active = False
        self._is_paused = False
        self._listener: Optional[keyboard.Listener] = None
        self._lock = threading.Lock()

        logger.info(f"Hotkey configured: '{hotkey}' (mode: {mode})")

    def start(self):
        """Start listening for the global hotkey."""
        if self._listener is not None:
            return

        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.daemon = True
        self._listener.start()
        logger.info("[KEYBOARD] Hotkey listener started")

    def stop(self):
        """Stop listening for hotkeys."""
        if self._listener:
            self._listener.stop()
            self._listener = None
        logger.info("[KEYBOARD] Hotkey listener stopped")

    def pause(self):
        """Temporarily pause hotkey detection."""
        self._is_paused = True
        logger.info("[PAUSE] Hotkey paused")

    def resume(self):
        """Resume hotkey detection."""
        self._is_paused = False
        logger.info("[RESUME] Hotkey resumed")

    def _normalize_key(self, key):
        """Normalize key to match our key set."""
        # Map right-side modifiers to left-side
        right_to_left = {
            keyboard.Key.ctrl_r: keyboard.Key.ctrl_l,
            keyboard.Key.shift_r: keyboard.Key.shift_l,
            keyboard.Key.alt_r: keyboard.Key.alt_l,
            keyboard.Key.alt_gr: keyboard.Key.alt_l,
        }
        return right_to_left.get(key, key)

    def _on_press(self, key):
        """Handle key press events."""
        if self._is_paused:
            return

        key = self._normalize_key(key)
        self._pressed_keys.add(key)

        # Check if our full hotkey combo is pressed
        is_combo_pressed = self._hotkey_keys.issubset(self._pressed_keys)
        
        if is_combo_pressed:
            with self._lock:
                if self._mode == "toggle":
                    # For toggle, we only want to act on the first press event, 
                    # not on auto-repeats. We use a flag to track if we've handled this press.
                    if not getattr(self, '_combo_already_pressed', False):
                        self._combo_already_pressed = True
                        if not self._is_active:
                            self._is_active = True
                            logger.info("[ON] Hotkey activated (toggle)")
                            if self._on_activate:
                                threading.Thread(target=self._on_activate, daemon=True).start()
                        else:
                            self._is_active = False
                            logger.info("[OFF] Hotkey deactivated (toggle)")
                            if self._on_deactivate:
                                threading.Thread(target=self._on_deactivate, daemon=True).start()
                
                elif self._mode == "hold":
                    if not self._is_active:
                        self._is_active = True
                        logger.info("[ON] Hotkey activated (hold)")
                        if self._on_activate:
                            threading.Thread(target=self._on_activate, daemon=True).start()

    def _on_release(self, key):
        """Handle key release events."""
        key = self._normalize_key(key)
        self._pressed_keys.discard(key)
        
        # Reset the combo-already-pressed flag if any key of the combo is released
        if key in self._hotkey_keys:
            self._combo_already_pressed = False

        # In hold mode, releasing any part of the combo deactivates
        if self._mode == "hold" and self._is_active:
            # We check if the combo is still held
            if not self._hotkey_keys.issubset(self._pressed_keys):
                with self._lock:
                    self._is_active = False
                    logger.info("[OFF] Hotkey deactivated (released)")
                    if self._on_deactivate:
                        threading.Thread(target=self._on_deactivate, daemon=True).start()

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def is_paused(self) -> bool:
        return self._is_paused

    def update_hotkey(self, hotkey: str, mode: str = None):
        """Update the hotkey combination. Requires restart of listener."""
        with self._lock:
            self._hotkey_string = hotkey
            self._hotkey_keys = parse_hotkey(hotkey)
            if mode:
                self._mode = mode
            
            # Reset state to avoid "stuck" listening
            self._is_active = False
            self._pressed_keys.clear()
            self._combo_already_pressed = False
            
            logger.info(f"Hotkey updated to: '{hotkey}' (mode: {self._mode})")

        # Restart listener if running
        was_running = self._listener is not None
        if was_running:
            self.stop()
            self.start()
