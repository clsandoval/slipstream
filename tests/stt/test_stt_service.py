"""Tests for STTService - Whisper transcription service."""

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

import numpy as np
import pytest

from src.stt.stt_service import STTService
from src.stt.log_manager import LogManager


class TestTranscribe:
    """Tests for transcription functionality."""

    def test_transcribe_audio(self, mock_whisper_model):
        """Transcribes audio array to text."""
        service = STTService(model_name="small")

        # Create sample audio (1 second at 16kHz)
        audio = np.random.randn(16000).astype(np.float32)
        result = service.transcribe(audio)

        assert result == "hello world"
        mock_whisper_model.return_value.transcribe.assert_called_once()

    def test_transcribe_silence(self, mock_whisper_model):
        """Silent audio returns empty string."""
        # Configure mock to return empty segments
        mock_whisper_model.return_value.transcribe.return_value = ([], None)

        service = STTService(model_name="small")
        audio = np.zeros(16000, dtype=np.float32)
        result = service.transcribe(audio)

        assert result == ""

    def test_transcribe_whitespace_only(self, mock_whisper_model):
        """Whitespace-only transcription returns empty string."""
        mock_segment = MagicMock()
        mock_segment.text = "   "
        mock_whisper_model.return_value.transcribe.return_value = ([mock_segment], None)

        service = STTService(model_name="small")
        audio = np.random.randn(16000).astype(np.float32)
        result = service.transcribe(audio)

        assert result == ""


class TestModelLoading:
    """Tests for model initialization."""

    def test_model_loads(self, mock_whisper_model):
        """Model loads successfully with valid name."""
        service = STTService(model_name="small")

        mock_whisper_model.assert_called_once()
        call_args = mock_whisper_model.call_args
        assert call_args[0][0] == "small"

    def test_model_auto_device(self, mock_whisper_model):
        """Auto device selection uses cuda if available."""
        service = STTService(model_name="small", device="auto")

        mock_whisper_model.assert_called_once()
        # Device should be determined based on availability
        call_kwargs = mock_whisper_model.call_args[1]
        assert "device" in call_kwargs

    def test_model_specific_device(self, mock_whisper_model):
        """Specific device is passed to model."""
        service = STTService(model_name="small", device="cpu")

        call_kwargs = mock_whisper_model.call_args[1]
        assert call_kwargs["device"] == "cpu"

    def test_auto_device_with_cuda(self, mock_whisper_model, mocker):
        """Auto device uses CUDA when available."""
        # Mock torch.cuda.is_available to return True
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        mocker.patch.dict("sys.modules", {"torch": mock_torch})

        # Need to reimport to pick up the mock
        from src.stt.stt_service import _detect_device
        device = _detect_device()

        assert device == "cuda"

    def test_auto_device_without_torch(self, mock_whisper_model, mocker):
        """Auto device falls back to CPU when torch not available."""
        # Mock torch import to raise ImportError
        def raise_import_error():
            raise ImportError("No module named 'torch'")

        mocker.patch.dict("sys.modules", {"torch": None})

        from src.stt.stt_service import _detect_device
        device = _detect_device()

        assert device == "cpu"


