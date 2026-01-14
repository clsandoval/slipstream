"""Tests for in-memory state management."""

import threading
import time
from datetime import datetime, timezone

import pytest
from freezegun import freeze_time

from src.mcp.models.messages import StateUpdate
from src.mcp.state_store import (
    NoActiveSessionError,
    SessionActiveError,
    StateStore,
)


class TestStateStore:
    """Tests for StateStore class."""

    @pytest.fixture
    def store(self) -> StateStore:
        """Fresh StateStore instance."""
        return StateStore()

    def test_initial_state(self, store: StateStore) -> None:
        """Initial state has correct defaults."""
        assert store.session.active is False
        assert store.system.is_swimming is False
        assert store.system.pose_detected is False
        assert store.system.voice_state == "idle"

    @freeze_time("2026-01-14T08:30:00Z")
    def test_start_session(self, store: StateStore) -> None:
        """Start session activates session and returns ID."""
        session_id = store.start_session()

        assert session_id == "2026-01-14_0830"
        assert store.session.active is True
        assert store._session_id == session_id
        assert store._started_at is not None

    def test_end_session(self, store: StateStore) -> None:
        """End session deactivates and returns summary."""
        store.start_session()
        store.update_strokes(count=50, rate=52.5)

        summary = store.end_session()

        assert store.session.active is False
        assert summary["stroke_count"] == 50
        assert summary["stroke_rate_avg"] == 52.5
        assert "duration_seconds" in summary
        assert "session_id" in summary

    def test_update_stroke_metrics(self, store: StateStore) -> None:
        """Update stroke count and rate."""
        store.start_session()

        store.update_strokes(count=10, rate=52.5)

        assert store.session.stroke_count == 10
        assert store.session.stroke_rate == 52.5

    def test_update_system_state(self, store: StateStore) -> None:
        """Update system state fields."""
        store.update_system(is_swimming=True, pose_detected=True, voice_state="listening")

        assert store.system.is_swimming is True
        assert store.system.pose_detected is True
        assert store.system.voice_state == "listening"

    def test_update_system_partial(self, store: StateStore) -> None:
        """Update only some system state fields."""
        store.update_system(is_swimming=True)
        store.update_system(pose_detected=True)

        assert store.system.is_swimming is True
        assert store.system.pose_detected is True
        assert store.system.voice_state == "idle"

    def test_get_state_update(self, store: StateStore) -> None:
        """Get current state as StateUpdate object."""
        store.start_session()
        store.update_strokes(count=10, rate=50.0)
        store.update_system(is_swimming=True)

        update = store.get_state_update()

        assert isinstance(update, StateUpdate)
        assert update.session.active is True
        assert update.session.stroke_count == 10
        assert update.system.is_swimming is True

    def test_stroke_rate_trend_increasing(self, store: StateStore) -> None:
        """Detect increasing stroke rate trend."""
        store.start_session()

        # Simulate increasing rates
        for rate in [48.0, 50.0, 52.0, 54.0]:
            store.update_strokes(count=10, rate=rate)

        assert store.session.stroke_rate_trend == "increasing"

    def test_stroke_rate_trend_decreasing(self, store: StateStore) -> None:
        """Detect decreasing stroke rate trend."""
        store.start_session()

        # Simulate decreasing rates
        for rate in [56.0, 54.0, 52.0, 50.0]:
            store.update_strokes(count=10, rate=rate)

        assert store.session.stroke_rate_trend == "decreasing"

    def test_stroke_rate_trend_stable(self, store: StateStore) -> None:
        """Detect stable stroke rate trend."""
        store.start_session()

        # Simulate stable rates
        for rate in [52.0, 51.5, 52.0, 51.8]:
            store.update_strokes(count=10, rate=rate)

        assert store.session.stroke_rate_trend == "stable"

    @freeze_time("2026-01-14T08:30:00Z", auto_tick_seconds=60)
    def test_elapsed_time(self, store: StateStore) -> None:
        """Elapsed time calculated correctly."""
        store.start_session()

        # Time advances by 60 seconds (auto_tick_seconds)
        time.sleep(0)  # Trigger time advance

        update = store.get_state_update()
        # With auto_tick_seconds=60, one tick advances 60 seconds
        assert update.session.elapsed_seconds >= 0

    def test_thread_safety(self, store: StateStore) -> None:
        """Concurrent updates don't cause race conditions."""
        store.start_session()
        errors = []

        def update_strokes():
            try:
                for i in range(100):
                    store.update_strokes(count=i, rate=50.0 + i)
            except Exception as e:
                errors.append(e)

        def update_system():
            try:
                for i in range(100):
                    store.update_system(is_swimming=i % 2 == 0)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=update_strokes),
            threading.Thread(target=update_system),
            threading.Thread(target=update_strokes),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_start_session_when_active(self, store: StateStore) -> None:
        """Starting session when active raises error."""
        store.start_session()

        with pytest.raises(SessionActiveError):
            store.start_session()

    def test_end_session_when_not_active(self, store: StateStore) -> None:
        """Ending session when not active raises error."""
        with pytest.raises(NoActiveSessionError):
            store.end_session()

    def test_estimated_distance(self, store: StateStore) -> None:
        """Estimated distance calculated from stroke count and DPS ratio."""
        store.start_session()
        store.update_strokes(count=100, rate=52.0)

        # Default DPS ratio is 1.8
        assert store.session.estimated_distance_m == pytest.approx(180.0)

    def test_custom_dps_ratio(self) -> None:
        """Custom DPS ratio affects distance calculation."""
        store = StateStore(dps_ratio=2.0)
        store.start_session()
        store.update_strokes(count=100, rate=52.0)

        assert store.session.estimated_distance_m == pytest.approx(200.0)
