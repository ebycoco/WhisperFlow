"""
WhisperFlow — System Tray Icon
Background tray icon with context menu using pystray.
"""

import threading
from typing import Callable, Optional

from PIL import Image, ImageDraw, ImageFont
import pystray

from src.utils.logger import get_logger

logger = get_logger("TrayIcon")


class TrayIcon:
    """
    System tray icon for WhisperFlow.
    Runs in its own thread and provides a context menu.
    """

    # Color scheme (dark modern)
    COLOR_IDLE = "#6C63FF"       # Purple accent
    COLOR_RECORDING = "#FF4B4B"  # Red pulse
    COLOR_PROCESSING = "#FFA940" # Amber
    COLOR_BG = "#1A1A2E"         # Dark background

    def __init__(
        self,
        on_settings: Optional[Callable] = None,
        on_pause: Optional[Callable] = None,
        on_logout: Optional[Callable] = None,
        on_quit: Optional[Callable] = None,
    ):
        self._on_settings = on_settings
        self._on_pause = on_pause
        self._on_logout = on_logout
        self._on_quit = on_quit
        self._icon: Optional[pystray.Icon] = None
        self._thread: Optional[threading.Thread] = None
        self._is_paused = False

    def start(self):
        """Start the tray icon in a background thread."""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("[UI] System tray icon started")

    def _run(self):
        """Internal: create and run the tray icon."""
        menu = pystray.Menu(
            pystray.MenuItem(
                "Settings",
                self._handle_settings,
            ),
            pystray.MenuItem(
                lambda item: "Resume" if self._is_paused else "Pause",
                self._handle_pause,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Déconnexion",
                self._handle_logout,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "About WhisperFlow",
                self._handle_about,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Quit",
                self._handle_quit,
            ),
        )

        logger.info("[UI] Creating pystray icon...")
        self._icon = pystray.Icon(
            name="WhisperFlow",
            icon=self._create_icon(self.COLOR_IDLE),
            title="WhisperFlow - Ready",
            menu=menu,
        )

        logger.info("[UI] Running pystray loop...")
        self._icon.run()

    def _create_icon(self, color: str, size: int = 64) -> Image.Image:
        """Create a programmatic tray icon with the given accent color."""
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Background circle
        padding = 4
        draw.ellipse(
            [padding, padding, size - padding, size - padding],
            fill=color,
        )

        # Microphone shape (simplified)
        cx, cy = size // 2, size // 2
        mic_w, mic_h = 10, 16

        # Mic body (rounded rectangle)
        draw.rounded_rectangle(
            [cx - mic_w // 2, cy - mic_h // 2 - 4,
             cx + mic_w // 2, cy + mic_h // 2 - 4],
            radius=5,
            fill="white",
        )

        # Mic stand arc
        arc_y = cy + mic_h // 2 - 8
        draw.arc(
            [cx - mic_w, arc_y, cx + mic_w, arc_y + 14],
            start=0, end=180,
            fill="white",
            width=2,
        )

        # Stand line
        draw.line(
            [cx, arc_y + 14, cx, arc_y + 20],
            fill="white",
            width=2,
        )

        return img

    def set_state(self, state: str):
        """
        Update the tray icon to reflect the current state.

        Args:
            state: "idle", "recording", "processing"
        """
        if not self._icon:
            return

        color_map = {
            "idle": (self.COLOR_IDLE, "WhisperFlow — Ready"),
            "recording": (self.COLOR_RECORDING, "WhisperFlow — 🎤 Recording..."),
            "processing": (self.COLOR_PROCESSING, "WhisperFlow — ⏳ Processing..."),
        }

        color, title = color_map.get(state, (self.COLOR_IDLE, "WhisperFlow"))

        try:
            self._icon.icon = self._create_icon(color)
            self._icon.title = title
        except Exception as e:
            logger.error(f"Failed to update tray icon: {e}")

    def _handle_settings(self, icon, item):
        if self._on_settings:
            self._on_settings()

    def _handle_pause(self, icon, item):
        self._is_paused = not self._is_paused
        if self._on_pause:
            self._on_pause(self._is_paused)

    def _handle_logout(self, icon, item):
        if self._on_logout:
            self._on_logout()

    def _handle_about(self, icon, item):
        """Show about info."""
        logger.info("WhisperFlow v1.0 - AI Voice Dictation")

    def _handle_quit(self, icon, item):
        logger.info("Quit requested from tray")
        if self._icon:
            self._icon.stop()
        if self._on_quit:
            self._on_quit()

    def stop(self):
        """Stop and remove the tray icon."""
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
