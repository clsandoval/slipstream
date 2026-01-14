"""Tests for session storage."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from freezegun import freeze_time

from src.mcp.storage.session_storage import SessionStorage


class TestSessionStorage:
    """Tests for SessionStorage class."""

    @pytest.fixture
    def storage(self, temp_slipstream_dir: Path) -> SessionStorage:
        """SessionStorage with temp directory."""
        return SessionStorage(sessions_dir=temp_slipstream_dir / "sessions")

    @freeze_time("2026-01-14T08:30:00Z")
    def test_create_session(self, storage: SessionStorage) -> None:
        """Create a new session file."""
        session_id = "2026-01-14_0830"
        started_at = datetime.now(timezone.utc)

        result = storage.create_session(session_id, started_at)

        assert result["session_id"] == session_id
        assert result["started_at"] == "2026-01-14T08:30:00+00:00"
        assert result["ended_at"] is None
        assert result["stroke_count"] == 0
        assert result["duration_seconds"] == 0

        # File should exist
        session_path = storage.sessions_dir / f"{session_id}.json"
        assert session_path.exists()

    def test_get_session(self, storage: SessionStorage) -> None:
        """Get existing session by ID."""
        session_id = "2026-01-14_0830"
        session_data = {
            "session_id": session_id,
            "started_at": "2026-01-14T08:30:00+00:00",
            "ended_at": None,
            "stroke_count": 50,
            "stroke_rate_avg": 52.5,
            "duration_seconds": 300,
        }
        session_path = storage.sessions_dir / f"{session_id}.json"
        session_path.write_text(json.dumps(session_data))

        result = storage.get_session(session_id)

        assert result is not None
        assert result["session_id"] == session_id
        assert result["stroke_count"] == 50

    def test_update_session(self, storage: SessionStorage) -> None:
        """Update existing session."""
        session_id = "2026-01-14_0830"
        session_data = {
            "session_id": session_id,
            "started_at": "2026-01-14T08:30:00+00:00",
            "stroke_count": 10,
        }
        session_path = storage.sessions_dir / f"{session_id}.json"
        session_path.write_text(json.dumps(session_data))

        storage.update_session(session_id, {"stroke_count": 50, "stroke_rate_avg": 52.5})

        updated = json.loads(session_path.read_text())
        assert updated["stroke_count"] == 50
        assert updated["stroke_rate_avg"] == 52.5
        assert updated["started_at"] == "2026-01-14T08:30:00+00:00"

    def test_list_sessions(self, storage: SessionStorage) -> None:
        """List sessions sorted by date (newest first)."""
        # Create several session files
        for date in ["2026-01-12_0800", "2026-01-14_0830", "2026-01-13_0900"]:
            session_path = storage.sessions_dir / f"{date}.json"
            session_path.write_text(json.dumps({"session_id": date}))

        sessions = storage.list_sessions()

        assert len(sessions) == 3
        assert sessions[0]["session_id"] == "2026-01-14_0830"
        assert sessions[1]["session_id"] == "2026-01-13_0900"
        assert sessions[2]["session_id"] == "2026-01-12_0800"

    def test_list_sessions_with_limit(self, storage: SessionStorage) -> None:
        """List sessions with limit."""
        for date in ["2026-01-12_0800", "2026-01-14_0830", "2026-01-13_0900"]:
            session_path = storage.sessions_dir / f"{date}.json"
            session_path.write_text(json.dumps({"session_id": date}))

        sessions = storage.list_sessions(limit=2)

        assert len(sessions) == 2

    def test_session_not_found(self, storage: SessionStorage) -> None:
        """Get returns None for non-existent session."""
        result = storage.get_session("nonexistent")
        assert result is None

    def test_creates_sessions_dir(self, tmp_path: Path) -> None:
        """Creates sessions directory if it doesn't exist."""
        sessions_dir = tmp_path / "new_dir" / "sessions"
        storage = SessionStorage(sessions_dir=sessions_dir)
        assert not sessions_dir.exists()

        storage.create_session("test", datetime.now(timezone.utc))

        assert sessions_dir.exists()

    @freeze_time("2026-01-14T08:30:00Z")
    def test_session_filename_format(self, storage: SessionStorage) -> None:
        """Session filename matches expected format."""
        session_id = storage.generate_session_id()

        assert session_id == "2026-01-14_0830"

    def test_delete_session(self, storage: SessionStorage) -> None:
        """Delete existing session."""
        session_id = "2026-01-14_0830"
        session_path = storage.sessions_dir / f"{session_id}.json"
        session_path.write_text(json.dumps({"session_id": session_id}))
        assert session_path.exists()

        result = storage.delete_session(session_id)

        assert result is True
        assert not session_path.exists()

    def test_delete_session_not_found(self, storage: SessionStorage) -> None:
        """Delete returns False for non-existent session."""
        result = storage.delete_session("nonexistent")
        assert result is False
