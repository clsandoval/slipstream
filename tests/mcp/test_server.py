"""Tests for MCP server."""

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio

from src.mcp.server import SwimCoachServer


class TestSwimCoachServer:
    """Tests for SwimCoachServer class."""

    @pytest.fixture
    def temp_config_dir(self, tmp_path: Path) -> Path:
        """Temporary config directory."""
        slipstream_dir = tmp_path / ".slipstream"
        slipstream_dir.mkdir()
        (slipstream_dir / "sessions").mkdir()
        return slipstream_dir

    def test_server_creation(self, temp_config_dir: Path) -> None:
        """Server creates with correct name."""
        server = SwimCoachServer(
            websocket_port=0,
            config_dir=temp_config_dir,
        )

        assert server.mcp.name == "swim-coach"

    def test_tools_registered(self, temp_config_dir: Path) -> None:
        """Session tools are registered."""
        server = SwimCoachServer(
            websocket_port=0,
            config_dir=temp_config_dir,
        )

        # Check tools are registered by listing them
        tool_names = list(server.mcp._tool_manager._tools.keys())
        assert "start_session" in tool_names
        assert "end_session" in tool_names
        assert "get_status" in tool_names

    @pytest.mark.asyncio
    async def test_tool_call_get_status(self, temp_config_dir: Path) -> None:
        """get_status tool returns valid response."""
        server = SwimCoachServer(
            websocket_port=0,
            config_dir=temp_config_dir,
        )

        # Call tool directly
        result = server._get_status()

        assert result["session_active"] is False
        assert "is_swimming" in result

    @pytest.mark.asyncio
    async def test_server_lifecycle(self, temp_config_dir: Path) -> None:
        """Server starts and stops cleanly."""
        server = SwimCoachServer(
            websocket_port=0,
            config_dir=temp_config_dir,
        )

        await server.start()
        assert server.websocket_server._server is not None

        await server.stop()
        assert server.websocket_server._server is None

    @pytest.mark.asyncio
    async def test_websocket_integration(self, temp_config_dir: Path) -> None:
        """WebSocket server runs when main server starts."""
        server = SwimCoachServer(
            websocket_port=0,
            config_dir=temp_config_dir,
        )

        await server.start()

        # WebSocket should be running
        assert server.websocket_server.port > 0
        assert server.websocket_server._running is True

        await server.stop()

    def test_error_handling_start_session_twice(
        self, temp_config_dir: Path
    ) -> None:
        """Starting session twice returns error, server continues."""
        server = SwimCoachServer(
            websocket_port=0,
            config_dir=temp_config_dir,
        )

        result1 = server._start_session()
        assert "session_id" in result1

        result2 = server._start_session()
        assert "error" in result2
        assert "already active" in result2["error"].lower()
