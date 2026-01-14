"""Mock transcript stream for testing."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Iterator


_sequence_counter = 0


def _next_sequence_id() -> int:
    """Get next sequence ID."""
    global _sequence_counter
    _sequence_counter += 1
    return _sequence_counter


def _reset_sequence_counter() -> None:
    """Reset sequence counter (for testing)."""
    global _sequence_counter
    _sequence_counter = 0


@dataclass
class Utterance:
    """
    A simulated voice utterance.

    Matches the format expected from the STT service.
    """

    text: str
    delay_seconds: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sequence_id: int = field(default_factory=_next_sequence_id)
    confidence: float = 0.95

    def to_dict(self) -> dict[str, Any]:
        """Convert to transcript log format."""
        return {
            "sequence_id": self.sequence_id,
            "timestamp": self.timestamp.isoformat(),
            "text": self.text,
            "confidence": self.confidence,
        }

    def to_log_line(self) -> str:
        """Convert to transcript.log line format."""
        return f"[{self.sequence_id}] {self.timestamp.isoformat()} | {self.text}"


class MockTranscriptStream:
    """
    Mock transcript stream for testing.

    Simulates STT output with controllable timing.
    """

    def __init__(self, utterances: list[Utterance] | None = None) -> None:
        self._utterances = list(utterances) if utterances else []
        self._index = 0

    def add(self, text: str, delay_seconds: float = 0.0) -> Utterance:
        """Add an utterance to the stream."""
        utterance = Utterance(text=text, delay_seconds=delay_seconds)
        self._utterances.append(utterance)
        return utterance

    def get_next(self) -> Utterance | None:
        """Get next utterance (blocking if delay specified)."""
        if self._index >= len(self._utterances):
            return None

        utterance = self._utterances[self._index]
        self._index += 1

        if utterance.delay_seconds > 0:
            time.sleep(utterance.delay_seconds)

        return utterance

    async def get_next_async(self) -> Utterance | None:
        """Get next utterance (async, respects delay)."""
        if self._index >= len(self._utterances):
            return None

        utterance = self._utterances[self._index]
        self._index += 1

        if utterance.delay_seconds > 0:
            await asyncio.sleep(utterance.delay_seconds)

        return utterance

    def reset(self) -> None:
        """Reset to beginning of stream."""
        self._index = 0

    def __iter__(self) -> Iterator[Utterance]:
        """Iterate over utterances."""
        self.reset()
        while True:
            utterance = self.get_next()
            if utterance is None:
                break
            yield utterance

    async def __aiter__(self) -> AsyncIterator[Utterance]:
        """Async iterate over utterances."""
        self.reset()
        while True:
            utterance = await self.get_next_async()
            if utterance is None:
                break
            yield utterance

    def __len__(self) -> int:
        """Number of utterances."""
        return len(self._utterances)

    @property
    def remaining(self) -> int:
        """Number of utterances remaining."""
        return len(self._utterances) - self._index
