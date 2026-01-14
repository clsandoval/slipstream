"""Tests for MCP message models."""

import json
from datetime import datetime, timezone

import pytest
from freezegun import freeze_time

from src.mcp.models.messages import SessionState, SystemState, StateUpdate


class TestSessionState:
    """Tests for SessionState dataclass."""

    def test_session_state_defaults(self) -> None:
        """SessionState has correct default values."""
        state = SessionState()

        assert state.active is False
        assert state.elapsed_seconds == 0
        assert state.stroke_count == 0
        assert state.stroke_rate == 0.0
        assert state.stroke_rate_trend == "stable"
        assert state.estimated_distance_m == 0.0

    def test_session_state_custom_values(self) -> None:
        """SessionState accepts custom values."""
        state = SessionState(
            active=True,
            elapsed_seconds=120,
            stroke_count=50,
            stroke_rate=52.5,
            stroke_rate_trend="increasing",
            estimated_distance_m=75.0,
        )

        assert state.active is True
        assert state.elapsed_seconds == 120
        assert state.stroke_count == 50
        assert state.stroke_rate == 52.5
        assert state.stroke_rate_trend == "increasing"
        assert state.estimated_distance_m == 75.0

    def test_session_state_to_dict(self) -> None:
        """SessionState converts to dict correctly."""
        state = SessionState(active=True, stroke_count=10)
        d = state.to_dict()

        assert d["active"] is True
        assert d["stroke_count"] == 10
        assert d["elapsed_seconds"] == 0


class TestSystemState:
    """Tests for SystemState dataclass."""

    def test_system_state_defaults(self) -> None:
        """SystemState has correct default values."""
        state = SystemState()

        assert state.is_swimming is False
        assert state.pose_detected is False
        assert state.voice_state == "idle"

    def test_system_state_custom_values(self) -> None:
        """SystemState accepts custom values."""
        state = SystemState(
            is_swimming=True,
            pose_detected=True,
            voice_state="listening",
        )

        assert state.is_swimming is True
        assert state.pose_detected is True
        assert state.voice_state == "listening"

    def test_system_state_to_dict(self) -> None:
        """SystemState converts to dict correctly."""
        state = SystemState(is_swimming=True, voice_state="speaking")
        d = state.to_dict()

        assert d["is_swimming"] is True
        assert d["voice_state"] == "speaking"


class TestStateUpdate:
    """Tests for StateUpdate dataclass."""

    @freeze_time("2026-01-14T08:30:00Z")
    def test_state_update_to_json(self) -> None:
        """StateUpdate serializes to valid JSON with ISO timestamp."""
        update = StateUpdate(
            session=SessionState(active=True, stroke_count=42),
            system=SystemState(is_swimming=True),
        )

        json_str = update.to_json()
        parsed = json.loads(json_str)

        assert parsed["type"] == "state_update"
        assert parsed["timestamp"] == "2026-01-14T08:30:00+00:00"
        assert parsed["session"]["active"] is True
        assert parsed["session"]["stroke_count"] == 42
        assert parsed["system"]["is_swimming"] is True

    def test_state_update_from_dict(self) -> None:
        """StateUpdate creates from dict correctly."""
        data = {
            "type": "state_update",
            "timestamp": "2026-01-14T08:30:00+00:00",
            "session": {
                "active": True,
                "elapsed_seconds": 165,
                "stroke_count": 142,
                "stroke_rate": 52.0,
                "stroke_rate_trend": "stable",
                "estimated_distance_m": 213.0,
            },
            "system": {
                "is_swimming": True,
                "pose_detected": True,
                "voice_state": "listening",
            },
        }

        update = StateUpdate.from_dict(data)

        assert update.type == "state_update"
        assert update.timestamp == "2026-01-14T08:30:00+00:00"
        assert update.session.active is True
        assert update.session.stroke_count == 142
        assert update.system.is_swimming is True
        assert update.system.voice_state == "listening"

    def test_state_update_defaults(self) -> None:
        """StateUpdate has correct default values."""
        update = StateUpdate()

        assert update.type == "state_update"
        assert update.session.active is False
        assert update.system.is_swimming is False

    def test_state_update_timestamp_format(self) -> None:
        """StateUpdate timestamp is ISO format."""
        update = StateUpdate()

        # Should be parseable as ISO datetime
        datetime.fromisoformat(update.timestamp)
