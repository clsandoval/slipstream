"""Tests for mock infrastructure."""

import pytest
import asyncio
import time
from datetime import datetime, timezone

from verification.mocks.vision import MockVisionStateStore
from verification.mocks.transcript import (
    MockTranscriptStream,
    Utterance,
    _reset_sequence_counter,
)


class TestMockVisionStateStore:
    """Test mock vision state store."""

    def test_default_state(self):
        """Test 1: Default state has expected values."""
        store = MockVisionStateStore()
        state = store.get_state()

        assert state.is_swimming is False
        assert state.stroke_count == 0
        assert state.stroke_rate == 0.0
        assert state.pose_detected is False
        assert state.confidence == 0.0

    def test_set_swimming(self):
        """Test 2: Set swimming state."""
        store = MockVisionStateStore()

        store.set_swimming(True)
        state = store.get_state()

        assert state.is_swimming is True
        assert state.pose_detected is True  # Swimming implies pose detected

    def test_set_stroke_count(self):
        """Test 3: Set stroke count."""
        store = MockVisionStateStore()

        store.set_stroke_count(50)
        state = store.get_state()

        assert state.stroke_count == 50

    def test_set_stroke_rate(self):
        """Test 4: Set stroke rate."""
        store = MockVisionStateStore()

        store.set_stroke_rate(52.5)
        state = store.get_state()

        assert state.stroke_rate == 52.5

    def test_increment_strokes(self):
        """Test 5: Increment strokes."""
        store = MockVisionStateStore()

        store.set_stroke_count(10)
        store.increment_strokes(5)
        state = store.get_state()

        assert state.stroke_count == 15

    @pytest.mark.asyncio
    async def test_simulate_swimming_burst(self):
        """Test 6: Simulate swimming burst increments strokes over time."""
        store = MockVisionStateStore()

        # Short burst: 120 spm = 2 strokes/sec, 0.5 sec = 1 stroke minimum
        await store.simulate_swimming(
            duration_seconds=0.5, stroke_rate=120.0, start_strokes=0
        )

        state = store.get_state()
        assert state.is_swimming is False  # Should be off after simulation
        assert state.stroke_count > 0  # Should have accumulated strokes

    def test_reset(self):
        """Test 7: Reset returns to default state."""
        store = MockVisionStateStore()

        store.set_swimming(True)
        store.set_stroke_count(100)
        store.set_stroke_rate(55.0)

        store.reset()
        state = store.get_state()

        assert state.is_swimming is False
        assert state.stroke_count == 0
        assert state.stroke_rate == 0.0

    def test_interface_compatibility(self):
        """Test 8: Mock is compatible with expected interface."""
        store = MockVisionStateStore()

        # Should have these methods (duck typing)
        assert hasattr(store, "get_state")
        assert hasattr(store, "set_swimming")
        assert hasattr(store, "set_stroke_count")
        assert hasattr(store, "set_stroke_rate")

        # get_state should return object with expected attributes
        state = store.get_state()
        assert hasattr(state, "is_swimming")
        assert hasattr(state, "stroke_count")
        assert hasattr(state, "stroke_rate")
        assert hasattr(state, "timestamp")


class TestMockTranscriptStream:
    """Test mock transcript stream."""

    def setup_method(self):
        """Reset sequence counter before each test."""
        _reset_sequence_counter()

    def test_create_with_utterances(self):
        """Test 9: Create stream with utterances."""
        utterances = [
            Utterance(text="first"),
            Utterance(text="second"),
            Utterance(text="third"),
        ]
        stream = MockTranscriptStream(utterances)

        assert len(stream) == 3

    def test_get_next(self):
        """Test 10: Get next returns utterances in order."""
        stream = MockTranscriptStream()
        stream.add("first")
        stream.add("second")
        stream.add("third")

        assert stream.get_next().text == "first"
        assert stream.get_next().text == "second"
        assert stream.get_next().text == "third"

    def test_get_next_empty(self):
        """Test 11: Get next returns None when empty."""
        stream = MockTranscriptStream()
        stream.add("only one")

        stream.get_next()  # Consume
        result = stream.get_next()

        assert result is None

    def test_utterance_delay(self):
        """Test 12: Utterance with delay waits."""
        stream = MockTranscriptStream()
        stream.add("delayed", delay_seconds=0.1)

        start = time.time()
        stream.get_next()
        elapsed = time.time() - start

        assert elapsed >= 0.1

    def test_reset(self):
        """Test 13: Reset allows re-iteration."""
        stream = MockTranscriptStream()
        stream.add("first")
        stream.add("second")

        stream.get_next()
        stream.get_next()
        assert stream.get_next() is None

        stream.reset()
        assert stream.get_next().text == "first"

    @pytest.mark.asyncio
    async def test_async_iteration(self):
        """Test 14: Async iteration yields all utterances."""
        stream = MockTranscriptStream()
        stream.add("one")
        stream.add("two")
        stream.add("three")

        texts = []
        async for utterance in stream:
            texts.append(utterance.text)

        assert texts == ["one", "two", "three"]

    def test_utterance_format(self):
        """Test 15: Utterance to_dict matches expected format."""
        utterance = Utterance(text="what's my stroke rate")
        result = utterance.to_dict()

        assert "sequence_id" in result
        assert "timestamp" in result
        assert "text" in result
        assert result["text"] == "what's my stroke rate"
        assert "confidence" in result


class TestUtterance:
    """Test Utterance data model."""

    def setup_method(self):
        """Reset sequence counter before each test."""
        _reset_sequence_counter()

    def test_create_utterance(self):
        """Test 16: Create utterance with text."""
        utterance = Utterance(text="what's my stroke rate")

        assert utterance.text == "what's my stroke rate"
        assert utterance.timestamp is not None
        assert isinstance(utterance.timestamp, datetime)

    def test_custom_timestamp(self):
        """Test 17: Utterance with custom timestamp."""
        custom_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        utterance = Utterance(text="test", timestamp=custom_time)

        assert utterance.timestamp == custom_time

    def test_sequence_id(self):
        """Test 18: Utterances have incrementing sequence IDs."""
        u1 = Utterance(text="first")
        u2 = Utterance(text="second")
        u3 = Utterance(text="third")

        assert u2.sequence_id == u1.sequence_id + 1
        assert u3.sequence_id == u2.sequence_id + 1

    def test_to_log_line(self):
        """Test utterance can be formatted as log line."""
        utterance = Utterance(text="hello")
        line = utterance.to_log_line()

        assert utterance.text in line
        assert str(utterance.sequence_id) in line
