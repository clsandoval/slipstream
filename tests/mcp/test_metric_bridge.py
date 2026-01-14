"""Tests for MetricBridge adapter between vision and MCP."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from src.vision.state_store import SwimState
from src.vision.rate_calculator import RateSample
from src.mcp.storage.config import Config


class TestMetricBridgeStrokeRate:
    """Test stroke rate retrieval."""

    def test_get_stroke_rate_returns_current_rate(self, metric_bridge, mock_vision_state_store):
        """Given vision state with stroke_rate=54.5, returns rate=54.5."""
        mock_vision_state_store.get_state.return_value = SwimState(
            session_active=True,
            stroke_rate=54.5,
            is_swimming=True,
        )

        result = metric_bridge.get_stroke_rate()

        assert result["rate"] == 54.5

    def test_get_stroke_rate_includes_trend_increasing(self, metric_bridge, mock_vision_state_store):
        """Given rate_history showing increasing pattern, returns trend='increasing'."""
        mock_vision_state_store.get_state.return_value = SwimState(
            session_active=True,
            stroke_rate=56.0,
            rate_history=[
                RateSample(timestamp=0.0, rate=50.0),
                RateSample(timestamp=5.0, rate=52.0),
                RateSample(timestamp=10.0, rate=54.0),
                RateSample(timestamp=15.0, rate=56.0),
            ],
            is_swimming=True,
        )

        result = metric_bridge.get_stroke_rate()

        assert result["trend"] == "increasing"

    def test_get_stroke_rate_includes_trend_decreasing(self, metric_bridge, mock_vision_state_store):
        """Given rate_history showing decreasing pattern, returns trend='decreasing'."""
        mock_vision_state_store.get_state.return_value = SwimState(
            session_active=True,
            stroke_rate=44.0,
            rate_history=[
                RateSample(timestamp=0.0, rate=50.0),
                RateSample(timestamp=5.0, rate=48.0),
                RateSample(timestamp=10.0, rate=46.0),
                RateSample(timestamp=15.0, rate=44.0),
            ],
            is_swimming=True,
        )

        result = metric_bridge.get_stroke_rate()

        assert result["trend"] == "decreasing"

    def test_get_stroke_rate_includes_trend_stable(self, metric_bridge, mock_vision_state_store):
        """Given rate_history within threshold, returns trend='stable'."""
        mock_vision_state_store.get_state.return_value = SwimState(
            session_active=True,
            stroke_rate=51.0,
            rate_history=[
                RateSample(timestamp=0.0, rate=50.0),
                RateSample(timestamp=5.0, rate=50.5),
                RateSample(timestamp=10.0, rate=50.0),
                RateSample(timestamp=15.0, rate=51.0),
            ],
            is_swimming=True,
        )

        result = metric_bridge.get_stroke_rate()

        assert result["trend"] == "stable"

    def test_get_stroke_rate_not_swimming(self, metric_bridge, mock_vision_state_store):
        """Given is_swimming=False, returns rate=0, trend='stable'."""
        mock_vision_state_store.get_state.return_value = SwimState(
            session_active=False,
            stroke_rate=0.0,
            is_swimming=False,
        )

        result = metric_bridge.get_stroke_rate()

        assert result["rate"] == 0.0
        assert result["trend"] == "stable"

    def test_get_stroke_rate_includes_window(self, metric_bridge, mock_vision_state_store):
        """Returns window_seconds from configuration."""
        mock_vision_state_store.get_state.return_value = SwimState()

        result = metric_bridge.get_stroke_rate()

        assert result["window_seconds"] == 15.0


class TestMetricBridgeStrokeCount:
    """Test stroke count retrieval."""

    def test_get_stroke_count_returns_total(self, metric_bridge, mock_vision_state_store):
        """Given vision state with stroke_count=142, returns count=142."""
        mock_vision_state_store.get_state.return_value = SwimState(
            session_active=True,
            stroke_count=142,
        )

        result = metric_bridge.get_stroke_count()

        assert result["count"] == 142

    def test_get_stroke_count_includes_distance(self, metric_bridge, mock_vision_state_store, config):
        """Given stroke_count=100 and config.dps_ratio=1.5, returns estimated_distance_m=150.0."""
        config.dps_ratio = 1.5
        mock_vision_state_store.get_state.return_value = SwimState(
            session_active=True,
            stroke_count=100,
        )

        result = metric_bridge.get_stroke_count()

        assert result["estimated_distance_m"] == 150.0

    def test_distance_uses_config_dps_ratio(self, metric_bridge, mock_vision_state_store, config):
        """Given config.dps_ratio=2.0, stroke_count=50, returns estimated_distance_m=100.0."""
        config.dps_ratio = 2.0
        mock_vision_state_store.get_state.return_value = SwimState(
            session_active=True,
            stroke_count=50,
        )

        result = metric_bridge.get_stroke_count()

        assert result["estimated_distance_m"] == 100.0


class TestMetricBridgeSessionTime:
    """Test session time retrieval."""

    def test_get_session_time_active(self, metric_bridge, mock_vision_state_store):
        """Given session started 5 minutes ago, returns elapsed_seconds=300."""
        five_minutes_ago = datetime.now() - timedelta(minutes=5)
        mock_vision_state_store.get_state.return_value = SwimState(
            session_active=True,
            session_start=five_minutes_ago,
        )

        result = metric_bridge.get_session_time()

        # Allow 1 second tolerance for test execution time
        assert 299 <= result["elapsed_seconds"] <= 301
        assert result["formatted"] == "5:00"

    @pytest.mark.parametrize("seconds,expected", [
        (0, "0:00"),
        (59, "0:59"),
        (60, "1:00"),
        (125, "2:05"),
        (3661, "61:01"),  # Over an hour
    ])
    def test_get_session_time_formatting(self, metric_bridge, mock_vision_state_store, seconds, expected):
        """Test time formatting for various durations."""
        start_time = datetime.now() - timedelta(seconds=seconds)
        mock_vision_state_store.get_state.return_value = SwimState(
            session_active=True,
            session_start=start_time,
        )

        result = metric_bridge.get_session_time()

        assert result["formatted"] == expected

    def test_get_session_time_no_session(self, metric_bridge, mock_vision_state_store):
        """Given no active session, returns elapsed_seconds=0, formatted='0:00'."""
        mock_vision_state_store.get_state.return_value = SwimState(
            session_active=False,
            session_start=None,
        )

        result = metric_bridge.get_session_time()

        assert result["elapsed_seconds"] == 0
        assert result["formatted"] == "0:00"


class TestMetricBridgeEdgeCases:
    """Test edge cases and error handling."""

    def test_handles_no_vision_state(self, metric_bridge, mock_vision_state_store):
        """Given vision state_store returns default SwimState, returns safe defaults."""
        mock_vision_state_store.get_state.return_value = SwimState()

        rate = metric_bridge.get_stroke_rate()
        count = metric_bridge.get_stroke_count()
        time = metric_bridge.get_session_time()

        assert rate["rate"] == 0.0
        assert rate["trend"] == "stable"
        assert count["count"] == 0
        assert time["elapsed_seconds"] == 0

    def test_trend_with_few_samples(self, metric_bridge, mock_vision_state_store):
        """Trend should be 'stable' with fewer than 2 samples."""
        mock_vision_state_store.get_state.return_value = SwimState(
            rate_history=[RateSample(timestamp=0.0, rate=50.0)],
        )

        result = metric_bridge.get_stroke_rate()

        assert result["trend"] == "stable"

    def test_get_all_metrics(self, metric_bridge, mock_vision_state_store):
        """Get all metrics returns combined dict with rate, count, time."""
        start_time = datetime.now() - timedelta(minutes=10)
        mock_vision_state_store.get_state.return_value = SwimState(
            session_active=True,
            session_start=start_time,
            stroke_count=200,
            stroke_rate=55.0,
            rate_history=[
                RateSample(timestamp=0.0, rate=54.0),
                RateSample(timestamp=5.0, rate=55.0),
            ],
        )

        result = metric_bridge.get_all_metrics()

        assert "stroke_rate" in result
        assert "stroke_count" in result
        assert "session_time" in result
        assert result["stroke_rate"]["rate"] == 55.0
        assert result["stroke_count"]["count"] == 200
        assert result["session_time"]["formatted"] == "10:00"
