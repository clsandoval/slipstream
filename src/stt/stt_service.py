"""Speech-to-Text service using Whisper."""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Literal, Optional

import numpy as np

from .log_manager import LogManager

# Whisper expects 16kHz audio
SAMPLE_RATE = 16000

# Supported backends
Backend = Literal["faster-whisper", "whisper-trt"]


def _detect_device() -> str:
    """Detect best available compute device."""
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    return "cpu"


@dataclass
class STTService:
    """Speech-to-Text transcription service.

    Continuously captures audio and transcribes it using Whisper,
    appending results to a transcript log.

    Supports two backends:
    - faster-whisper: CPU/CUDA, works everywhere (default)
    - whisper-trt: TensorRT optimized, Jetson/NVIDIA only (~3x faster)
    """

    model_name: str = "small.en"
    backend: Backend = "faster-whisper"
    device: str = "auto"
    chunk_duration: float = 3.0
    log_manager: LogManager = field(default_factory=LogManager)
    _model: Optional[Any] = field(default=None, init=False, repr=False)
    _running: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize the Whisper model."""
        if self.backend == "whisper-trt":
            from whisper_trt import load_trt_model
            self._model = load_trt_model(self.model_name)
        else:
            from faster_whisper import WhisperModel
            device = self.device if self.device != "auto" else _detect_device()
            self._model = WhisperModel(self.model_name, device=device)

    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio array to text.

        Args:
            audio: Audio samples as numpy array (float32, 16kHz mono).

        Returns:
            Transcribed text, or empty string if no speech detected.
        """
        if self._model is None:
            raise RuntimeError("Model not initialized")

        if self.backend == "whisper-trt":
            result = self._model.transcribe(audio)
            text = result.get("text", "").strip()
        else:
            segments, _ = self._model.transcribe(audio)
            texts = [seg.text for seg in segments]
            text = " ".join(texts).strip()

        # Return empty string if only whitespace
        if not text:
            return ""
        return text

    async def capture_chunk(self) -> np.ndarray:
        """Capture audio chunk from microphone.

        Returns:
            Audio samples as numpy array (float32, mono).
        """
        frames = int(self.chunk_duration * SAMPLE_RATE)

        # Run blocking audio recording in thread pool
        loop = asyncio.get_event_loop()
        audio = await loop.run_in_executor(
            None,
            lambda: self._record_audio(frames)
        )
        return audio

    def _record_audio(self, frames: int) -> np.ndarray:
        """Synchronous audio recording.

        Args:
            frames: Number of audio frames to record.

        Returns:
            Audio samples as numpy array.
        """
        import sounddevice as sd

        audio = sd.rec(frames, samplerate=SAMPLE_RATE, channels=1, dtype=np.float32)
        sd.wait()
        return audio.flatten()

    async def _process_one_chunk(self) -> None:
        """Process a single audio chunk: capture, transcribe, log."""
        audio = await self.capture_chunk()
        text = self.transcribe(audio)
        if text:
            self.log_manager.append(text)

    async def run(self) -> None:
        """Main daemon loop: continuously capture, transcribe, log."""
        self._running = True
        try:
            while self._running:
                await self._process_one_chunk()
                # Yield to allow stop() to take effect
                await asyncio.sleep(0)
        except asyncio.CancelledError:
            pass

    def stop(self) -> None:
        """Stop the service loop."""
        self._running = False
