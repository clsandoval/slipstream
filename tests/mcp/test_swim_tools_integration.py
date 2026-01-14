"""Integration tests for swim tools with MCP server."""

import pytest
from pathlib import Path
from unittest.mock import Mock

from src.vision.state_store import SwimState, StateStore as VisionStateStore
from src.vision.rate_calculator import RateSample


class TestSwimToolsServerIntegration:
    """Test swim tools registration with MCP server."""

    @pytest.fixture
    def mock_vision_store(self):
        """Mock vision state store."""
        store = Mock(spec=VisionStateStore)
        store.get_state.return_value = SwimState(
            session_active=True,
            stroke_count=100,
            stroke_rate=54.0,
            is_swimming=True,
        )
        return store

    @pytest.fixture
    def server_with_swim_tools(self, temp_slipstream_dir: Path, mock_vision_store):
        """SwimCoachServer with swim tools registered."""
        from src.mcp.server import SwimCoachServer

        server = SwimCoachServer(
            websocket_port=0,
            config_dir=temp_slipstream_dir,
            vision_state_store=mock_vision_store,
        )
        return server

    def test_swim_tools_registered(self, server_with_swim_tools):
        """Swim tools are registered on server."""
        tool_names = list(server_with_swim_tools.mcp._tool_manager._tools.keys())

        assert "get_stroke_rate" in tool_names
        assert "get_stroke_count" in tool_names
        assert "get_session_time" in tool_names

    def test_session_tools_still_registered(self, server_with_swim_tools):
        """Session tools remain registered alongside swim tools."""
        tool_names = list(server_with_swim_tools.mcp._tool_manager._tools.keys())

        assert "start_session" in tool_names
        assert "end_session" in tool_names
        assert "get_status" in tool_names

    def test_tool_call_get_stroke_rate(self, server_with_swim_tools):
        """get_stroke_rate tool returns valid response."""
        result = server_with_swim_tools._get_stroke_rate()

        assert "rate" in result
        assert result["rate"] == 54.0
        assert "trend" in result
        assert "window_seconds" in result

    def test_tool_call_get_stroke_count(self, server_with_swim_tools):
        """get_stroke_count tool returns valid response."""
        result = server_with_swim_tools._get_stroke_count()

        assert "count" in result
        assert result["count"] == 100
        assert "estimated_distance_m" in result

    def test_tool_call_get_session_time(self, server_with_swim_tools):
        """get_session_time tool returns valid response."""
        result = server_with_swim_tools._get_session_time()

        assert "elapsed_seconds" in result
        assert "formatted" in result

    def test_swim_and_session_tools_together(self, server_with_swim_tools, mock_vision_store):
        """Swim and session tools work correctly together."""
        # Start session via session tool
        result1 = server_with_swim_tools._start_session()
        assert "session_id" in result1

        # Get swim metrics
        rate_result = server_with_swim_tools._get_stroke_rate()
        assert rate_result["rate"] == 54.0

        count_result = server_with_swim_tools._get_stroke_count()
        assert count_result["count"] == 100

    def test_vision_state_propagation(self, server_with_swim_tools, mock_vision_store):
        """Vision state updates propagate to swim tools."""
        # Initially mock returns 100 strokes
        result1 = server_with_swim_tools._get_stroke_count()
        assert result1["count"] == 100

        # Update mock to return new count
        mock_vision_store.get_state.return_value = SwimState(
            session_active=True,
            stroke_count=150,
            stroke_rate=56.0,
            is_swimming=True,
        )

        result2 = server_with_swim_tools._get_stroke_count()
        assert result2["count"] == 150

    def test_distance_uses_config_dps_ratio(self, server_with_swim_tools):
        """Distance calculation uses config DPS ratio."""
        # Default dps_ratio is 1.8, count is 100
        result = server_with_swim_tools._get_stroke_count()

        assert result["estimated_distance_m"] == 180.0

    def test_trend_calculation(self, server_with_swim_tools, mock_vision_store):
        """Trend calculated correctly from rate history."""
        mock_vision_store.get_state.return_value = SwimState(
            session_active=True,
            stroke_rate=58.0,
            rate_history=[
                RateSample(timestamp=0.0, rate=50.0),
                RateSample(timestamp=5.0, rate=52.0),
                RateSample(timestamp=10.0, rate=55.0),
                RateSample(timestamp=15.0, rate=58.0),
            ],
            is_swimming=True,
        )

        result = server_with_swim_tools._get_stroke_rate()

        assert result["trend"] == "increasing"


class TestSwimToolsServerLifecycle:
    """Test swim tools with server lifecycle."""

    @pytest.fixture
    def mock_vision_store(self):
        """Mock vision state store."""
        store = Mock(spec=VisionStateStore)
        store.get_state.return_value = SwimState()
        return store

    @pytest.mark.asyncio
    async def test_server_with_swim_tools_lifecycle(
        self, temp_slipstream_dir: Path, mock_vision_store
    ):
        """Server with swim tools starts and stops cleanly."""
        from src.mcp.server import SwimCoachServer

        server = SwimCoachServer(
            websocket_port=0,
            config_dir=temp_slipstream_dir,
            vision_state_store=mock_vision_store,
        )

        await server.start()
        assert server.websocket_server._server is not None

        # Swim tools should work while server is running
        result = server._get_stroke_rate()
        assert "rate" in result

        await server.stop()
        assert server.websocket_server._server is None
