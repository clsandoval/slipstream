"""Integration tests for full server stack with mocked vision."""

import asyncio
import json

import pytest
import pytest_asyncio
import websockets
from pathlib import Path

from verification.mocks import MockVisionStateStore
from src.mcp.server import SwimCoachServer


class TestServerIntegration:
    """Integration tests for full server stack."""

    @pytest.fixture
    def mock_vision(self):
        """Mock vision state store."""
        return MockVisionStateStore()

    @pytest_asyncio.fixture
    async def server(self, tmp_path: Path, mock_vision):
        """Running server with mocked vision."""
        config_dir = tmp_path / ".slipstream"
        config_dir.mkdir(parents=True)
        (config_dir / "sessions").mkdir()

        server = SwimCoachServer(
            websocket_port=0,  # Random port
            push_interval=0.1,  # Fast push for tests
            config_dir=config_dir,
            vision_state_store=mock_vision,
        )
        await server.start()
        yield server
        await server.stop()

    @pytest.mark.asyncio
    async def test_server_starts(self, server):
        """Test 1: Server starts with mocked vision."""
        assert server.websocket_server.port > 0

    @pytest.mark.asyncio
    async def test_websocket_initial_state(self, server):
        """Test 2: WebSocket receives initial state."""
        uri = f"ws://localhost:{server.websocket_server.port}"
        async with websockets.connect(uri) as ws:
            msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
            data = json.loads(msg)

            assert data["type"] == "state_update"
            assert data["session"]["active"] is False

    @pytest.mark.asyncio
    async def test_start_session_updates_websocket(self, server):
        """Test 3: Start session updates WebSocket."""
        uri = f"ws://localhost:{server.websocket_server.port}"
        async with websockets.connect(uri) as ws:
            # Consume initial state
            await ws.recv()

            # Start session via tool
            result = server._start_session()
            assert "session_id" in result

            # Wait for state update
            msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
            data = json.loads(msg)
            assert data["session"]["active"] is True

    @pytest.mark.asyncio
    async def test_vision_state_flows_to_websocket(self, server, mock_vision):
        """Test 4: Mock vision state flows to WebSocket via system state."""
        uri = f"ws://localhost:{server.websocket_server.port}"
        async with websockets.connect(uri) as ws:
            # Consume initial state
            await ws.recv()

            # Update mock vision state
            mock_vision.set_swimming(True)

            # Update server's system state to reflect vision
            server.state_store.update_system(is_swimming=True, pose_detected=True)

            # Wait for next push
            msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
            data = json.loads(msg)
            assert data["system"]["is_swimming"] is True

    @pytest.mark.asyncio
    async def test_end_session_updates_websocket(self, server):
        """Test 5: End session updates WebSocket."""
        uri = f"ws://localhost:{server.websocket_server.port}"
        async with websockets.connect(uri) as ws:
            await ws.recv()  # Initial

            server._start_session()
            await ws.recv()  # Start update

            await server._end_session()

            msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
            data = json.loads(msg)
            assert data["session"]["active"] is False

    @pytest.mark.asyncio
    async def test_stroke_rate_query(self, server, mock_vision):
        """Test 6: Stroke rate query returns mock data."""
        # Start session first, then set values
        mock_vision.start_session()
        mock_vision.set_stroke_rate(55.0)
        mock_vision.set_swimming(True)

        # Query through metric bridge
        result = server.metric_bridge.get_stroke_rate()
        assert result["rate"] == 55.0

    @pytest.mark.asyncio
    async def test_distance_calculation(self, server, mock_vision):
        """Test 7: Distance calculation uses mock strokes."""
        # Start sessions
        server._start_session()
        mock_vision.start_session()

        # Set mock strokes (100 strokes * 1.8 DPS = 180m)
        mock_vision.set_stroke_count(100)

        result = server.metric_bridge.get_stroke_count()
        assert result["count"] == 100
        assert result["estimated_distance_m"] == pytest.approx(180.0, rel=0.1)

    @pytest.mark.asyncio
    async def test_multiple_clients(self, server):
        """Test 8: Multiple WebSocket clients receive updates."""
        uri = f"ws://localhost:{server.websocket_server.port}"

        async with (
            websockets.connect(uri) as ws1,
            websockets.connect(uri) as ws2,
            websockets.connect(uri) as ws3,
        ):
            # Consume initial states
            await asyncio.gather(ws1.recv(), ws2.recv(), ws3.recv())

            # Trigger change
            server._start_session()

            # All should receive
            msgs = await asyncio.gather(
                asyncio.wait_for(ws1.recv(), timeout=2.0),
                asyncio.wait_for(ws2.recv(), timeout=2.0),
                asyncio.wait_for(ws3.recv(), timeout=2.0),
            )

            for msg in msgs:
                data = json.loads(msg)
                assert data["session"]["active"] is True


