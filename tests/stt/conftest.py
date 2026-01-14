"""STT-specific pytest fixtures."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from src.stt.log_manager import LogManager


@pytest.fixture
def log_manager(temp_log_path: Path) -> LogManager:
    """LogManager with temp directory."""
    return LogManager(log_path=temp_log_path)


@pytest.fixture
def mock_whisper_model(mocker):
    """Mock WhisperModel for fast tests.

    Patches faster_whisper.WhisperModel before it's imported.
    """
    mock_segment = MagicMock()
    mock_segment.text = "hello world"

    # Patch faster_whisper.WhisperModel (used in runtime import)
    mock = mocker.patch("faster_whisper.WhisperModel")
    mock.return_value.transcribe.return_value = (
        [mock_segment],
        None,
    )
    return mock
