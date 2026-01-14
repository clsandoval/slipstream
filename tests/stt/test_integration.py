"""Integration tests for STT service - end-to-end testing."""

import os
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest
from freezegun import freeze_time

from src.stt.log_manager import LogManager
from src.stt.stt_service import STTService


class TestFullTranscriptionLoop:
    """End-to-end tests for transcription pipeline."""

    def test_transcribe_known_audio(self, mock_whisper_model, temp_log_path: Path):
        """Full pipeline: audio -> transcribe -> log."""
        # Configure mock to return specific text
        mock_segment = MagicMock()
        mock_segment.text = "start a new session"
        mock_whisper_model.return_value.transcribe.return_value = ([mock_segment], None)

        log_manager = LogManager(log_path=temp_log_path)
        service = STTService(model_name="small", log_manager=log_manager)

        # Simulate processing audio
        audio = np.random.randn(16000).astype(np.float32)
        text = service.transcribe(audio)
        if text:
            log_manager.append(text)

        # Verify log contains the text
        content = temp_log_path.read_text()
        assert "start a new session" in content

        # Verify timestamp format
        lines = content.strip().split("\n")
        timestamp_part = lines[0].split(" ")[0]
        datetime.fromisoformat(timestamp_part)

    def test_multiple_transcriptions_in_sequence(self, mock_whisper_model, temp_log_path: Path):
        """Multiple transcriptions are logged in order."""
        log_manager = LogManager(log_path=temp_log_path)
        service = STTService(model_name="small", log_manager=log_manager)

        # Simulate sequence of transcriptions
        phrases = [
            "what's my current stroke rate",
            "how many laps have I done",
            "start a new workout",
        ]

        for phrase in phrases:
            mock_segment = MagicMock()
            mock_segment.text = phrase
            mock_whisper_model.return_value.transcribe.return_value = ([mock_segment], None)

            audio = np.random.randn(16000).astype(np.float32)
            text = service.transcribe(audio)
            if text:
                log_manager.append(text)

        # Verify all phrases are logged in order
        content = temp_log_path.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 3

        for i, phrase in enumerate(phrases):
            assert phrase in lines[i]


class TestLogRotationDuringOperation:
    """Tests for log rotation during service operation."""

    @freeze_time("2026-01-11 08:00:00")
    def test_rotation_during_operation(self, mock_whisper_model, temp_log_dir: Path):
        """Log rotates without losing entries during operation."""
        log_path = temp_log_dir / "transcript.log"
        log_manager = LogManager(log_path=log_path)
        service = STTService(model_name="small", log_manager=log_manager)

        # Write entry and set mtime to yesterday
        mock_segment = MagicMock()
        mock_segment.text = "yesterday's entry"
        mock_whisper_model.return_value.transcribe.return_value = ([mock_segment], None)

        audio = np.random.randn(16000).astype(np.float32)
        text = service.transcribe(audio)
        log_manager.append(text)

        # Set file mtime to yesterday
        yesterday_ts = datetime(2026, 1, 10, 8, 0, 0).timestamp()
        os.utime(log_path, (yesterday_ts, yesterday_ts))

        # Rotate logs
        log_manager.rotate_if_needed()

        # Write new entry
        mock_segment.text = "today's entry"
        text = service.transcribe(audio)
        log_manager.append(text)

        # Verify rotation happened
        rotated_file = temp_log_dir / "transcript.2026-01-10.log"
        assert rotated_file.exists()
        assert "yesterday's entry" in rotated_file.read_text()

        # Verify new entry in current log
        assert log_path.exists()
        assert "today's entry" in log_path.read_text()

    def test_cleanup_during_operation(self, mock_whisper_model, temp_log_dir: Path):
        """Old logs are cleaned up without affecting current operation."""
        import time

        log_path = temp_log_dir / "transcript.log"
        log_manager = LogManager(log_path=log_path)
        service = STTService(model_name="small", log_manager=log_manager)

        # Create old log file
        old_log = temp_log_dir / "transcript.2026-01-01.log"
        old_log.write_text("very old entry")
        old_time = time.time() - (10 * 24 * 60 * 60)  # 10 days ago
        os.utime(old_log, (old_time, old_time))

        # Write current entry
        mock_segment = MagicMock()
        mock_segment.text = "current entry"
        mock_whisper_model.return_value.transcribe.return_value = ([mock_segment], None)

        audio = np.random.randn(16000).astype(np.float32)
        text = service.transcribe(audio)
        log_manager.append(text)

        # Run cleanup
        log_manager.cleanup_old_logs(retention_days=7)

        # Verify old log deleted
        assert not old_log.exists()

        # Verify current log intact
        assert log_path.exists()
        assert "current entry" in log_path.read_text()


class TestServiceLifecycle:
    """Tests for service start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_service_starts_and_stops_cleanly(self, mock_whisper_model, temp_log_path: Path):
        """Service can start, process, and stop without errors."""
        import asyncio
        from unittest.mock import AsyncMock

        log_manager = LogManager(log_path=temp_log_path)
        service = STTService(model_name="small", log_manager=log_manager)

        # Mock audio capture
        audio = np.random.randn(16000).astype(np.float32)
        service.capture_chunk = AsyncMock(return_value=audio)

        # Start service
        task = asyncio.create_task(service.run())

        # Let it process a few chunks
        await asyncio.sleep(0.1)

        # Stop service
        service.stop()
        await asyncio.wait_for(task, timeout=1.0)

        # Verify service logged entries
        assert temp_log_path.exists()
        content = temp_log_path.read_text()
        assert "hello world" in content  # Default mock response
