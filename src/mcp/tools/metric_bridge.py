"""Adapter connecting vision pipeline state to MCP tools."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.vision.state_store import StateStore as VisionStateStore
    from src.mcp.storage.config import Config


@dataclass
class MetricBridge:
    """
    Adapter connecting vision pipeline state to MCP tools.

    Encapsulates the coupling between vision and MCP modules,
    providing a clean interface for swim metric tools.
    """

    vision_state_store: "VisionStateStore"
    config: "Config"
    rate_window_seconds: float = 15.0

    def get_stroke_rate(self) -> dict:
        """
        Get current stroke rate and trend.

        Returns:
            {
                "rate": float,           # strokes per minute
                "trend": str,            # "increasing" | "stable" | "decreasing"
                "window_seconds": float  # rate calculation window
            }
        """
        state = self.vision_state_store.get_state()
        trend = self._calculate_trend(state.rate_history)

        return {
            "rate": round(state.stroke_rate, 1),
            "trend": trend,
            "window_seconds": self.rate_window_seconds,
        }

    def get_stroke_count(self) -> dict:
        """
        Get total strokes and estimated distance.

        Returns:
            {
                "count": int,               # total strokes in session
                "estimated_distance_m": float  # count * dps_ratio
            }
        """
        state = self.vision_state_store.get_state()
        distance = state.stroke_count * self.config.dps_ratio

        return {
            "count": state.stroke_count,
            "estimated_distance_m": round(distance, 1),
        }

    def get_session_time(self) -> dict:
        """
        Get elapsed session time.

        Returns:
            {
                "elapsed_seconds": int,
                "formatted": str  # "MM:SS" format
            }
        """
        state = self.vision_state_store.get_state()

        if not state.session_active or state.session_start is None:
            return {"elapsed_seconds": 0, "formatted": "0:00"}

        elapsed = (datetime.now() - state.session_start).total_seconds()
        elapsed_int = int(elapsed)

        minutes = elapsed_int // 60
        seconds = elapsed_int % 60
        formatted = f"{minutes}:{seconds:02d}"

        return {
            "elapsed_seconds": elapsed_int,
            "formatted": formatted,
        }

    def get_all_metrics(self) -> dict:
        """Get all metrics in a single call."""
        return {
            "stroke_rate": self.get_stroke_rate(),
            "stroke_count": self.get_stroke_count(),
            "session_time": self.get_session_time(),
        }

    def _calculate_trend(self, rate_history: list) -> str:
        """
        Calculate trend from rate history.

        Uses last 4 samples to determine direction.
        Threshold of ±2.0 strokes/min for trend detection.
        """
        if len(rate_history) < 2:
            return "stable"

        # Take last 4 samples (or all if fewer)
        recent = rate_history[-4:]
        rates = [sample.rate for sample in recent]

        # Simple linear trend: compare first and last
        diff = rates[-1] - rates[0]

        if diff > 2.0:
            return "increasing"
        elif diff < -2.0:
            return "decreasing"
        else:
            return "stable"
