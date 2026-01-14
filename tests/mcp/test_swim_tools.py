"""Tests for MCP swim metric tools."""

import pytest
import time
from unittest.mock import Mock


class TestSwimTools:
    """Test MCP swim metric tools."""

    @pytest.fixture
    def mock_bridge(self):
        """Mock MetricBridge for tool tests."""
        bridge = Mock()
        bridge.get_stroke_rate.return_value = {
            "rate": 54.0,
            "trend": "stable",
            "window_seconds": 15.0,
        }
        bridge.get_stroke_count.return_value = {
            "count": 142,
            "estimated_distance_m": 255.6,
        }
        bridge.get_session_time.return_value = {
            "elapsed_seconds": 300,
            "formatted": "5:00",
        }
        return bridge

    @pytest.fixture
    def swim_tools(self, mock_bridge):
        """Swim tools using mock bridge."""
        from src.mcp.tools.swim_tools import create_swim_tools

        return create_swim_tools(mock_bridge)

    def test_get_stroke_rate_tool(self, swim_tools, mock_bridge):
        """get_stroke_rate tool returns bridge data."""
        get_stroke_rate = swim_tools[0]

        result = get_stroke_rate()

        assert result == {
            "rate": 54.0,
            "trend": "stable",
            "window_seconds": 15.0,
        }
        mock_bridge.get_stroke_rate.assert_called_once()

    def test_get_stroke_count_tool(self, swim_tools, mock_bridge):
        """get_stroke_count tool returns bridge data."""
        get_stroke_count = swim_tools[1]

        result = get_stroke_count()

        assert result == {
            "count": 142,
            "estimated_distance_m": 255.6,
        }
        mock_bridge.get_stroke_count.assert_called_once()

    def test_get_session_time_tool(self, swim_tools, mock_bridge):
        """get_session_time tool returns bridge data."""
        get_session_time = swim_tools[2]

        result = get_session_time()

        assert result == {
            "elapsed_seconds": 300,
            "formatted": "5:00",
        }
        mock_bridge.get_session_time.assert_called_once()

    def test_tool_descriptions(self, swim_tools):
        """Each tool has descriptive docstring for Claude."""
        get_stroke_rate, get_stroke_count, get_session_time = swim_tools

        assert get_stroke_rate.__doc__ is not None
        assert "stroke rate" in get_stroke_rate.__doc__.lower()
        assert "trend" in get_stroke_rate.__doc__.lower()

        assert get_stroke_count.__doc__ is not None
        assert "stroke" in get_stroke_count.__doc__.lower()
        assert "distance" in get_stroke_count.__doc__.lower()

        assert get_session_time.__doc__ is not None
        assert "time" in get_session_time.__doc__.lower()

    def test_tool_latency(self, swim_tools, mock_bridge):
        """Tools respond within latency budget (<100ms avg)."""
        get_stroke_rate = swim_tools[0]

        start = time.time()
        for _ in range(100):
            get_stroke_rate()
        elapsed = time.time() - start

        avg_latency_ms = (elapsed / 100) * 1000
        assert avg_latency_ms < 100

    def test_tool_handles_bridge_error(self, mock_bridge):
        """Tool returns error dict when bridge raises exception."""
        from src.mcp.tools.swim_tools import create_swim_tools

        mock_bridge.get_stroke_rate.side_effect = RuntimeError("Vision pipeline error")
        tools = create_swim_tools(mock_bridge)
        get_stroke_rate = tools[0]

        result = get_stroke_rate()

        assert "error" in result
        assert "Vision pipeline error" in result["error"]

    def test_create_swim_tools_factory(self, mock_bridge):
        """create_swim_tools returns list of 3 tool functions."""
        from src.mcp.tools.swim_tools import create_swim_tools

        tools = create_swim_tools(mock_bridge)

        assert len(tools) == 3
        assert callable(tools[0])
        assert callable(tools[1])
        assert callable(tools[2])

    def test_tool_names(self, swim_tools):
        """Tools have correct function names."""
        assert swim_tools[0].__name__ == "get_stroke_rate"
        assert swim_tools[1].__name__ == "get_stroke_count"
        assert swim_tools[2].__name__ == "get_session_time"


class TestSwimToolsIntegration:
    """Integration tests with real MetricBridge."""

    @pytest.fixture
    def integration_setup(self, temp_slipstream_dir):
        """Real components for integration tests."""
        from datetime import datetime
        from src.vision.state_store import StateStore as VisionStateStore
        from src.mcp.storage.config import Config
        from src.mcp.tools.metric_bridge import MetricBridge
        from src.mcp.tools.swim_tools import create_swim_tools

        vision_store = VisionStateStore()
        config = Config(
            dps_ratio=1.8,
            config_path=temp_slipstream_dir / "config.json",
        )
        bridge = MetricBridge(vision_store, config)
        tools = create_swim_tools(bridge)

        return vision_store, config, bridge, tools

    def test_integration_stroke_rate(self, integration_setup):
        """Full integration - stroke rate from vision pipeline."""
        vision_store, config, bridge, tools = integration_setup
        get_stroke_rate = tools[0]

        # Start session and update vision state
        vision_store.start_session()
        vision_store.update(stroke_rate=52.5, is_swimming=True)

        result = get_stroke_rate()

        assert result["rate"] == 52.5
        assert result["trend"] == "stable"
        assert result["window_seconds"] == 15.0

    def test_integration_stroke_count(self, integration_setup):
        """Full integration - stroke count with distance."""
        vision_store, config, bridge, tools = integration_setup
        get_stroke_count = tools[1]

        # Update config and vision state
        config.dps_ratio = 1.8
        vision_store.start_session()
        vision_store.update(stroke_count=100)

        result = get_stroke_count()

        assert result["count"] == 100
        assert result["estimated_distance_m"] == 180.0

    def test_integration_session_time(self, integration_setup):
        """Full integration - session time."""
        vision_store, config, bridge, tools = integration_setup
        get_session_time = tools[2]

        # Start session
        vision_store.start_session()

        # Small delay to ensure elapsed time > 0
        time.sleep(0.1)

        result = get_session_time()

        assert result["elapsed_seconds"] >= 0
        assert result["formatted"] == "0:00"  # Less than 1 second
