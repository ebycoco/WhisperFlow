"""
WhisperFlow — Local Whisper Engine
Uses faster-whisper (CTranslate2) for offline, private speech-to-text.
"""

import numpy as np
from typing import Optional

from src.core.transcriber import BaseTranscriber
from src.config.settings import get_models_dir
from src.utils.logger import get_logger

logger = get_logger("WhisperEngine")


class WhisperEngine(BaseTranscriber):
    """
    Local speech-to-text using faster-whisper.
    Supports NVIDIA GPU (CUDA) acceleration with CPU fallback.
    """

    SUPPORTED_MODELS = ["tiny", "base", "small", "medium", "large-v3"]

    def __init__(self, model_size: str = "base"):
        if model_size not in self.SUPPORTED_MODELS:
            logger.warning(f"Unknown model '{model_size}', falling back to 'base'")
            model_size = "base"

        self._model_size = model_size
        self._model = None
        self._device = None
        self._compute_type = None

    def _load_model(self):
        """Lazy-load the Whisper model on first use."""
        if self._model is not None:
            return

        try:
            from faster_whisper import WhisperModel

            # Auto-detect GPU availability
            self._device, self._compute_type = self._detect_device()

            logger.info(
                f"Loading faster-whisper model '{self._model_size}' "
                f"on {self._device} ({self._compute_type})..."
            )

            import os
            num_threads = os.cpu_count() or 4
            
            self._model = WhisperModel(
                self._model_size,
                device=self._device,
                compute_type=self._compute_type,
                download_root=str(get_models_dir()),
                cpu_threads=num_threads,
                num_workers=2
            )

            logger.info(f"[SUCCESS] Model '{self._model_size}' loaded successfully")

        except Exception as e:
            logger.error(f"[ERROR] Failed to load Whisper model: {e}")
            raise

    def _detect_device(self) -> tuple[str, str]:
        """Detect whether CUDA GPU is available."""
        try:
            import torch
            if torch.cuda.is_available():
                logger.info(f"CUDA GPU detected: {torch.cuda.get_device_name(0)}")
                return "cuda", "float16"
        except ImportError:
            pass

        # Try CTranslate2 CUDA check as fallback
        try:
            import ctranslate2
            if "cuda" in ctranslate2.get_supported_compute_types("cuda"):
                logger.info("CUDA available via CTranslate2")
                return "cuda", "float16"
        except Exception:
            pass

        logger.info("No GPU detected — using CPU with int8 quantization")
        return "cpu", "int8"

    def transcribe(self, audio_data: np.ndarray, language: str = "auto") -> str:
        """
        Transcribe audio using the local Whisper model.

        Args:
            audio_data: int16 numpy array at 16kHz mono
            language: ISO code or "auto"

        Returns:
            Transcribed text
        """
        self._load_model()

        # Convert int16 to float32 normalized [-1, 1] as expected by faster-whisper
        audio_float = audio_data.astype(np.float32) / 32768.0

        transcribe_kwargs = {
            "beam_size": 10,         # Increased from 5 to 10 for better accuracy
            "vad_filter": True,
            "vad_parameters": {
                "min_silence_duration_ms": 500,
            },
            "initial_prompt": "Ceci est une dictée vocale en français.", # Help Whisper stay in French
        }

        if language != "auto":
            transcribe_kwargs["language"] = language

        try:
            segments, info = self._model.transcribe(audio_float, **transcribe_kwargs)

            detected_lang = info.language
            logger.info(
                f"Detected language: {detected_lang} "
                f"(probability: {info.language_probability:.2f})"
            )

            # Collect all segment texts
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())

            full_text = " ".join(text_parts)
            logger.info(f"Transcription result: '{full_text[:100]}...'")
            return full_text

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return ""

    def is_available(self) -> bool:
        """Check if faster-whisper is installed."""
        try:
            import faster_whisper
            return True
        except ImportError:
            return False

    def get_name(self) -> str:
        device_info = f" ({self._device})" if self._device else ""
        return f"Whisper Local [{self._model_size}]{device_info}"
