"""Workout data models.

Defines core data structures for structured workout management:
- WorkoutSegment: A single segment (warmup, work, rest, cooldown)
- Workout: A complete workout plan with multiple segments
- WorkoutState: Current execution state of a workout
- SegmentResult: Result of a completed segment
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal


class WorkoutPhase(Enum):
    """Workout lifecycle phases."""

    NO_WORKOUT = "no_workout"
    CREATED = "created"
    ACTIVE = "active"
    COMPLETE = "complete"


SegmentType = Literal["warmup", "work", "rest", "cooldown"]


@dataclass
class WorkoutSegment:
    """
    A single segment within a workout.

    Each segment has a type and optional targets for duration,
    distance, or stroke rate.
    """

    type: SegmentType
    target_duration_seconds: int | None = None
    target_distance_m: int | None = None
    target_stroke_rate: tuple[int, int] | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "type": self.type,
            "target_duration_seconds": self.target_duration_seconds,
            "target_distance_m": self.target_distance_m,
            "target_stroke_rate": (
                list(self.target_stroke_rate) if self.target_stroke_rate else None
            ),
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkoutSegment:
        """Create from dictionary."""
        stroke_rate = data.get("target_stroke_rate")
        return cls(
            type=data["type"],
            target_duration_seconds=data.get("target_duration_seconds"),
            target_distance_m=data.get("target_distance_m"),
            target_stroke_rate=tuple(stroke_rate) if stroke_rate else None,
            notes=data.get("notes", ""),
        )


def _generate_workout_id() -> str:
    """Generate unique workout ID."""
    return datetime.now(timezone.utc).strftime("wkt_%Y%m%d_%H%M%S")


@dataclass
class Workout:
    """
    A complete workout plan with multiple segments.
    """

    name: str
    segments: list[WorkoutSegment]
    workout_id: str = field(default_factory=_generate_workout_id)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "claude"

    @property
    def total_duration_seconds(self) -> int:
        """Sum of all segment durations (where defined)."""
        return sum(s.target_duration_seconds or 0 for s in self.segments)

    @property
    def total_distance_m(self) -> int:
        """Sum of all segment distances (where defined)."""
        return sum(s.target_distance_m or 0 for s in self.segments)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "workout_id": self.workout_id,
            "name": self.name,
            "segments": [s.to_dict() for s in self.segments],
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Workout:
        """Create from dictionary."""
        return cls(
            workout_id=data["workout_id"],
            name=data["name"],
            segments=[WorkoutSegment.from_dict(s) for s in data["segments"]],
            created_at=datetime.fromisoformat(data["created_at"]),
            created_by=data.get("created_by", "claude"),
        )


@dataclass
class SegmentResult:
    """
    Result of a completed segment.
    """

    segment_index: int
    segment_type: SegmentType
    started_at: datetime
    ended_at: datetime
    actual_duration_seconds: int
    actual_distance_m: float
    stroke_count: int
    avg_stroke_rate: float
    skipped: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "segment_index": self.segment_index,
            "segment_type": self.segment_type,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat(),
            "actual_duration_seconds": self.actual_duration_seconds,
            "actual_distance_m": self.actual_distance_m,
            "stroke_count": self.stroke_count,
            "avg_stroke_rate": self.avg_stroke_rate,
            "skipped": self.skipped,
        }


@dataclass
class WorkoutState:
    """
    Current state of an executing workout.
    """

    workout: Workout
    current_segment_idx: int = 0
    segment_started_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    segment_stroke_count_start: int = 0
    total_started_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    segments_completed: list[SegmentResult] = field(default_factory=list)
    phase: WorkoutPhase = WorkoutPhase.ACTIVE

    @property
    def current_segment(self) -> WorkoutSegment:
        """Get current segment."""
        return self.workout.segments[self.current_segment_idx]

    @property
    def next_segment(self) -> WorkoutSegment | None:
        """Get next segment, or None if at end."""
        next_idx = self.current_segment_idx + 1
        if next_idx < len(self.workout.segments):
            return self.workout.segments[next_idx]
        return None

    @property
    def is_last_segment(self) -> bool:
        """Check if on last segment."""
        return self.current_segment_idx >= len(self.workout.segments) - 1

    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage."""
        total = len(self.workout.segments)
        completed = len(self.segments_completed)
        return (completed / total) * 100 if total > 0 else 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "workout": self.workout.to_dict(),
            "current_segment_idx": self.current_segment_idx,
            "segment_started_at": self.segment_started_at.isoformat(),
            "total_started_at": self.total_started_at.isoformat(),
            "segments_completed": [s.to_dict() for s in self.segments_completed],
            "phase": self.phase.value,
        }
