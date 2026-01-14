"""Shared pytest fixtures for STT tests."""

import pytest
from pathlib import Path


@pytest.fixture
def temp_log_dir(tmp_path: Path) -> Path:
    """Temporary ~/.slipstream directory."""
    log_dir = tmp_path / ".slipstream"
    log_dir.mkdir()
    return log_dir


@pytest.fixture
def temp_log_path(temp_log_dir: Path) -> Path:
    """Path to temporary transcript.log file."""
    return temp_log_dir / "transcript.log"
