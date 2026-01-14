"""Tests for session summary formatting."""

import pytest

from src.notifications.formatter import format_summary, format_duration, format_distance


class TestFormatDuration:
    """Test duration formatting."""

    @pytest.mark.parametrize(
        "seconds,expected",
        [
            (60, "1:00"),
            (125, "2:05"),
            (1934, "32:14"),
            (3661, "1:01:01"),
        ],
    )
    def test_format_duration(self, seconds, expected):
        """Duration formatted as MM:SS or H:MM:SS."""
        assert format_duration(seconds) == expected

    def test_format_duration_zero(self):
        """Zero seconds formatted correctly."""
        assert format_duration(0) == "0:00"


class TestFormatDistance:
    """Test distance formatting."""

    @pytest.mark.parametrize(
        "meters,expected",
        [
            (150.0, "150m"),
            (1200.6, "1,201m"),  # .6 rounds up consistently
            (2500.0, "2,500m"),
        ],
    )
    def test_format_distance(self, meters, expected):
        """Distance formatted with commas, rounded to int."""
        assert format_distance(meters) == expected

    def test_format_distance_zero(self):
        """Zero distance formatted correctly."""
        assert format_distance(0.0) == "0m"


class TestSessionFormatter:
    """Test session summary formatting."""

    def test_format_complete_session(self):
        """Format complete session with all fields."""
        session = {
            "session_id": "2024-01-15_1430",
            "started_at": "2024-01-15T14:30:00+00:00",
            "ended_at": "2024-01-15T15:02:14+00:00",
            "stroke_count": 842,
            "stroke_rate_avg": 53.2,
            "duration_seconds": 1934,
            "estimated_distance_m": 1515.6,
        }

        result = format_summary(session)

        assert "32:14" in result  # Duration
        assert "1,516m" in result  # Distance (rounded)
        assert "53/min" in result  # Stroke rate
        assert "842" in result  # Stroke count

    def test_format_stroke_rate(self):
        """Stroke rate rounded to int with /min suffix."""
        session = {
            "session_id": "test",
            "stroke_count": 100,
            "stroke_rate_avg": 53.2,
            "duration_seconds": 300,
            "estimated_distance_m": 500.0,
        }

        result = format_summary(session)

        assert "53/min" in result

    def test_format_empty_session(self):
        """Handle session with zero values gracefully."""
        session = {
            "session_id": "2024-01-15_1430",
            "stroke_count": 0,
            "stroke_rate_avg": 0.0,
            "duration_seconds": 0,
            "estimated_distance_m": 0.0,
        }

        result = format_summary(session)

        # Should not raise, should return valid message
        assert isinstance(result, str)
        assert len(result) > 0

    def test_format_includes_header(self):
        """Message starts with swim emoji header."""
        session = {
            "session_id": "test",
            "stroke_count": 100,
            "stroke_rate_avg": 50.0,
            "duration_seconds": 300,
            "estimated_distance_m": 500.0,
        }

        result = format_summary(session)

        assert result.startswith("🏊 Swim Session Complete")

    def test_format_message_length(self):
        """Message is under Telegram's 4096 char limit."""
        session = {
            "session_id": "2024-01-15_1430",
            "stroke_count": 999999,
            "stroke_rate_avg": 999.9,
            "duration_seconds": 99999,
            "estimated_distance_m": 99999.9,
        }

        result = format_summary(session)

        assert len(result) < 4096

    def test_format_handles_missing_fields(self):
        """Handle session with missing optional fields."""
        session = {
            "session_id": "test",
        }

        result = format_summary(session)

        # Should use defaults (0) for missing fields
        assert isinstance(result, str)
        assert "0:00" in result  # Default duration
