"""
WhisperFlow — Groq Cloud Engine
Uses Groq's ultra-fast Whisper API for cloud-based speech-to-text.
"""

import io
import numpy as np
from typing import Optional

from src.core.transcriber import BaseTranscriber
from src.core.audio_recorder import AudioRecorder
from src.utils.logger import get_logger

logger = get_logger("GroqEngine")


class GroqEngine(BaseTranscriber):
    """
    Cloud speech-to-text using Groq's Whisper API.
    Extremely fast (~2s for 60s audio) but requires internet + API key.
    """

    def __init__(self, api_key: str = ""):
        self._api_key = api_key
        self._client = None

    def _init_client(self):
        """Initialize the Groq client lazily."""
        if self._client is not None:
            return

        if not self._api_key:
            raise ValueError("Groq API key is required. Set it in Settings.")

        try:
            from groq import Groq
            self._client = Groq(api_key=self._api_key)
            logger.info("[SUCCESS] Groq client initialized")
        except ImportError:
            raise ImportError("groq package not installed. Run: pip install groq")

    def transcribe(self, audio_data: np.ndarray, language: str = "auto") -> str:
        """
        Transcribe audio using Groq's Whisper API.

        Args:
            audio_data: int16 numpy array at 16kHz mono
            language: ISO code or "auto"

        Returns:
            Transcribed text
        """
        self._init_client()

        # Convert numpy array to WAV bytes for upload
        wav_bytes = AudioRecorder.numpy_to_wav_bytes(audio_data)

        try:
            # Create a file-like object for the API
            audio_file = io.BytesIO(wav_bytes)
            audio_file.name = "recording.wav"

            transcribe_kwargs = {
                "file": audio_file,
                "model": "whisper-large-v3",
                "response_format": "text",
            }

            if language != "auto":
                transcribe_kwargs["language"] = language

            logger.info("Sending audio to Groq API...")
            result = self._client.audio.transcriptions.create(**transcribe_kwargs)

            text = result.strip() if isinstance(result, str) else str(result).strip()
            logger.info(f"Groq transcription result: '{text[:100]}...'")
            return text

        except Exception as e:
            logger.error(f"Groq transcription failed: {e}")
            return ""

    def is_available(self) -> bool:
        """Check if Groq SDK is installed and API key is configured."""
        if not self._api_key:
            return False
        try:
            import groq
            return True
        except ImportError:
            return False

    def get_name(self) -> str:
        return "Groq Cloud [whisper-large-v3]"

    def set_api_key(self, api_key: str):
        """Update the API key (resets client)."""
        self._api_key = api_key
        self._client = None
