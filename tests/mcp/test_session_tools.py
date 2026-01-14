"""Tests for session management MCP tools."""

from pathlib import Path

import pytest
from freezegun import freeze_time

from src.mcp.state_store import StateStore, SessionActiveError, NoActiveSessionError
from src.mcp.storage.session_storage import SessionStorage
from src.mcp.tools.session_tools import create_session_tools


class TestSessionTools:
    """Tests for session management tools."""

    @pytest.fixture
    def storage(self, temp_slipstream_dir: Path) -> SessionStorage:
        """SessionStorage with temp directory."""
        return SessionStorage(sessions_dir=temp_slipstream_dir / "sessions")

    @pytest.fixture
    def state_store(self) -> StateStore:
        """Fresh StateStore instance."""
        return StateStore()

    @pytest.fixture
    def tools(
        self, state_store: StateStore, storage: SessionStorage
    ) -> dict:
        """Session tools dict."""
        tool_list = create_session_tools(state_store, storage)
        return {fn.__name__: fn for fn in tool_list}

    @freeze_time("2026-01-14T08:30:00Z")
    def test_start_session_tool(
        self, tools: dict, state_store: StateStore
    ) -> None:
        """start_session returns session_id and started_at."""
        result = tools["start_session"]()

        assert result["session_id"] == "2026-01-14_0830"
        assert result["started_at"] == "2026-01-14T08:30:00+00:00"
        assert state_store.session.active is True

    def test_start_session_already_active(
        self, tools: dict, state_store: StateStore
    ) -> None:
        """start_session returns error when session is active."""
        tools["start_session"]()
        result = tools["start_session"]()

        assert "error" in result
        assert "already active" in result["error"].lower()

    def test_end_session_tool(
        self, tools: dict, state_store: StateStore
    ) -> None:
        """end_session returns summary with stroke data."""
        tools["start_session"]()
        state_store.update_strokes(count=50, rate=52.5)

        result = tools["end_session"]()

        assert "summary" in result
        assert result["summary"]["stroke_count"] == 50
        assert "duration_seconds" in result["summary"]
        assert state_store.session.active is False

    def test_end_session_not_active(self, tools: dict) -> None:
        """end_session returns error when no session active."""
        result = tools["end_session"]()

        assert "error" in result
        assert "no active session" in result["error"].lower()

    def test_get_status_tool(
        self, tools: dict, state_store: StateStore
    ) -> None:
        """get_status returns full status dict."""
        tools["start_session"]()
        state_store.update_strokes(count=42, rate=50.0)
        state_store.update_system(is_swimming=True, pose_detected=True)

        result = tools["get_status"]()

        assert result["session_active"] is True
        assert result["stroke_count"] == 42
        assert result["stroke_rate"] == 50.0
        assert result["is_swimming"] is True
        assert result["pose_detected"] is True

    def test_get_status_idle(self, tools: dict) -> None:
        """get_status shows inactive state when no session."""
        result = tools["get_status"]()

        assert result["session_active"] is False
        assert result["stroke_count"] == 0

    def test_session_persisted_to_storage(
        self, tools: dict, storage: SessionStorage, state_store: StateStore
    ) -> None:
        """Session data persisted to storage after end."""
        result = tools["start_session"]()
        session_id = result["session_id"]
        state_store.update_strokes(count=100, rate=55.0)
        tools["end_session"]()

        # Check storage
        stored = storage.get_session(session_id)
        assert stored is not None
        assert stored["stroke_count"] == 100