class TestStateStoreIntegration:
    """Integration tests for state store interactions."""

    @pytest.fixture
    def mock_vision(self):
        """Mock vision state store."""
        return MockVisionStateStore()

    @pytest_asyncio.fixture
    async def server(self, tmp_path: Path, mock_vision):
        """Running server with mocked vision."""
        config_dir = tmp_path / ".slipstream"
        config_dir.mkdir(parents=True)
        (config_dir / "sessions").mkdir()

        server = SwimCoachServer(
            websocket_port=0,
            push_interval=0.1,
            config_dir=config_dir,
            vision_state_store=mock_vision,
        )
        await server.start()
        yield server
        await server.stop()

    @pytest.mark.asyncio
    async def test_state_update_includes_all_fields(self, server):
        """Test state update message includes expected fields."""
        uri = f"ws://localhost:{server.websocket_server.port}"
        async with websockets.connect(uri) as ws:
            msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
            data = json.loads(msg)

            # Check top-level fields
            assert "type" in data
            assert "timestamp" in data
            assert "session" in data
            assert "system" in data

            # Check session fields
            session = data["session"]
            assert "active" in session
            assert "elapsed_seconds" in session
            assert "stroke_count" in session
            assert "stroke_rate" in session

            # Check system fields
            system = data["system"]
            assert "is_swimming" in system
            assert "pose_detected" in system

    @pytest.mark.asyncio
    async def test_strokes_update_to_state(self, server):
        """Test stroke updates flow to state."""
        server._start_session()
        server.state_store.update_strokes(count=50, rate=52.0)

        update = server.state_store.get_state_update()
        assert update.session.stroke_count == 50
        assert update.session.stroke_rate == 52.0

    @pytest.mark.asyncio
    async def test_estimated_distance_calculation(self, server):
        """Test distance is calculated from strokes and DPS."""
        server._start_session()
        server.state_store.update_strokes(count=100, rate=50.0)

        update = server.state_store.get_state_update()
        # Default DPS is 1.8, so 100 * 1.8 = 180
        assert update.session.estimated_distance_m == pytest.approx(180.0, rel=0.1)


class TestMetricBridgeIntegration:
    """Integration tests for metric bridge with mock vision."""

    @pytest.fixture
    def mock_vision(self):
        """Mock vision state store."""
        store = MockVisionStateStore()
        store.start_session()
        return store

    @pytest_asyncio.fixture
    async def server(self, tmp_path: Path, mock_vision):
        """Running server with mocked vision."""
        config_dir = tmp_path / ".slipstream"
        config_dir.mkdir(parents=True)
        (config_dir / "sessions").mkdir()

        server = SwimCoachServer(
            websocket_port=0,
            push_interval=0.1,
            config_dir=config_dir,
            vision_state_store=mock_vision,
        )
        await server.start()
        yield server
        await server.stop()

    @pytest.mark.asyncio
    async def test_metric_bridge_reads_vision_state(self, server, mock_vision):
        """Test metric bridge reads from vision state store."""
        mock_vision.set_stroke_rate(48.5)
        mock_vision.set_stroke_count(75)

        rate_result = server.metric_bridge.get_stroke_rate()
        count_result = server.metric_bridge.get_stroke_count()

        assert rate_result["rate"] == 48.5
        assert count_result["count"] == 75

    @pytest.mark.asyncio
    async def test_all_metrics_combined(self, server, mock_vision):
        """Test get_all_metrics returns combined data."""
        mock_vision.set_stroke_rate(50.0)
        mock_vision.set_stroke_count(100)

        result = server.metric_bridge.get_all_metrics()

        assert "stroke_rate" in result
        assert "stroke_count" in result
        assert "session_time" in result
