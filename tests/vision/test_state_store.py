"""Tests for SwimState and StateStore."""

import threading
import time
from datetime import datetime

import pytest


class TestSwimState:
    """Tests for SwimState dataclass."""

    def test_default_values(self):
        """SwimState has sensible defaults."""
        from src.vision.state_store import SwimState

        state = SwimState()

        assert state.session_active is False
        assert state.session_start is None
        assert state.stroke_count == 0
        assert state.stroke_rate == 0.0
        assert state.rate_history == []  # Empty list, not trend
        assert state.last_stroke_time is None
        assert state.pose_detected is False
        assert state.is_swimming is False

    def test_rate_history_default_empty(self):
        """Rate history starts as empty list."""
        from src.vision.state_store import SwimState

        state = SwimState()
        assert state.rate_history == []
        assert isinstance(state.rate_history, list)

    def test_state_creation_with_values(self):
        """Can create state with custom values."""
        from src.vision.rate_calculator import RateSample
        from src.vision.state_store import SwimState

        now = datetime.now()
        rate_samples = [RateSample(timestamp=1.0, rate=60.0), RateSample(timestamp=2.0, rate=62.0)]
        state = SwimState(
            session_active=True,
            session_start=now,
            stroke_count=42,
            stroke_rate=65.5,
            rate_history=rate_samples,
            last_stroke_time=now,
            pose_detected=True,
            is_swimming=True,
        )

        assert state.session_active is True
        assert state.session_start == now
        assert state.stroke_count == 42
        assert state.stroke_rate == 65.5
        assert len(state.rate_history) == 2
        assert state.rate_history[0].rate == 60.0
        assert state.last_stroke_time == now
        assert state.pose_detected is True
        assert state.is_swimming is True


class TestStateStore:
    """Tests for StateStore."""

    def test_initial_state(self):
        """Store starts with default state."""
        from src.vision.state_store import StateStore, SwimState

        store = StateStore()
        state = store.get_state()

        assert isinstance(state, SwimState)
        assert state.session_active is False

    def test_atomic_update(self):
        """Updates are atomic and complete."""
        from src.vision.state_store import StateStore

        store = StateStore()

        store.update(stroke_count=10, stroke_rate=60.0)

        state = store.get_state()
        assert state.stroke_count == 10
        assert state.stroke_rate == 60.0

    def test_start_session(self):
        """Start session initializes correctly."""
        from src.vision.state_store import StateStore

        store = StateStore()

        before = datetime.now()
        store.start_session()
        after = datetime.now()

        state = store.get_state()
        assert state.session_active is True
        assert before <= state.session_start <= after
        assert state.stroke_count == 0
        assert state.stroke_rate == 0.0

    def test_end_session_returns_final_state(self):
        """End session returns snapshot and resets."""
        from src.vision.state_store import StateStore

        store = StateStore()
        store.start_session()
        store.update(stroke_count=50, stroke_rate=62.0)

        final_state = store.end_session()

        # Final state should have session data
        assert final_state.stroke_count == 50
        assert final_state.stroke_rate == 62.0
        assert final_state.session_active is False  # Marked as ended

        # Store should be reset
        current_state = store.get_state()
        assert current_state.session_active is False
        assert current_state.stroke_count == 0

    def test_thread_safety(self):
        """Concurrent access is safe."""
        from src.vision.state_store import StateStore

        store = StateStore()
        store.start_session()
        errors = []

        def writer():
            try:
                for i in range(100):
                    store.update(stroke_count=i, stroke_rate=float(i))
            except Exception as e:
                errors.append(e)

        def reader():
            try:
                for _ in range(100):
                    state = store.get_state()
                    # Just access values
                    _ = state.stroke_count
                    _ = state.stroke_rate
            except Exception as e:
                errors.append(e)

        threads = []
        for _ in range(3):
            threads.append(threading.Thread(target=writer))
            threads.append(threading.Thread(target=reader))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_get_state_returns_copy(self):
        """get_state returns a copy, not a reference."""
        from src.vision.state_store import StateStore

        store = StateStore()
        store.update(stroke_count=10)

        state1 = store.get_state()
        state1.stroke_count = 999  # Modify local copy

        state2 = store.get_state()
        assert state2.stroke_count == 10  # Original unchanged

    def test_update_preserves_unmodified_fields(self):
        """Partial updates preserve other fields."""
        from src.vision.state_store import StateStore

        store = StateStore()
        store.start_session()
        store.update(stroke_count=10)
        store.update(stroke_rate=65.0)

        state = store.get_state()
        assert state.session_active is True
        assert state.stroke_count == 10
        assert state.stroke_rate == 65.0

    def test_update_last_stroke_time(self):
        """Can update last_stroke_time."""
        from src.vision.state_store import StateStore

        store = StateStore()
        now = datetime.now()

        store.update(last_stroke_time=now)

        state = store.get_state()
        assert state.last_stroke_time == now
