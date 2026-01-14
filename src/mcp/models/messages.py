"""WebSocket message schemas for dashboard communication."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class SessionState:
    """Current swim session state."""

    active: bool = False
    elapsed_seconds: int = 0
    stroke_count: int = 0
    stroke_rate: float = 0.0
    stroke_rate_trend: str = "stable"  # "increasing" | "stable" | "decreasing"
    estimated_distance_m: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "active": self.active,
            "elapsed_seconds": self.elapsed_seconds,
            "stroke_count": self.stroke_count,
            "stroke_rate": self.stroke_rate,
            "stroke_rate_trend": self.stroke_rate_trend,
            "estimated_distance_m": self.estimated_distance_m,
        }


@dataclass
class SystemState:
    """Current system status."""

    is_swimming: bool = False
    pose_detected: bool = False
    voice_state: str = "idle"  # "idle" | "listening" | "speaking"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_swimming": self.is_swimming,
            "pose_detected": self.pose_detected,
            "voice_state": self.voice_state,
        }


def _current_timestamp() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class StateUpdate:
    """State update message for WebSocket broadcast."""

    type: str = "state_update"
    timestamp: str = field(default_factory=_current_timestamp)
    session: SessionState = field(default_factory=SessionState)
    system: SystemState = field(default_factory=SystemState)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(
            {
                "type": self.type,
                "timestamp": self.timestamp,
                "session": self.session.to_dict(),
                "system": self.system.to_dict(),
            }
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StateUpdate:
        """Create StateUpdate from dictionary."""
        session_data = data.get("session", {})
        system_data = data.get("system", {})

        return cls(
            type=data.get("type", "state_update"),
            timestamp=data.get("timestamp", _current_timestamp()),
            session=SessionState(
                active=session_data.get("active", False),
                elapsed_seconds=session_data.get("elapsed_seconds", 0),
                stroke_count=session_data.get("stroke_count", 0),
                stroke_rate=session_data.get("stroke_rate", 0.0),
                stroke_rate_trend=session_data.get("stroke_rate_trend", "stable"),
                estimated_distance_m=session_data.get("estimated_distance_m", 0.0),
            ),
            system=SystemState(
                is_swimming=system_data.get("is_swimming", False),
                pose_detected=system_data.get("pose_detected", False),
                voice_state=system_data.get("voice_state", "idle"),
            ),
        )
