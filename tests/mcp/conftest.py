"""Test fixtures for MCP server tests."""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

from src.vision.state_store import SwimState
from src.mcp.storage.config import Config


@pytest.fixture
def temp_slipstream_dir(tmp_path: Path) -> Path:
    """Temporary ~/.slipstream directory."""
    slipstream_dir = tmp_path / ".slipstream"
    slipstream_dir.mkdir()
    (slipstream_dir / "sessions").mkdir()
    return slipstream_dir


@pytest.fixture
def config(temp_slipstream_dir: Path) -> Config:
    """Config with temporary directory."""
    return Config(
        dps_ratio=1.8,
        config_path=temp_slipstream_dir / "config.json",
    )


@pytest.fixture
def mock_vision_state_store() -> Mock:
    """Mock VisionStateStore with controllable state."""
    store = Mock()
    store.get_state.return_value = SwimState(
        session_active=True,
        session_start=datetime.now(),
        stroke_count=100,
        stroke_rate=54.0,
        rate_history=[],
        is_swimming=True,
        pose_detected=True,
    )
    return store


@pytest.fixture
def metric_bridge(mock_vision_state_store: Mock, config: Config):
    """MetricBridge with mock vision state."""
    from src.mcp.tools.metric_bridge import MetricBridge

    return MetricBridge(
        vision_state_store=mock_vision_state_store,
        config=config,
    )
