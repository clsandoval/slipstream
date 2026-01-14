"""MCP tools for swim metrics."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from src.mcp.tools.metric_bridge import MetricBridge


def create_swim_tools(bridge: "MetricBridge") -> list[Callable[[], dict[str, Any]]]:
    """
    Create swim metric tools for MCP registration.

    Args:
        bridge: MetricBridge adapter connecting to vision pipeline

    Returns:
        List of tool functions to register with FastMCP
    """

    def get_stroke_rate() -> dict[str, Any]:
        """
        Get current stroke rate and trend.

        Returns the swimmer's current stroke rate (strokes per minute),
        the trend direction, and the time window used for calculation.

        Returns:
            rate: Current strokes per minute
            trend: "increasing", "stable", or "decreasing"
            window_seconds: Time window for rate calculation (typically 15s)
        """
        try:
            return bridge.get_stroke_rate()
        except Exception as e:
            return {"error": str(e)}

    def get_stroke_count() -> dict[str, Any]:
        """
        Get total strokes and estimated distance.

        Returns the total stroke count for the current session
        and an estimated distance based on the user's DPS ratio
        (distance per stroke) setting.

        Returns:
            count: Total strokes in current session
            estimated_distance_m: Estimated distance swum in meters
        """
        try:
            return bridge.get_stroke_count()
        except Exception as e:
            return {"error": str(e)}

    def get_session_time() -> dict[str, Any]:
        """
        Get elapsed session time.

        Returns the total time elapsed since the session started,
        both as raw seconds and as a formatted string.

        Returns:
            elapsed_seconds: Total seconds since session start
            formatted: Human-readable time (e.g., "20:34")
        """
        try:
            return bridge.get_session_time()
        except Exception as e:
            return {"error": str(e)}

    return [get_stroke_rate, get_stroke_count, get_session_time]
