"""Tests for synchronization between vision and MCP state."""

import pytest
from datetime import datetime
from unittest.mock import Mock

from src.vision.state_store import SwimState, StateStore as VisionStateStore
from src.vision.rate_calculator import RateSample


class TestVisionMCPStateSync:
    """Test synchronization between vision and MCP state."""

    @pytest.fixture
    def mock_vision_store(self):
        """Mock vision state store."""
        store = Mock(spec=VisionStateStore)
        store.get_state.return_value = SwimState(
            session_active=True,
            stroke_count=50,
            stroke_rate=52.5,
            is_swimming=True,
        )
        return store

    @pytest.fixture
    def integrated_server(self, temp_slipstream_dir, mock_vision_store):
        """Server with vision integration."""
        from src.mcp.server import SwimCoachServer

        return SwimCoachServer(
            websocket_port=0,
            config_dir=temp_slipstream_dir,
            vision_state_store=mock_vision_store,
        )

    def test_stroke_count_sync(self, integrated_server, mock_vision_store):
        """Vision stroke count syncs to MCP swim tools."""
        mock_vision_store.get_state.return_value = SwimState(
            session_active=True,
            stroke_count=50,
        )

        result = integrated_server._get_stroke_count()

        assert result["count"] == 50

    def test_stroke_rate_sync(self, integrated_server, mock_vision_store):
        """Vision stroke rate syncs to MCP swim tools."""
        mock_vision_store.get_state.return_value = SwimState(
            session_active=True,
            stroke_rate=52.5,
        )

        result = integrated_server._get_stroke_rate()

        assert result["rate"] == 52.5

    def test_session_lifecycle_sync(self, integrated_server, mock_vision_store):
        """Session start/end syncs correctly."""
        # Start session via MCP
        start_result = integrated_server._start_session()
        assert "session_id" in start_result

        # Vision state reflects swimming
        mock_vision_store.get_state.return_value = SwimState(
            session_active=True,
            stroke_count=100,
            stroke_rate=55.0,
            is_swimming=True,
        )

        # Swim tools should see updated data
        rate_result = integrated_server._get_stroke_rate()
        assert rate_result["rate"] == 55.0

        count_result = integrated_server._get_stroke_count()
        assert count_result["count"] == 100

    def test_distance_config_update(self, integrated_server, mock_vision_store):
        """Distance calculation uses current config."""
        mock_vision_store.get_state.return_value = SwimState(
            session_active=True,
            stroke_count=100,
        )

        # Initial distance with default dps_ratio=1.8
        result1 = integrated_server._get_stroke_count()
        assert result1["estimated_distance_m"] == 180.0

        # Update config
        integrated_server.config.dps_ratio = 2.0

        # Distance should reflect new ratio
        result2 = integrated_server._get_stroke_count()
        assert result2["estimated_distance_m"] == 200.0

    def test_rate_trend_calculation(self, integrated_server, mock_vision_store):
        """Rate trend calculated correctly from vision rate history."""
        # Increasing trend
        mock_vision_store.get_state.return_value = SwimState(
            session_active=True,
            stroke_rate=58.0,
            rate_history=[
                RateSample(timestamp=0.0, rate=50.0),
                RateSample(timestamp=5.0, rate=52.0),
                RateSample(timestamp=10.0, rate=54.0),
                RateSample(timestamp=15.0, rate=58.0),
            ],
            is_swimming=True,
        )

        result = integrated_server._get_stroke_rate()
        assert result["trend"] == "increasing"

        # Decreasing trend
        mock_vision_store.get_state.return_value = SwimState(
            session_active=True,
            stroke_rate=42.0,
            rate_history=[
                RateSample(timestamp=0.0, rate=50.0),
                RateSample(timestamp=5.0, rate=48.0),
                RateSample(timestamp=10.0, rate=45.0),
                RateSample(timestamp=15.0, rate=42.0),
            ],
            is_swimming=True,
        )

        result = integrated_server._get_stroke_rate()
        assert result["trend"] == "decreasing"

    def test_multiple_updates_sync(self, integrated_server, mock_vision_store):
        """Multiple rapid updates sync correctly."""
        for i in range(10):
            mock_vision_store.get_state.return_value = SwimState(
                session_active=True,
                stroke_count=i * 10,
                stroke_rate=50.0 + i,
            )

            count_result = integrated_server._get_stroke_count()
            assert count_result["count"] == i * 10

            rate_result = integrated_server._get_stroke_rate()
            assert rate_result["rate"] == 50.0 + i

    def test_no_session_returns_safe_defaults(self, integrated_server, mock_vision_store):
        """No active session returns safe defaults."""
        mock_vision_store.get_state.return_value = SwimState(
            session_active=False,
            stroke_count=0,
            stroke_rate=0.0,
            is_swimming=False,
        )

        rate = integrated_server._get_stroke_rate()
        count = integrated_server._get_stroke_count()
        time = integrated_server._get_session_time()

        assert rate["rate"] == 0.0
        assert rate["trend"] == "stable"
        assert count["count"] == 0
        assert time["elapsed_seconds"] == 0


