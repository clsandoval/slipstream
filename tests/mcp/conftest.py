"""Test fixtures for MCP server tests."""

import pytest
from pathlib import Path


@pytest.fixture
def temp_slipstream_dir(tmp_path: Path) -> Path:
    """Temporary ~/.slipstream directory."""
    slipstream_dir = tmp_path / ".slipstream"
    slipstream_dir.mkdir()
    (slipstream_dir / "sessions").mkdir()
    return slipstream_dir
