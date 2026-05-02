"""
WhisperFlow — Floating Overlay
Semi-transparent overlay window showing dictation state.
Modern dark glassmorphism design using tkinter.
"""

import threading
import tkinter as tk
from typing import Optional
import math
import time

from src.utils.logger import get_logger

logger = get_logger("Overlay")


class DictationOverlay:
    """
    A sleek, floating overlay window that shows the current dictation state.
    Features a modern dark glassmorphism design with smooth animations.
    """

    # ── Color Palette (Dark Modern) ──────────────────────
    BG_COLOR = "#0D0D1A"          # Deep navy black
    BG_ACCENT = "#1A1A3E"         # Slightly lighter for depth
    BORDER_COLOR = "#2D2D5E"      # Subtle border
    TEXT_COLOR = "#E8E8F0"         # Soft white
    TEXT_MUTED = "#8888AA"         # Muted text

    COLOR_LISTENING = "#6C63FF"    # Vibrant purple
    COLOR_LISTENING_GLOW = "#8B83FF"
    COLOR_PROCESSING = "#FFA940"   # Warm amber
    COLOR_SUCCESS = "#52C41A"      # Green
    COLOR_ERROR = "#FF4B4B"        # Red

    # ── Dimensions ───────────────────────────────────────
    WIDTH = 340
    HEIGHT = 72
    CORNER_RADIUS = 18
    PADDING_BOTTOM = 60

    def __init__(self):
        self._root: Optional[tk.Tk] = None
        self._canvas: Optional[tk.Canvas] = None
        self._thread: Optional[threading.Thread] = None
        self._is_visible = False
        self._animation_running = False
        self._animation_phase = 0.0
        self._current_state = "idle"
        self._ready_event = threading.Event()

    def _create_window(self):
        """Create the overlay window on a dedicated tkinter thread."""
        self._root = tk.Tk()
        self._root.title("WhisperFlow")
        self._root.overrideredirect(True)          # No window decorations
        self._root.attributes("-topmost", True)     # Always on top
        self._root.attributes("-alpha", 0.92)       # Slight transparency
        self._root.configure(bg=self.BG_COLOR)

        # Make background transparent (Windows)
        try:
            self._root.attributes("-transparentcolor", "#000001")
        except tk.TclError:
            pass

        # Position at bottom center of screen
        screen_w = self._root.winfo_screenwidth()
        screen_h = self._root.winfo_screenheight()
        x = (screen_w - self.WIDTH) // 2
        y = screen_h - self.HEIGHT - self.PADDING_BOTTOM

        self._root.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

        # Canvas for custom drawing
        self._canvas = tk.Canvas(
            self._root,
            width=self.WIDTH,
            height=self.HEIGHT,
            bg=self.BG_COLOR,
            highlightthickness=0,
            bd=0,
        )
        self._canvas.pack(fill="both", expand=True)

        # Start hidden
        self._root.withdraw()
        self._ready_event.set()

        # Run tkinter main loop
        self._root.mainloop()

    def start(self):
        """Start the overlay system in a background thread."""
        self._thread = threading.Thread(target=self._create_window, daemon=True)
        self._thread.start()
        self._ready_event.wait(timeout=3.0)
        logger.info("Overlay system ready")

    def show(self, state: str, text: str = ""):
        """
        Show the overlay with a specific state.

        Args:
            state: "listening", "processing", "success", "error"
            text: Optional status text to display
        """
        if not self._root:
            return

        self._current_state = state
        self._is_visible = True

        try:
            self._root.after(0, lambda: self._show_state(state, text))
        except Exception as e:
            logger.error(f"Failed to show overlay: {e}")

    def hide(self):
        """Hide the overlay."""
        if not self._root:
            return

        self._is_visible = False
        self._animation_running = False

        try:
            self._root.after(0, self._hide_window)
        except Exception:
            pass

    def _show_state(self, state: str, text: str):
        """Internal: render the appropriate state on the canvas."""
        if not self._canvas or not self._root:
            return

        self._root.deiconify()
        self._canvas.delete("all")

        # Draw rounded rectangle background
        self._draw_rounded_rect(
            2, 2, self.WIDTH - 2, self.HEIGHT - 2,
            radius=self.CORNER_RADIUS,
            fill=self.BG_COLOR,
            outline=self.BORDER_COLOR,
        )

        # State-specific rendering
        if state == "listening":
            color = self.COLOR_LISTENING
            icon = "🎤"
            default_text = "Listening..."
            self._start_pulse_animation(color)

        elif state == "processing":
            color = self.COLOR_PROCESSING
            icon = "⏳"
            default_text = "Processing..."
            self._start_spinner_animation(color)

        elif state == "success":
            color = self.COLOR_SUCCESS
            icon = "✅"
            default_text = "Done!"
            # Auto-hide after 1.5 seconds
            self._root.after(1500, self.hide)

        elif state == "error":
            color = self.COLOR_ERROR
            icon = "❌"
            default_text = "Error"
            self._root.after(2500, self.hide)

        else:
            return

        display_text = text or default_text

        # Draw accent bar on the left
        self._canvas.create_rectangle(
            6, 14, 10, self.HEIGHT - 14,
            fill=color, outline="",
        )

        # Draw icon
        self._canvas.create_text(
            32, self.HEIGHT // 2,
            text=icon,
            font=("Segoe UI Emoji", 18),
            fill=self.TEXT_COLOR,
            anchor="w",
        )

        # Draw status text
        self._canvas.create_text(
            62, self.HEIGHT // 2 - 2,
            text=display_text,
            font=("Segoe UI", 13, "bold"),
            fill=self.TEXT_COLOR,
            anchor="w",
        )

        # Draw subtle hotkey hint
        self._canvas.create_text(
            self.WIDTH - 16, self.HEIGHT // 2,
            text="Ctrl+Shift+Space",
            font=("Segoe UI", 8),
            fill=self.TEXT_MUTED,
            anchor="e",
        )

    def _start_pulse_animation(self, color: str):
        """Animate a pulsing dot for the listening state."""
        self._animation_running = True
        self._animation_phase = 0.0

        def pulse():
            if not self._animation_running or not self._canvas:
                return

            self._animation_phase += 0.15
            alpha = (math.sin(self._animation_phase) + 1) / 2  # 0..1

            # Pulsing circle indicator
            size = 6 + int(alpha * 4)
            cx, cy = self.WIDTH - 50, self.HEIGHT // 2

            self._canvas.delete("pulse")
            self._canvas.create_oval(
                cx - size, cy - size, cx + size, cy + size,
                fill=color, outline="", tags="pulse",
            )

            if self._animation_running:
                self._root.after(50, pulse)

        self._root.after(50, pulse)

    def _start_spinner_animation(self, color: str):
        """Animate a spinner for the processing state."""
        self._animation_running = True
        self._animation_phase = 0.0

        def spin():
            if not self._animation_running or not self._canvas:
                return

            self._animation_phase += 15
            cx, cy = self.WIDTH - 50, self.HEIGHT // 2
            r = 10

            self._canvas.delete("spinner")

            start_angle = self._animation_phase % 360
            self._canvas.create_arc(
                cx - r, cy - r, cx + r, cy + r,
                start=start_angle, extent=270,
                style="arc", outline=color, width=3,
                tags="spinner",
            )

            if self._animation_running:
                self._root.after(40, spin)

        self._root.after(40, spin)

    def _draw_rounded_rect(self, x1, y1, x2, y2, radius=20, **kwargs):
        """Draw a rounded rectangle on the canvas."""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1, x2, y1 + radius,
            x2, y2 - radius,
            x2, y2, x2 - radius, y2,
            x1 + radius, y2,
            x1, y2, x1, y2 - radius,
            x1, y1 + radius,
            x1, y1, x1 + radius, y1,
        ]
        return self._canvas.create_polygon(points, smooth=True, **kwargs)

    def _hide_window(self):
        """Internal: hide the overlay window."""
        if self._root:
            self._animation_running = False
            self._root.withdraw()

    def stop(self):
        """Stop and destroy the overlay."""
        self._animation_running = False
        self._is_visible = False
        if self._root:
            try:
                self._root.after(0, self._root.destroy)
            except Exception:
                pass
