"""
WhisperFlow — Audio Recorder
Captures audio from the microphone using sounddevice into a numpy buffer.
"""

import threading
import numpy as np
import wave
import io
import queue
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger("AudioRecorder")

# Whisper expects 16kHz, 16-bit, mono audio
SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2  # 16-bit = 2 bytes
FORMAT_NUMPY_DTYPE = np.int16


class AudioRecorder:
    """Records audio from the microphone into a numpy buffer using sounddevice."""

    def __init__(self, device_index: Optional[int] = None):
        self._device_index = device_index
        self._is_recording = False
        self._audio_queue = queue.Queue()
        self._stream = None
        self._lock = threading.Lock()
        self._audio_data = []
        self._consumer_thread: Optional[threading.Thread] = None

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    def start(self):
        """Start recording audio in a background thread."""
        if self._is_recording:
            logger.warning("Already recording, ignoring start request")
            return

        import sounddevice as sd

        self._audio_data = []
        self._is_recording = True

        def callback(indata, frames, time, status):
            if status:
                logger.warning(f"Audio status: {status}")
            self._audio_queue.put(indata.copy())

        try:
            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                device=self._device_index,
                channels=CHANNELS,
                dtype=FORMAT_NUMPY_DTYPE,
                callback=callback
            )
            self._stream.start()
            logger.info("[AUDIO] Recording started")
            
            # Start a thread to consume the queue and avoid blocking the audio callback
            self._consumer_thread = threading.Thread(target=self._consume_queue, daemon=True)
            self._consumer_thread.start()
            
        except Exception as e:
            self._is_recording = False
            logger.error(f"Failed to open audio stream: {e}")

    def _consume_queue(self):
        while self._is_recording or not self._audio_queue.empty():
            try:
                data = self._audio_queue.get(timeout=0.1)
                with self._lock:
                    self._audio_data.append(data)
            except queue.Empty:
                pass

    def stop(self) -> Optional[np.ndarray]:
        """
        Stop recording and return the audio as a numpy array.
        Returns None if no audio was captured.
        """
        if not self._is_recording:
            logger.warning("Not recording, ignoring stop request")
            return None

        self._is_recording = False

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        # Wait for the consumer thread to drain any audio chunks still sitting in the
        # queue — otherwise the last chunk(s) captured right before stop() can be lost,
        # cutting off the tail end of the recording.
        if self._consumer_thread:
            self._consumer_thread.join(timeout=1.0)
            self._consumer_thread = None

        with self._lock:
            if not self._audio_data:
                logger.warning("No audio data captured")
                return None

            # Flatten the list of numpy arrays
            audio_array = np.concatenate(self._audio_data, axis=0).flatten()
            duration = len(audio_array) / SAMPLE_RATE
            logger.info(f"[AUDIO] Recording stopped - {duration:.1f}s of audio captured")
            return audio_array

    @staticmethod
    def numpy_to_wav_bytes(audio_data: np.ndarray) -> bytes:
        """Convert numpy audio array to WAV bytes (for API upload)."""
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(SAMPLE_WIDTH)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_data.tobytes())
        return buffer.getvalue()

    @staticmethod
    def list_microphones() -> list[dict]:
        """List available microphone devices using sounddevice."""
        import sounddevice as sd
        devices = []
        try:
            for i, info in enumerate(sd.query_devices()):
                if info.get("max_input_channels", 0) > 0:
                    devices.append({
                        "index": i,
                        "name": info.get("name", f"Device {i}"),
                        "channels": info.get("max_input_channels", 0),
                        "sample_rate": int(info.get("default_samplerate", 0)),
                    })
        except Exception as e:
            logger.error(f"Failed to list devices: {e}")
            
        return devices
