"""Tests for E2E harness setup and control."""

import pytest
import pytest_asyncio
from pathlib import Path
from unittest.mock import patch

from verification.e2e_harness import E2EHarness, HarnessConfig


class TestE2EHarness:
    """Test E2E harness setup and control."""

    @pytest_asyncio.fixture
    async def harness(self, tmp_path: Path):
        """Create harness with test config."""
        config = HarnessConfig(
            websocket_port=0,  # Random port
            dashboard_port=5173,
            config_dir=tmp_path / ".slipstream-test",
            open_browser=False,  # Don't open browser in tests
        )
        harness = E2EHarness(config)
        await harness.start()
        yield harness
        await harness.stop()

    @pytest.mark.asyncio
    async def test_harness_starts_server(self, harness):
        """Test 21: Harness starts server."""
        assert harness.server is not None
        assert harness.server.websocket_server.port > 0

    def test_harness_dashboard_url(self, tmp_path: Path):
        """Test 22: Harness returns correct dashboard URL."""
        config = HarnessConfig(
            dashboard_port=5173,
            config_dir=tmp_path / ".slipstream-test",
            open_browser=False,
        )
        harness = E2EHarness(config)
        assert harness.get_dashboard_url() == "http://localhost:5173"

    @pytest.mark.asyncio
    async def test_harness_mock_controls(self, harness):
        """Test 23: Harness provides mock controls."""
        # Test setting swimming state
        harness.mock_vision.set_swimming(True)
        state = harness.mock_vision.get_state()
        assert state.is_swimming is True

        # Test setting stroke count
        harness.mock_vision.set_stroke_count(50)
        state = harness.mock_vision.get_state()
        assert state.stroke_count == 50

        # Test setting stroke rate
        harness.mock_vision.set_stroke_rate(52.0)
        state = harness.mock_vision.get_state()
        assert state.stroke_rate == 52.0

    def test_harness_cli_args(self):
        """Test 24: Harness CLI args parsed correctly."""
        import argparse

        # Simulate CLI argument parsing
        parser = argparse.ArgumentParser()
        parser.add_argument("--port", type=int, default=8765)
        parser.add_argument("--dashboard-port", type=int, default=5173)
        parser.add_argument("--no-browser", action="store_true")
        parser.add_argument("--config-dir", type=Path)

        args = parser.parse_args(["--port", "9000", "--no-browser"])

        assert args.port == 9000
        assert args.no_browser is True

    def test_harness_prints_checklist(self, capsys):
        """Test 25: Harness prints verification checklist."""
        config = HarnessConfig(open_browser=False)
        harness = E2EHarness(config)
        harness.print_checklist()

        captured = capsys.readouterr()
        assert "VERIFICATION CHECKLIST" in captured.out
        assert "DASHBOARD DISPLAY" in captured.out
        assert "SESSION FLOW" in captured.out


class TestHarnessCommands:
    """Test harness command handling."""

    @pytest_asyncio.fixture
    async def harness(self, tmp_path: Path):
        """Create harness with test config."""
        config = HarnessConfig(
            websocket_port=0,
            config_dir=tmp_path / ".slipstream-test",
            open_browser=False,
        )
        harness = E2EHarness(config)
        await harness.start()
        yield harness
        await harness.stop()

    @pytest.mark.asyncio
    async def test_swim_command(self, harness):
        """Test swim command sets swimming state."""
        await harness._handle_command("swim 60")
        state = harness.mock_vision.get_state()
        assert state.is_swimming is True
        assert state.stroke_rate == 60.0

    @pytest.mark.asyncio
    async def test_stop_command(self, harness):
        """Test stop command stops swimming."""
        harness.mock_vision.set_swimming(True)
        await harness._handle_command("stop")
        state = harness.mock_vision.get_state()
        assert state.is_swimming is False

    @pytest.mark.asyncio
    async def test_strokes_command(self, harness):
        """Test strokes command sets stroke count."""
        await harness._handle_command("strokes 100")
        state = harness.mock_vision.get_state()
        assert state.stroke_count == 100

    @pytest.mark.asyncio
    async def test_rate_command(self, harness):
        """Test rate command sets stroke rate."""
        await harness._handle_command("rate 55.5")
        state = harness.mock_vision.get_state()
        assert state.stroke_rate == 55.5

    @pytest.mark.asyncio
    async def test_session_start_command(self, harness):
        """Test session start command."""
        await harness._handle_command("session start")
        update = harness.server.state_store.get_state_update()
        assert update.session.active is True

    @pytest.mark.asyncio
    async def test_session_end_command(self, harness):
        """Test session end command."""
        harness.server._start_session()
        await harness._handle_command("session end")
        update = harness.server.state_store.get_state_update()
        assert update.session.active is False

    @pytest.mark.asyncio
    async def test_quit_command(self, harness):
        """Test quit command sets running to false."""
        harness._running = True
        await harness._handle_command("quit")
        assert harness._running is False

    @pytest.mark.asyncio
    async def test_unknown_command(self, harness, capsys):
        """Test unknown command shows error."""
        await harness._handle_command("foobar")
        captured = capsys.readouterr()
        assert "Unknown command" in captured.out
