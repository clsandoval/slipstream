"""Mock vision state store for testing."""

from __future__ import annotations

import asyncio
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class MockVisionState:
    """Mock vision state matching real SwimState interface from vision.state_store."""

    # Core metrics
    is_swimming: bool = False
    stroke_count: int = 0
    stroke_rate: float = 0.0
    pose_detected: bool = False

    # Session tracking (needed for MetricBridge compatibility)
    session_active: bool = False
    session_start: datetime | None = None
    rate_history: list = field(default_factory=list)
    last_stroke_time: datetime | None = None

    # Extra fields for testing
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MockVisionStateStore:
    """
    Mock vision state store for testing.

    Provides controllable vision state without requiring
    actual camera/pose estimation hardware.

    Thread-safe for use in async contexts.
    """

    def __init__(self) -> None:
        self._state = MockVisionState()
        self._lock = threading.Lock()
        self._swimming_task: asyncio.Task[None] | None = None

    def get_state(self) -> MockVisionState:
        """Get current vision state."""
        with self._lock:
            return MockVisionState(
                is_swimming=self._state.is_swimming,
                stroke_count=self._state.stroke_count,
                stroke_rate=self._state.stroke_rate,
                pose_detected=self._state.pose_detected,
                session_active=self._state.session_active,
                session_start=self._state.session_start,
                rate_history=list(self._state.rate_history),
                last_stroke_time=self._state.last_stroke_time,
                confidence=self._state.confidence,
                timestamp=datetime.now(timezone.utc),
            )

    def start_session(self) -> None:
        """Start a session (for MetricBridge compatibility)."""
        with self._lock:
            self._state.session_active = True
            # Use timezone-naive datetime to match MetricBridge expectation
            self._state.session_start = datetime.now()
            self._state.stroke_count = 0
            self._state.stroke_rate = 0.0
            self._state.rate_history = []

    def end_session(self) -> MockVisionState:
        """End session and return final state."""
        with self._lock:
            self._state.session_active = False
            final_state = MockVisionState(
                is_swimming=self._state.is_swimming,
                stroke_count=self._state.stroke_count,
                stroke_rate=self._state.stroke_rate,
                pose_detected=self._state.pose_detected,
                session_active=False,
                session_start=self._state.session_start,
                rate_history=list(self._state.rate_history),
                last_stroke_time=self._state.last_stroke_time,
                confidence=self._state.confidence,
                timestamp=datetime.now(timezone.utc),
            )
            return final_state

    def set_swimming(self, is_swimming: bool) -> None:
        """Set swimming state."""
        with self._lock:
            self._state.is_swimming = is_swimming
            self._state.pose_detected = is_swimming

    def set_stroke_count(self, count: int) -> None:
        """Set stroke count."""
        with self._lock:
            self._state.stroke_count = count

    def set_stroke_rate(self, rate: float) -> None:
        """Set stroke rate."""
        with self._lock:
            self._state.stroke_rate = rate

    def increment_strokes(self, count: int = 1) -> None:
        """Increment stroke count."""
        with self._lock:
            self._state.stroke_count += count

    async def simulate_swimming(
        self,
        duration_seconds: float,
        stroke_rate: float = 50.0,
        start_strokes: int | None = None,
    ) -> None:
        """
        Simulate a swimming burst.

        Args:
            duration_seconds: How long to swim
            stroke_rate: Strokes per minute
            start_strokes: Starting stroke count (None = keep current)
        """
        with self._lock:
            self._state.is_swimming = True
            self._state.pose_detected = True
            self._state.stroke_rate = stroke_rate
            if start_strokes is not None:
                self._state.stroke_count = start_strokes
            initial_strokes = self._state.stroke_count

        strokes_per_second = stroke_rate / 60.0
        elapsed = 0.0
        interval = 0.1  # Update every 100ms
        accumulated_strokes = 0.0

        while elapsed < duration_seconds:
            await asyncio.sleep(interval)
            elapsed += interval
            accumulated_strokes += strokes_per_second * interval

            with self._lock:
                self._state.stroke_count = initial_strokes + int(accumulated_strokes)

        with self._lock:
            self._state.is_swimming = False

    def reset(self) -> None:
        """Reset to default state."""
        with self._lock:
            self._state = MockVisionState()
