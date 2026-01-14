"""Test fixtures for notifications tests."""

import json

import pytest


@pytest.fixture
def temp_slipstream_dir(tmp_path):
    """Temporary ~/.slipstream directory."""
    slipstream_dir = tmp_path / ".slipstream"
    slipstream_dir.mkdir()
    return slipstream_dir


@pytest.fixture
def config_with_telegram(temp_slipstream_dir):
    """Config with telegram enabled."""
    config_path = temp_slipstream_dir / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "dps_ratio": 1.8,
                "telegram": {
                    "bot_token": "123456:ABC-DEF-test",
                    "chat_id": "987654321",
                    "enabled": True,
                },
            }
        )
    )
    return config_path


@pytest.fixture
def sample_session():
    """Sample completed session."""
    return {
        "session_id": "2024-01-15_1430",
        "started_at": "2024-01-15T14:30:00+00:00",
        "ended_at": "2024-01-15T15:02:14+00:00",
        "stroke_count": 842,
        "stroke_rate_avg": 53.2,
        "duration_seconds": 1934,
        "estimated_distance_m": 1515.6,
    }
