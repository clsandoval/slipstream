"""State storage for swim session data."""

import threading
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.vision.rate_calculator import RateSample


@dataclass
class SwimState:
    """Core state for a swimming session."""

    session_active: bool = False
    session_start: datetime | None = None
    stroke_count: int = 0
    stroke_rate: float = 0.0
    rate_history: list["RateSample"] = field(default_factory=list)  # For trend analysis
    last_stroke_time: datetime | None = None
    pose_detected: bool = False
    is_swimming: bool = False

    # Note: No trend field - Claude derives trends from rate_history


class StateStore:
    """
    Thread-safe state container for swim session data.

    Provides atomic updates and read access for:
    - Vision pipeline (writes state)
    - MCP server (reads state)
    - WebSocket publisher (reads state)
    """

    def __init__(self) -> None:
        """Initialize state store with default state."""
        self._state = SwimState()
        self._lock = threading.RLock()

    def get_state(self) -> SwimState:
        """
        Get a snapshot of current state.

        Returns a copy to prevent external modification.
        """
        with self._lock:
            # Create a copy with a new list for rate_history
            return replace(self._state, rate_history=list(self._state.rate_history))

    def update(self, **kwargs: Any) -> None:
        """
        Update state fields atomically.

        Args:
            **kwargs: Fields to update (e.g., stroke_count=10)
        """
        with self._lock:
            self._state = replace(self._state, **kwargs)

    def start_session(self) -> None:
        """Initialize a new session."""
        with self._lock:
            self._state = SwimState(
                session_active=True,
                session_start=datetime.now(),
                stroke_count=0,
                stroke_rate=0.0,
                rate_history=[],
                last_stroke_time=None,
                pose_detected=False,
                is_swimming=False,
            )

    def end_session(self) -> SwimState:
        """
        End session and return final state.

        Returns:
            Final state snapshot before reset
        """
        with self._lock:
            # Mark session as ended and capture final state
            self._state = replace(self._state, session_active=False)
            final_state = replace(self._state, rate_history=list(self._state.rate_history))

            # Reset to default
            self._state = SwimState()

            return final_state
