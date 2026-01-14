"""Integration tests for MCP server."""

import asyncio
import json
from pathlib import Path

import pytest
import pytest_asyncio
import websockets

from src.mcp.server import SwimCoachServer


class TestIntegration:
    """End-to-end integration tests."""

    @pytest.fixture
    def temp_config_dir(self, tmp_path: Path) -> Path:
        """Temporary config directory."""
        slipstream_dir = tmp_path / ".slipstream"
        slipstream_dir.mkdir()
        (slipstream_dir / "sessions").mkdir()
        return slipstream_dir

    @pytest_asyncio.fixture
    async def server(self, temp_config_dir: Path):
        """Running server for integration tests."""
        srv = SwimCoachServer(
            websocket_port=0,
            push_interval=0.1,
            config_dir=temp_config_dir,
        )
        await srv.start()
        yield srv
        await srv.stop()

    @pytest.mark.asyncio
    async def test_full_session_lifecycle(
        self, server: SwimCoachServer, temp_config_dir: Path
    ) -> None:
        """Full session: start, update strokes, end."""
        # Start session
        result = server._start_session()
        assert "session_id" in result
        session_id = result["session_id"]

        # Simulate stroke updates
        server.state_store.update_strokes(count=50, rate=52.0)
        server.state_store.update_strokes(count=100, rate=54.0)
        server.state_store.update_strokes(count=150, rate=53.0)

        # End session
        end_result = server._end_session()
        assert "summary" in end_result
        assert end_result["summary"]["stroke_count"] == 150

        # Verify session saved
        session_file = temp_config_dir / "sessions" / f"{session_id}.json"
        assert session_file.exists()

        saved = json.loads(session_file.read_text())
        assert saved["stroke_count"] == 150
        assert saved["ended_at"] is not None

    @pytest.mark.asyncio
    async def test_websocket_receives_session_updates(
        self, server: SwimCoachServer
    ) -> None:
        """WebSocket client receives state when session starts."""
        async with websockets.connect(
            f"ws://localhost:{server.websocket_server.port}"
        ) as ws:
            # Get initial state
            msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
            data = json.loads(msg)
            assert data["session"]["active"] is False

            # Start session
            server._start_session()

            # Get updated state
            msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
            data = json.loads(msg)
            assert data["session"]["active"] is True

    @pytest.mark.asyncio
    async def test_multiple_tool_calls(self, server: SwimCoachServer) -> None:
        """Rapid tool calls handled correctly."""
        # Multiple status checks
        for _ in range(10):
            result = server._get_status()
            assert "session_active" in result

        # Start and end multiple sessions
        for i in range(3):
            start = server._start_session()
            assert "session_id" in start

            server.state_store.update_strokes(count=i * 10, rate=50.0)

            end = server._end_session()
            assert "summary" in end

    @pytest.mark.asyncio
    async def test_persistence_after_session(
        self, server: SwimCoachServer, temp_config_dir: Path
    ) -> None:
        """Session data persists after ending."""
        # Complete a session
        start = server._start_session()
        session_id = start["session_id"]
        server.state_store.update_strokes(count=75, rate=51.0)
        server._end_session()

        # Read directly from storage
        session_file = temp_config_dir / "sessions" / f"{session_id}.json"
        stored = json.loads(session_file.read_text())

        assert stored["stroke_count"] == 75
        assert stored["ended_at"] is not None
        assert stored["duration_seconds"] >= 0

    @pytest.mark.asyncio
    async def test_config_used_correctly(
        self, temp_config_dir: Path
    ) -> None:
        """Server uses config values correctly."""
        # Write custom config
        config_file = temp_config_dir / "config.json"
        config_file.write_text(json.dumps({
            "dps_ratio": 2.5,
            "notifications": {
                "telegram_enabled": False,
                "telegram_chat_id": None,
                "sms_enabled": False,
                "sms_phone": None,
            }
        }))

        # Create server with this config
        srv = SwimCoachServer(
            websocket_port=0,
            config_dir=temp_config_dir,
        )

        # Start session and check DPS calculation
        srv._start_session()
        srv.state_store.update_strokes(count=100, rate=50.0)

        status = srv._get_status()
        # 100 strokes * 2.5 DPS = 250m
        assert status["estimated_distance_m"] == pytest.approx(250.0)

    @pytest.mark.asyncio
    async def test_websocket_stroke_updates(
        self, server: SwimCoachServer
    ) -> None:
        """WebSocket shows stroke count updates."""
        server._start_session()

        async with websockets.connect(
            f"ws://localhost:{server.websocket_server.port}"
        ) as ws:
            # Skip initial message
            await asyncio.wait_for(ws.recv(), timeout=1.0)

            # Update strokes
            server.state_store.update_strokes(count=42, rate=52.0)

            # Wait for next push
            msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
            data = json.loads(msg)

            assert data["session"]["stroke_count"] == 42
            assert data["session"]["stroke_rate"] == 52.0
