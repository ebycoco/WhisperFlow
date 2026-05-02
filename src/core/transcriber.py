"""
WhisperFlow — Transcriber Interface
Abstract base class and factory for speech-to-text engines.
"""

from abc import ABC, abstractmethod
from typing import Optional

import numpy as np

from src.utils.logger import get_logger

logger = get_logger("Transcriber")


class BaseTranscriber(ABC):
    """Abstract interface for speech-to-text engines."""

    @abstractmethod
    def transcribe(self, audio_data: np.ndarray, language: str = "auto") -> str:
        """
        Transcribe audio data to text.

        Args:
            audio_data: numpy array of int16 audio samples at 16kHz mono.
            language: ISO language code or "auto" for auto-detection.

        Returns:
            Transcribed text string.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this engine is ready to use."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return human-readable engine name."""
        pass


class TranscriberFactory:
    """Factory to create the appropriate transcription engine."""

    @staticmethod
    def create(engine_type: str, **kwargs) -> BaseTranscriber:
        """
        Create a transcriber instance.

        Args:
            engine_type: "local" for faster-whisper, "groq" for Groq API
            **kwargs: Engine-specific configuration

        Returns:
            A BaseTranscriber instance
        """
        if engine_type == "local":
            from src.core.whisper_engine import WhisperEngine
            return WhisperEngine(
                model_size=kwargs.get("model", "base"),
            )
        elif engine_type == "groq":
            from src.core.groq_engine import GroqEngine
            return GroqEngine(
                api_key=kwargs.get("api_key", ""),
            )
        else:
            raise ValueError(f"Unknown engine type: {engine_type}")
