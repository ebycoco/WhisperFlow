"""
WhisperFlow — Settings Window
Modern dark-themed UI using customtkinter.
"""

import threading
import tkinter as tk
from typing import Optional, Callable

import customtkinter as ctk

from src.config.settings import Settings
from src.core.audio_recorder import AudioRecorder
from src.utils.logger import get_logger

logger = get_logger("SettingsWindow")


class SettingsWindow:
    """
    Application settings window with a modern dark theme.
    """

    def __init__(self, settings: Settings, on_save: Optional[Callable] = None):
        self._settings = settings
        self._on_save = on_save
        self._root: Optional[ctk.CTk] = None
        self._is_open = False

    def show(self):
        """Open the settings window. If already open, bring to front."""
        if self._is_open and self._root:
            self._root.lift()
            self._root.focus_force()
            return

        self._is_open = True
        
        # Configure customtkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._root = ctk.CTk()
        self._root.title("WhisperFlow Settings")
        self._root.geometry("600x500")
        self._root.resizable(False, False)
        
        # Handle window close
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        
        # Center on screen
        self._root.eval('tk::PlaceWindow . center')
        
        # Start main loop
        self._root.mainloop()

    def _build_ui(self):
        """Build the settings interface."""
        # Tab view
        self.tabview = ctk.CTkTabview(self._root)
        self.tabview.pack(padx=20, pady=(20, 10), fill="both", expand=True)

        self.tab_general = self.tabview.add("General")
        self.tab_engine = self.tabview.add("Engine")
        self.tab_audio = self.tabview.add("Audio")

        self._build_general_tab()
        self._build_engine_tab()
        self._build_audio_tab()

        # Buttons frame
        btn_frame = ctk.CTkFrame(self._root, fg_color="transparent")
        btn_frame.pack(padx=20, pady=10, fill="x")

        btn_save = ctk.CTkButton(
            btn_frame, text="Save & Apply", command=self._save_settings
        )
        btn_save.pack(side="right", padx=5)

        btn_cancel = ctk.CTkButton(
            btn_frame, text="Cancel", fg_color="transparent", 
            border_width=1, command=self._on_close
        )
        btn_cancel.pack(side="right", padx=5)

    def _build_general_tab(self):
        """Build the General settings tab."""
        parent = self.tab_general
        
        # Hotkey
        lbl_hotkey = ctk.CTkLabel(parent, text="Global Hotkey:", font=("Segoe UI", 12, "bold"))
        lbl_hotkey.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        
        self.hotkey_options = [
            "ctrl+shift+space",
            "ctrl+alt+s",
            "ctrl+alt+v",
            "alt+space",
            "f9",
            "f10"
        ]
        
        # Ensure current hotkey is in the list
        curr_hotkey = self._settings.hotkey.lower()
        if curr_hotkey not in self.hotkey_options:
            self.hotkey_options.append(curr_hotkey)
            
        self.var_hotkey = ctk.StringVar(value=curr_hotkey)
        self.menu_hotkey = ctk.CTkOptionMenu(
            parent, values=self.hotkey_options, variable=self.var_hotkey, width=250
        )
        self.menu_hotkey.grid(row=0, column=1, padx=20, pady=(20, 5), sticky="w")
        
        # Activation Mode
        lbl_mode = ctk.CTkLabel(parent, text="Activation Mode:", font=("Segoe UI", 12, "bold"))
        lbl_mode.grid(row=1, column=0, padx=20, pady=15, sticky="w")
        
        self.var_mode = ctk.StringVar(value=self._settings.activation_mode)
        radio_toggle = ctk.CTkRadioButton(parent, text="Toggle (Press to start/stop)", variable=self.var_mode, value="toggle")
        radio_toggle.grid(row=1, column=1, padx=20, pady=5, sticky="w")
        
        radio_hold = ctk.CTkRadioButton(parent, text="Hold (Press and hold)", variable=self.var_mode, value="hold")
        radio_hold.grid(row=2, column=1, padx=20, pady=0, sticky="w")

        # Auto Punctuation
        self.var_punct = ctk.BooleanVar(value=self._settings.auto_punctuation)
        chk_punct = ctk.CTkCheckBox(parent, text="Auto-add punctuation", variable=self.var_punct)
        chk_punct.grid(row=3, column=1, padx=20, pady=(20, 5), sticky="w")

        # Filler Removal
        self.var_filler = ctk.BooleanVar(value=self._settings.filler_removal)
        chk_filler = ctk.CTkCheckBox(parent, text="Remove filler words (um, uh, etc.)", variable=self.var_filler)
        chk_filler.grid(row=4, column=1, padx=20, pady=5, sticky="w")

        # Auto Start
        self.var_autostart = ctk.BooleanVar(value=self._settings.auto_start)
        chk_autostart = ctk.CTkCheckBox(parent, text="Launch WhisperFlow when Windows starts", variable=self.var_autostart)
        chk_autostart.grid(row=5, column=1, padx=20, pady=(15, 5), sticky="w")

    def _build_engine_tab(self):
        """Build the Engine settings tab."""
        parent = self.tab_engine
        
        # Engine Type
        lbl_engine = ctk.CTkLabel(parent, text="Transcription Engine:", font=("Segoe UI", 12, "bold"))
        lbl_engine.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        
        self.var_engine = ctk.StringVar(value=self._settings.engine)
        engine_menu = ctk.CTkOptionMenu(
            parent, values=["local", "groq"], variable=self.var_engine, width=200
        )
        engine_menu.grid(row=0, column=1, padx=20, pady=(20, 5), sticky="w")
        
        # Local Model
        lbl_model = ctk.CTkLabel(parent, text="Local Model Size:", font=("Segoe UI", 12, "bold"))
        lbl_model.grid(row=1, column=0, padx=20, pady=15, sticky="w")
        
        self.var_model = ctk.StringVar(value=self._settings.model)
        model_menu = ctk.CTkOptionMenu(
            parent, values=["tiny", "base", "small", "medium", "large-v3"], variable=self.var_model, width=200
        )
        model_menu.grid(row=1, column=1, padx=20, pady=15, sticky="w")

        lbl_model_hint = ctk.CTkLabel(parent, text="('base' is recommended for CPU. 'small'/'large-v3' for better accuracy if you have a GPU)", text_color="gray", font=("Segoe UI", 10))
        lbl_model_hint.grid(row=2, column=1, padx=20, pady=(0, 15), sticky="w")

        # Language
        lbl_lang = ctk.CTkLabel(parent, text="Target Language:", font=("Segoe UI", 12, "bold"))
        lbl_lang.grid(row=3, column=0, padx=20, pady=10, sticky="w")
        
        self.lang_map = {
            "Auto-Detect": "auto",
            "French (Français)": "fr",
            "English": "en",
            "Spanish": "es",
            "German": "de",
            "Italian": "it"
        }
        self.lang_options = list(self.lang_map.keys())
        
        curr_lang_code = self._settings.language
        curr_lang_name = "Auto-Detect"
        for name, code in self.lang_map.items():
            if code == curr_lang_code:
                curr_lang_name = name
                break
                
        self.var_lang = ctk.StringVar(value=curr_lang_name)
        lang_menu = ctk.CTkOptionMenu(
            parent, values=self.lang_options, variable=self.var_lang, width=200
        )
        lang_menu.grid(row=3, column=1, padx=20, pady=10, sticky="w")

        # Groq API Key
        lbl_api = ctk.CTkLabel(parent, text="Groq API Key (Cloud):", font=("Segoe UI", 12, "bold"))
        lbl_api.grid(row=4, column=0, padx=20, pady=10, sticky="w")
        
        self.entry_api = ctk.CTkEntry(parent, width=300, show="*")
        self.entry_api.insert(0, self._settings.groq_api_key)
        self.entry_api.grid(row=4, column=1, padx=20, pady=10, sticky="w")

    def _build_audio_tab(self):
        """Build the Audio settings tab."""
        parent = self.tab_audio
        
        # Microphones
        lbl_mic = ctk.CTkLabel(parent, text="Microphone:", font=("Segoe UI", 12, "bold"))
        lbl_mic.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        
        # Fetch mics
        self.mics = AudioRecorder.list_microphones()
        mic_names = ["System Default"] + [m["name"] for m in self.mics]
        
        self.var_mic = ctk.StringVar()
        
        # Set current
        curr_idx = self._settings.microphone_index
        if curr_idx is not None and any(m["index"] == curr_idx for m in self.mics):
            curr_name = next(m["name"] for m in self.mics if m["index"] == curr_idx)
            self.var_mic.set(curr_name)
        else:
            self.var_mic.set("System Default")
            
        mic_menu = ctk.CTkOptionMenu(
            parent, values=mic_names, variable=self.var_mic, width=300
        )
        mic_menu.grid(row=0, column=1, padx=20, pady=(20, 5), sticky="w")

    def _save_settings(self):
        """Save settings and close."""
        self._settings.set("hotkey", self.var_hotkey.get())
        self._settings.set("activation_mode", self.var_mode.get())
        self._settings.set("auto_punctuation", self.var_punct.get())
        self._settings.set("filler_removal", self.var_filler.get())
        
        self._settings.set("engine", self.var_engine.get())
        self._settings.set("model", self.var_model.get())
        self._settings.set("language", self.lang_map.get(self.var_lang.get(), "auto"))
        self._settings.set("groq_api_key", self.entry_api.get().strip())
        
        # Apply Auto-Start
        self._settings.set_auto_start(self.var_autostart.get())
        
        # Resolve mic index
        selected_mic = self.var_mic.get()
        if selected_mic == "System Default":
            self._settings.set("microphone_index", None)
        else:
            for m in self.mics:
                if m["name"] == selected_mic:
                    self._settings.set("microphone_index", m["index"])
                    break

        logger.info("Settings saved")
        
        if self._on_save:
            self._on_save()
            
        self._on_close()

    def _on_close(self):
        """Handle window close."""
        self._is_open = False
        if self._root:
            self._root.destroy()
            self._root = None
