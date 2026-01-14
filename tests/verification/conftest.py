"""Shared fixtures for verification tests."""

import pytest
from pathlib import Path


@pytest.fixture
def tmp_config_dir(tmp_path: Path) -> Path:
    """Create temporary config directory."""
    config_dir = tmp_path / ".slipstream-test"
    config_dir.mkdir(parents=True)
    (config_dir / "sessions").mkdir()
    return config_dir
