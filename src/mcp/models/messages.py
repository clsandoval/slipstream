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


@dataclass
class WorkoutStateMessage:
    """Workout state for WebSocket broadcast."""

    has_active_workout: bool = False
    phase: str = "no_workout"
    workout_name: str | None = None
    current_segment: dict[str, Any] | None = None
    progress: dict[str, Any] | None = None
    next_segment: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "has_active_workout": self.has_active_workout,
            "phase": self.phase,
            "workout_name": self.workout_name,
            "current_segment": self.current_segment,
            "progress": self.progress,
            "next_segment": self.next_segment,
        }

    @classmethod
    def from_status(cls, status: dict[str, Any]) -> "WorkoutStateMessage":
        """Create from state machine get_status() result."""
        return cls(
            has_active_workout=status.get("has_active_workout", False),
            phase=status.get("phase", "no_workout"),
            workout_name=status.get("workout_name"),
            current_segment=status.get("current_segment"),
            progress=status.get("progress"),
            next_segment=status.get("next_segment"),
        )


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
    workout: WorkoutStateMessage | None = None

    def to_json(self) -> str:
        """Serialize to JSON string."""
        data = {
            "type": self.type,
            "timestamp": self.timestamp,
            "session": self.session.to_dict(),
            "system": self.system.to_dict(),
            "workout": self.workout.to_dict() if self.workout else None,
        }
        return json.dumps(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StateUpdate:
        """Create StateUpdate from dictionary."""
        session_data = data.get("session", {})
        system_data = data.get("system", {})
        workout_data = data.get("workout")

        workout = None
        if workout_data:
            workout = WorkoutStateMessage(
                has_active_workout=workout_data.get("has_active_workout", False),
                phase=workout_data.get("phase", "no_workout"),
                workout_name=workout_data.get("workout_name"),
                current_segment=workout_data.get("current_segment"),
                progress=workout_data.get("progress"),
                next_segment=workout_data.get("next_segment"),
            )

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
            workout=workout,
        )