class TestServiceLoop:
    """Tests for the main service loop."""

    @pytest.mark.asyncio
    async def test_service_writes_to_log(self, mock_whisper_model, temp_log_path: Path):
        """Service writes transcriptions to log file."""
        log_manager = LogManager(log_path=temp_log_path)
        service = STTService(model_name="small", log_manager=log_manager)

        # Mock capture_chunk to return audio once then stop
        audio = np.random.randn(16000).astype(np.float32)
        service.capture_chunk = AsyncMock(return_value=audio)

        # Run one iteration
        await service._process_one_chunk()

        content = temp_log_path.read_text()
        assert "hello world" in content

    @pytest.mark.asyncio
    async def test_skip_empty_transcriptions(self, mock_whisper_model, temp_log_path: Path):
        """Empty transcriptions are not written to log."""
        mock_whisper_model.return_value.transcribe.return_value = ([], None)

        log_manager = LogManager(log_path=temp_log_path)
        service = STTService(model_name="small", log_manager=log_manager)

        audio = np.zeros(16000, dtype=np.float32)
        service.capture_chunk = AsyncMock(return_value=audio)

        await service._process_one_chunk()

        assert not temp_log_path.exists() or temp_log_path.read_text() == ""

    @pytest.mark.asyncio
    async def test_continuous_loop(self, mock_whisper_model, temp_log_path: Path):
        """Service processes multiple chunks in sequence."""
        # Return different text for each call
        responses = [
            ([MagicMock(text="one")], None),
            ([MagicMock(text="two")], None),
            ([MagicMock(text="three")], None),
        ]
        mock_whisper_model.return_value.transcribe.side_effect = responses

        log_manager = LogManager(log_path=temp_log_path)
        service = STTService(model_name="small", log_manager=log_manager)

        audio = np.random.randn(16000).astype(np.float32)
        service.capture_chunk = AsyncMock(return_value=audio)

        # Process 3 chunks
        for _ in range(3):
            await service._process_one_chunk()

        content = temp_log_path.read_text()
        assert "one" in content
        assert "two" in content
        assert "three" in content


class TestAudioCapture:
    """Tests for audio capture functionality."""

    @pytest.mark.asyncio
    async def test_capture_chunk_returns_array(self, mock_whisper_model):
        """Capture chunk returns numpy array."""
        service = STTService(model_name="small", chunk_duration=0.1)

        # Mock the internal _record_audio method
        expected_audio = np.zeros(1600, dtype=np.float32)
        service._record_audio = MagicMock(return_value=expected_audio)

        audio = await service.capture_chunk()

        assert isinstance(audio, np.ndarray)
        assert audio.dtype == np.float32

    @pytest.mark.asyncio
    async def test_capture_chunk_duration(self, mock_whisper_model):
        """Capture chunk uses configured duration."""
        service = STTService(model_name="small", chunk_duration=3.0)

        # Mock the internal _record_audio method
        expected_audio = np.zeros(48000, dtype=np.float32)
        service._record_audio = MagicMock(return_value=expected_audio)

        await service.capture_chunk()

        # Check frames = duration * sample_rate (16000 Hz)
        call_args = service._record_audio.call_args
        assert call_args[0][0] == 48000  # 3.0 * 16000


class TestServiceRun:
    """Tests for run method."""

    @pytest.mark.asyncio
    async def test_run_can_be_stopped(self, mock_whisper_model, temp_log_path: Path):
        """Service run loop can be stopped gracefully."""
        log_manager = LogManager(log_path=temp_log_path)
        service = STTService(model_name="small", log_manager=log_manager)

        audio = np.random.randn(16000).astype(np.float32)
        service.capture_chunk = AsyncMock(return_value=audio)

        # Start run in background
        task = asyncio.create_task(service.run())

        # Let it run briefly then stop
        await asyncio.sleep(0.05)
        service.stop()

        # Wait for clean shutdown
        await asyncio.wait_for(task, timeout=1.0)

        # Should have logged at least one entry
        assert temp_log_path.exists()

    @pytest.mark.asyncio
    async def test_run_handles_cancellation(self, mock_whisper_model, temp_log_path: Path):
        """Service handles task cancellation gracefully."""
        log_manager = LogManager(log_path=temp_log_path)
        service = STTService(model_name="small", log_manager=log_manager)

        audio = np.random.randn(16000).astype(np.float32)
        service.capture_chunk = AsyncMock(return_value=audio)

        # Start run in background
        task = asyncio.create_task(service.run())

        # Let it run briefly
        await asyncio.sleep(0.02)

        # Cancel the task
        task.cancel()

        # Should handle cancellation without raising
        try:
            await task
        except asyncio.CancelledError:
            pass  # Expected