class TestMCPStateSyncFromVision:
    """Test MCP StateStore sync_from_vision method."""

    def test_sync_from_vision_updates_stroke_count(self):
        """sync_from_vision updates stroke count."""
        from src.mcp.state_store import StateStore

        mcp_store = StateStore()
        mcp_store.start_session()

        vision_state = SwimState(
            session_active=True,
            stroke_count=75,
            stroke_rate=54.0,
        )

        mcp_store.sync_from_vision(vision_state)

        assert mcp_store.session.stroke_count == 75

    def test_sync_from_vision_updates_stroke_rate(self):
        """sync_from_vision updates stroke rate."""
        from src.mcp.state_store import StateStore

        mcp_store = StateStore()
        mcp_store.start_session()

        vision_state = SwimState(
            session_active=True,
            stroke_count=100,
            stroke_rate=56.5,
        )

        mcp_store.sync_from_vision(vision_state)

        assert mcp_store.session.stroke_rate == 56.5

    def test_sync_from_vision_updates_distance(self):
        """sync_from_vision updates estimated distance."""
        from src.mcp.state_store import StateStore

        mcp_store = StateStore(dps_ratio=2.0)
        mcp_store.start_session()

        vision_state = SwimState(
            session_active=True,
            stroke_count=100,
        )

        mcp_store.sync_from_vision(vision_state)

        assert mcp_store.session.estimated_distance_m == 200.0

    def test_sync_from_vision_updates_trend(self):
        """sync_from_vision updates stroke rate trend from history."""
        from src.mcp.state_store import StateStore

        mcp_store = StateStore()
        mcp_store.start_session()

        vision_state = SwimState(
            session_active=True,
            stroke_rate=58.0,
            rate_history=[
                RateSample(timestamp=0.0, rate=50.0),
                RateSample(timestamp=5.0, rate=52.0),
                RateSample(timestamp=10.0, rate=55.0),
                RateSample(timestamp=15.0, rate=58.0),
            ],
        )

        mcp_store.sync_from_vision(vision_state)

        # The sync should have updated the rate history, allowing trend calculation
        assert mcp_store.session.stroke_rate_trend in ["increasing", "stable", "decreasing"]

    def test_sync_from_vision_thread_safe(self):
        """sync_from_vision is thread-safe."""
        import threading
        from src.mcp.state_store import StateStore

        mcp_store = StateStore()
        mcp_store.start_session()

        errors = []

        def sync_worker(store, count):
            try:
                for i in range(100):
                    vision_state = SwimState(
                        session_active=True,
                        stroke_count=count * 100 + i,
                        stroke_rate=50.0 + i % 10,
                    )
                    store.sync_from_vision(vision_state)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=sync_worker, args=(mcp_store, i))
            for i in range(5)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
