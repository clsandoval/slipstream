"""In-memory state management with thread safety."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.mcp.models.messages import SessionState, SystemState, StateUpdate


class SessionActiveError(Exception):
    """Raised when attempting to start a session while one is active."""

    pass


class NoActiveSessionError(Exception):
    """Raised when attempting to end a session when none is active."""

    pass


@dataclass
class StateStore:
    """Thread-safe in-memory state for swim sessions."""

    session: SessionState = field(default_factory=SessionState)
    system: SystemState = field(default_factory=SystemState)
    dps_ratio: float = 1.8
    _session_id: str | None = field(default=None, repr=False)
    _started_at: datetime | None = field(default=None, repr=False)
    _stroke_rate_history: list[float] = field(default_factory=list, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def start_session(self) -> str:
        """Begin a new swim session.

        Returns:
            Session ID in format YYYY-MM-DD_HHMM

        Raises:
            SessionActiveError: If a session is already active
        """
        with self._lock:
            if self.session.active:
                raise SessionActiveError("A session is already active")

            now = datetime.now(timezone.utc)
            session_id = now.strftime("%Y-%m-%d_%H%M")

            self._session_id = session_id
            self._started_at = now
            self._stroke_rate_history = []

            self.session = SessionState(active=True)

            return session_id

    def end_session(self) -> dict[str, Any]:
        """End the current session.

        Returns:
            Session summary dict

        Raises:
            NoActiveSessionError: If no session is active
        """
        with self._lock:
            if not self.session.active:
                raise NoActiveSessionError("No active session to end")

            now = datetime.now(timezone.utc)
            duration = int((now - self._started_at).total_seconds())

            # Calculate average stroke rate
            stroke_rate_avg = 0.0
            if self._stroke_rate_history:
                stroke_rate_avg = sum(self._stroke_rate_history) / len(
                    self._stroke_rate_history
                )

            summary = {
                "session_id": self._session_id,
                "started_at": self._started_at.isoformat(),
                "ended_at": now.isoformat(),
                "duration_seconds": duration,
                "stroke_count": self.session.stroke_count,
                "stroke_rate_avg": round(stroke_rate_avg, 1),
                "estimated_distance_m": self.session.estimated_distance_m,
            }

            # Reset state
            self._session_id = None
            self._started_at = None
            self._stroke_rate_history = []
            self.session = SessionState(active=False)

            return summary

    def update_strokes(self, count: int, rate: float) -> None:
        """Update stroke metrics.

        Args:
            count: Total stroke count
            rate: Current stroke rate (strokes/min)
        """
        with self._lock:
            self.session.stroke_count = count
            self.session.stroke_rate = rate
            self.session.estimated_distance_m = count * self.dps_ratio

            # Track rate history for trend calculation
            self._stroke_rate_history.append(rate)
            if len(self._stroke_rate_history) > 10:
                self._stroke_rate_history.pop(0)

            self.session.stroke_rate_trend = self._calculate_trend()

    def update_system(self, **kwargs: Any) -> None:
        """Update system state fields.

        Args:
            **kwargs: Fields to update (is_swimming, pose_detected, voice_state)
        """
        with self._lock:
            if "is_swimming" in kwargs:
                self.system.is_swimming = kwargs["is_swimming"]
            if "pose_detected" in kwargs:
                self.system.pose_detected = kwargs["pose_detected"]
            if "voice_state" in kwargs:
                self.system.voice_state = kwargs["voice_state"]

    def get_state_update(self) -> StateUpdate:
        """Get current state as StateUpdate message.

        Returns:
            StateUpdate with current session and system state
        """
        with self._lock:
            # Calculate elapsed time
            elapsed_seconds = 0
            if self._started_at:
                elapsed_seconds = int(
                    (datetime.now(timezone.utc) - self._started_at).total_seconds()
                )

            session = SessionState(
                active=self.session.active,
                elapsed_seconds=elapsed_seconds,
                stroke_count=self.session.stroke_count,
                stroke_rate=self.session.stroke_rate,
                stroke_rate_trend=self.session.stroke_rate_trend,
                estimated_distance_m=self.session.estimated_distance_m,
            )

            system = SystemState(
                is_swimming=self.system.is_swimming,
                pose_detected=self.system.pose_detected,
                voice_state=self.system.voice_state,
            )

            return StateUpdate(session=session, system=system)

    def _calculate_trend(self) -> str:
        """Calculate stroke rate trend from history.

        Returns:
            "increasing", "decreasing", or "stable"
        """
        if len(self._stroke_rate_history) < 4:
            return "stable"

        recent = self._stroke_rate_history[-4:]
        diffs = [recent[i + 1] - recent[i] for i in range(len(recent) - 1)]
        avg_diff = sum(diffs) / len(diffs)

        if avg_diff > 1.0:
            return "increasing"
        elif avg_diff < -1.0:
            return "decreasing"
        else:
            return "stable"
