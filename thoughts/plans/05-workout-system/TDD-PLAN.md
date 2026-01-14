# Workout System - TDD Implementation Plan

## Overview

Test-Driven Development plan for Branch 5: Workout System. Complete workout/interval system with MCP tools, state machine, and automatic segment transitions.

**Dependencies**: Branch 2 (mcp-server-core) + Branch 4 (swim-metrics)
**Complexity**: High

---

## Architecture

The workout system adds structured workout management on top of the existing session infrastructure.

```
+----------------------------------------------------------------------------------+
|                         WORKOUT SYSTEM ARCHITECTURE                              |
|                                                                                  |
|  Existing MCP Infrastructure         Workout Module                              |
|  +-----------------------+           +----------------------------------------+  |
|  | src/mcp/              |           | src/mcp/workout/                       |  |
|  | state_store.py        |<--------->| models.py                              |  |
|  |   SessionState        |  extends  |   WorkoutSegment, Workout,             |  |
|  |   SystemState         |           |   WorkoutState, SegmentResult          |  |
|  |                       |           |                                        |  |
|  | tools/                |           | state_machine.py                       |  |
|  |   session_tools.py    |           |   NO_WORKOUT -> CREATED -> ACTIVE ->   |  |
|  |   swim_tools.py       |           |   COMPLETE                             |  |
|  |                       |           |                                        |  |
|  | models/messages.py    |<--------->| tools.py                               |  |
|  |   StateUpdate         |  extends  |   create_workout, start_workout,       |  |
|  +-----------------------+           |   get_workout_status, skip_segment,    |  |
|                                      |   end_workout, list_workout_templates  |  |
|                                      |                                        |  |
|  Vision Pipeline                     | transitions.py                         |  |
|  +-----------------------+           |   Auto-advance based on:               |  |
|  | src/vision/           |---------->|   - Duration elapsed                   |  |
|  | state_store.py        |  reads    |   - Distance reached                   |  |
|  |   is_swimming         |           |   - Swimming start/stop                |  |
|  |   stroke_count        |           |                                        |  |
|  +-----------------------+           | templates.py                           |  |
|                                      |   Template CRUD operations             |  |
|                                      +----------------------------------------+  |
+----------------------------------------------------------------------------------+
```

### Key Design Decisions

1. **Separate WorkoutState**: Workouts are managed separately from sessions. A workout can span multiple sessions or be part of one session.

2. **State Machine**: Clear state transitions prevent invalid operations (can't skip segment if no workout active).

3. **Auto-Transitions**: Monitor vision state for duration/distance/swimming to auto-advance segments. Configurable thresholds.

4. **Template Storage**: Save workouts as templates for reuse. Stored in `~/.slipstream/templates/`.

5. **WebSocket Integration**: Extend `StateUpdate` to include workout state for dashboard display.

---

## Phase 1: Workout Models

**Goal**: Define core data models for workouts.

### Tests First (`tests/mcp/workout/test_models.py`)

```python
import pytest
from datetime import datetime, timezone
from src.mcp.workout.models import (
    WorkoutSegment,
    Workout,
    WorkoutState,
    SegmentResult,
    WorkoutPhase,
)


class TestWorkoutSegment:
    """Test WorkoutSegment data model."""

    # Test 1: Create segment with duration target
    def test_segment_with_duration(self):
        # Given segment type "work" with 4-minute duration
        # When WorkoutSegment created
        # Then target_duration_seconds=240, target_distance_m=None

    # Test 2: Create segment with distance target
    def test_segment_with_distance(self):
        # Given segment type "work" with 100m target
        # When WorkoutSegment created
        # Then target_distance_m=100, target_duration_seconds=None

    # Test 3: Create segment with stroke rate target
    def test_segment_with_stroke_rate_range(self):
        # Given target_stroke_rate=(50, 55)
        # When WorkoutSegment created
        # Then target_stroke_rate is tuple (50, 55)

    # Test 4: Segment types validation
    @pytest.mark.parametrize("segment_type", ["warmup", "work", "rest", "cooldown"])
    def test_valid_segment_types(self, segment_type):
        # Given valid segment type
        # When WorkoutSegment created
        # Then no error raised

    # Test 5: Segment to_dict serialization
    def test_segment_to_dict(self):
        # Given WorkoutSegment with all fields
        # When to_dict() called
        # Then returns complete dictionary

    # Test 6: Segment from_dict deserialization
    def test_segment_from_dict(self):
        # Given dict with segment data
        # When WorkoutSegment.from_dict(data) called
        # Then creates correct WorkoutSegment


class TestWorkout:
    """Test Workout data model."""

    # Test 7: Create workout with segments
    def test_workout_creation(self):
        # Given name="4x100m Intervals" and list of segments
        # When Workout created
        # Then workout_id generated, created_at set, segments stored

    # Test 8: Workout ID format
    def test_workout_id_format(self):
        # When Workout created
        # Then workout_id matches pattern "wkt_YYYYMMDD_HHMMSS"

    # Test 9: Workout total duration estimate
    def test_workout_total_duration(self):
        # Given segments with durations [60, 240, 30, 240, 30, 240, 30, 60]
        # When total_duration_seconds calculated
        # Then returns sum of all durations (930)

    # Test 10: Workout total distance estimate
    def test_workout_total_distance(self):
        # Given segments with distances [None, 100, None, 100, None, 100, None, None]
        # When total_distance_m calculated
        # Then returns sum of non-None distances (300)

    # Test 11: Workout segment count
    def test_workout_segment_count(self):
        # Given workout with 8 segments
        # When len(workout.segments)
        # Then returns 8

    # Test 12: Workout to_dict serialization
    def test_workout_to_dict(self):
        # Given Workout with segments
        # When to_dict() called
        # Then returns complete dictionary with nested segments

    # Test 13: Workout from_dict deserialization
    def test_workout_from_dict(self):
        # Given dict with workout data
        # When Workout.from_dict(data) called
        # Then creates correct Workout with segments


class TestSegmentResult:
    """Test SegmentResult data model."""

    # Test 14: Create segment result
    def test_segment_result_creation(self):
        # Given completed segment data
        # When SegmentResult created
        # Then stores segment_index, type, actual_duration, actual_distance, etc.

    # Test 15: Segment result with stroke metrics
    def test_segment_result_with_strokes(self):
        # Given segment with 80 strokes at avg 52/min
        # When SegmentResult created
        # Then stores stroke_count=80, avg_stroke_rate=52

    # Test 16: Segment result skipped flag
    def test_segment_result_skipped(self):
        # Given user skipped segment
        # When SegmentResult created with skipped=True
        # Then skipped flag set, duration reflects actual time

    # Test 17: Segment result to_dict
    def test_segment_result_to_dict(self):
        # Given SegmentResult
        # When to_dict() called
        # Then returns complete dictionary


class TestWorkoutState:
    """Test WorkoutState data model."""

    # Test 18: Create workout state
    def test_workout_state_creation(self):
        # Given Workout and initial values
        # When WorkoutState created
        # Then current_segment_idx=0, phase=ACTIVE

    # Test 19: Workout state current segment accessor
    def test_current_segment(self):
        # Given WorkoutState with segment_idx=2
        # When current_segment property accessed
        # Then returns workout.segments[2]

    # Test 20: Workout state next segment accessor
    def test_next_segment(self):
        # Given WorkoutState with segment_idx=2, total 5 segments
        # When next_segment property accessed
        # Then returns workout.segments[3]

    # Test 21: Workout state next segment at end
    def test_next_segment_at_end(self):
        # Given WorkoutState at last segment
        # When next_segment property accessed
        # Then returns None

    # Test 22: Workout state is_last_segment
    def test_is_last_segment(self):
        # Given WorkoutState at last segment
        # When is_last_segment checked
        # Then returns True

    # Test 23: Workout state progress calculation
    def test_progress_percentage(self):
        # Given 5 segments, 2 completed
        # When progress calculated
        # Then returns 40%

    # Test 24: Workout state to_dict
    def test_workout_state_to_dict(self):
        # Given WorkoutState with completed segments
        # When to_dict() called
        # Then returns complete dictionary


class TestWorkoutPhase:
    """Test WorkoutPhase enum."""

    # Test 25: All phases defined
    def test_phases_defined(self):
        # When checking WorkoutPhase enum
        # Then NO_WORKOUT, CREATED, ACTIVE, COMPLETE exist
```

### Implementation

```python
# src/mcp/workout/models.py
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
            "target_stroke_rate": list(self.target_stroke_rate) if self.target_stroke_rate else None,
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
        return sum(
            s.target_duration_seconds or 0
            for s in self.segments
        )

    @property
    def total_distance_m(self) -> int:
        """Sum of all segment distances (where defined)."""
        return sum(
            s.target_distance_m or 0
            for s in self.segments
        )

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
    segment_started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    segment_stroke_count_start: int = 0
    total_started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
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
```

---

## Phase 2: State Machine

**Goal**: Implement workout lifecycle state machine.

### Tests First (`tests/mcp/workout/test_state_machine.py`)

```python
import pytest
from datetime import datetime, timezone
from src.mcp.workout.models import (
    Workout, WorkoutSegment, WorkoutState, WorkoutPhase, SegmentResult
)
from src.mcp.workout.state_machine import WorkoutStateMachine


class TestWorkoutStateMachine:
    """Test workout state machine transitions."""

    @pytest.fixture
    def sample_workout(self) -> Workout:
        """Create sample workout for tests."""
        return Workout(
            name="Test Workout",
            segments=[
                WorkoutSegment(type="warmup", target_duration_seconds=60),
                WorkoutSegment(type="work", target_distance_m=100),
                WorkoutSegment(type="rest", target_duration_seconds=30),
                WorkoutSegment(type="work", target_distance_m=100),
                WorkoutSegment(type="cooldown", target_duration_seconds=60),
            ]
        )

    @pytest.fixture
    def state_machine(self) -> WorkoutStateMachine:
        """Create state machine instance."""
        return WorkoutStateMachine()

    # Test 1: Initial state is NO_WORKOUT
    def test_initial_state(self, state_machine):
        # Given new state machine
        # When checking phase
        # Then phase is NO_WORKOUT

    # Test 2: Create workout transitions to CREATED
    def test_create_workout(self, state_machine, sample_workout):
        # Given NO_WORKOUT state
        # When create_workout(workout) called
        # Then phase becomes CREATED, workout stored

    # Test 3: Cannot create workout if one exists
    def test_create_workout_already_exists(self, state_machine, sample_workout):
        # Given CREATED state
        # When create_workout called again
        # Then raises WorkoutExistsError

    # Test 4: Start workout transitions to ACTIVE
    def test_start_workout(self, state_machine, sample_workout):
        # Given CREATED state
        # When start_workout() called
        # Then phase becomes ACTIVE, segment_started_at set

    # Test 5: Cannot start workout if not created
    def test_start_workout_not_created(self, state_machine):
        # Given NO_WORKOUT state
        # When start_workout() called
        # Then raises NoWorkoutError

    # Test 6: Cannot start already active workout
    def test_start_workout_already_active(self, state_machine, sample_workout):
        # Given ACTIVE state
        # When start_workout() called
        # Then raises WorkoutAlreadyActiveError

    # Test 7: Advance segment moves to next
    def test_advance_segment(self, state_machine, sample_workout):
        # Given ACTIVE workout on segment 0
        # When advance_segment() called
        # Then current_segment_idx becomes 1, result recorded

    # Test 8: Advance segment captures result
    def test_advance_segment_captures_result(self, state_machine, sample_workout):
        # Given ACTIVE workout with stroke metrics
        # When advance_segment(stroke_count=50, distance=90.0) called
        # Then SegmentResult added to segments_completed

    # Test 9: Advance past last segment completes workout
    def test_advance_last_segment(self, state_machine, sample_workout):
        # Given ACTIVE workout on last segment
        # When advance_segment() called
        # Then phase becomes COMPLETE

    # Test 10: Skip segment marks as skipped
    def test_skip_segment(self, state_machine, sample_workout):
        # Given ACTIVE workout
        # When skip_segment() called
        # Then advances with skipped=True in result

    # Test 11: End workout early
    def test_end_workout(self, state_machine, sample_workout):
        # Given ACTIVE workout
        # When end_workout() called
        # Then phase becomes COMPLETE, returns summary

    # Test 12: End workout returns summary
    def test_end_workout_summary(self, state_machine, sample_workout):
        # Given ACTIVE workout with completed segments
        # When end_workout() called
        # Then returns dict with total_duration, segments_completed, etc.

    # Test 13: Get status returns current state
    def test_get_status(self, state_machine, sample_workout):
        # Given ACTIVE workout
        # When get_status() called
        # Then returns complete status dict

    # Test 14: Get status with no workout
    def test_get_status_no_workout(self, state_machine):
        # Given NO_WORKOUT state
        # When get_status() called
        # Then returns {"has_active_workout": False}

    # Test 15: Thread safety - concurrent operations
    def test_thread_safety(self, state_machine, sample_workout):
        # Given active workout
        # When multiple threads call advance_segment
        # Then no race conditions, consistent state


class TestWorkoutStateMachineErrors:
    """Test error conditions."""

    @pytest.fixture
    def state_machine(self) -> WorkoutStateMachine:
        return WorkoutStateMachine()

    # Test 16: Cannot advance in CREATED state
    def test_advance_not_active(self, state_machine):
        # Given CREATED state
        # When advance_segment() called
        # Then raises WorkoutNotActiveError

    # Test 17: Cannot advance in COMPLETE state
    def test_advance_complete(self, state_machine):
        # Given COMPLETE state
        # When advance_segment() called
        # Then raises WorkoutNotActiveError

    # Test 18: Cannot skip in COMPLETE state
    def test_skip_complete(self, state_machine):
        # Given COMPLETE state
        # When skip_segment() called
        # Then raises WorkoutNotActiveError

    # Test 19: Clear workout resets to NO_WORKOUT
    def test_clear_workout(self, state_machine):
        # Given COMPLETE state
        # When clear_workout() called
        # Then phase becomes NO_WORKOUT, workout cleared
```

### Implementation

```python
# src/mcp/workout/state_machine.py
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.mcp.workout.models import (
    Workout,
    WorkoutState,
    WorkoutPhase,
    SegmentResult,
)


class WorkoutExistsError(Exception):
    """Raised when creating workout but one already exists."""
    pass


class NoWorkoutError(Exception):
    """Raised when operation requires a workout but none exists."""
    pass


class WorkoutAlreadyActiveError(Exception):
    """Raised when starting a workout that's already active."""
    pass


class WorkoutNotActiveError(Exception):
    """Raised when operation requires active workout."""
    pass


@dataclass
class WorkoutStateMachine:
    """
    State machine for workout lifecycle.

    Manages transitions: NO_WORKOUT -> CREATED -> ACTIVE -> COMPLETE
    Thread-safe for concurrent access.
    """
    _workout: Workout | None = field(default=None, repr=False)
    _state: WorkoutState | None = field(default=None, repr=False)
    _phase: WorkoutPhase = field(default=WorkoutPhase.NO_WORKOUT)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    @property
    def phase(self) -> WorkoutPhase:
        """Current workout phase."""
        with self._lock:
            return self._phase

    @property
    def workout(self) -> Workout | None:
        """Current workout."""
        with self._lock:
            return self._workout

    @property
    def state(self) -> WorkoutState | None:
        """Current workout state."""
        with self._lock:
            return self._state

    def create_workout(self, workout: Workout) -> dict[str, Any]:
        """
        Create a new workout (does not start it).

        Args:
            workout: Workout to create

        Returns:
            Dict with workout_id and segment count

        Raises:
            WorkoutExistsError: If workout already exists
        """
        with self._lock:
            if self._phase != WorkoutPhase.NO_WORKOUT:
                raise WorkoutExistsError(
                    f"Cannot create workout: current phase is {self._phase.value}"
                )

            self._workout = workout
            self._phase = WorkoutPhase.CREATED

            return {
                "workout_id": workout.workout_id,
                "segments_count": len(workout.segments),
            }

    def start_workout(self) -> dict[str, Any]:
        """
        Begin executing the created workout.

        Returns:
            Dict with started_at, first_segment info

        Raises:
            NoWorkoutError: If no workout created
            WorkoutAlreadyActiveError: If workout already active
        """
        with self._lock:
            if self._phase == WorkoutPhase.NO_WORKOUT:
                raise NoWorkoutError("No workout created to start")
            if self._phase == WorkoutPhase.ACTIVE:
                raise WorkoutAlreadyActiveError("Workout already active")
            if self._phase == WorkoutPhase.COMPLETE:
                raise WorkoutAlreadyActiveError("Workout already complete")

            now = datetime.now(timezone.utc)
            self._state = WorkoutState(
                workout=self._workout,
                segment_started_at=now,
                total_started_at=now,
            )
            self._phase = WorkoutPhase.ACTIVE

            return {
                "started_at": now.isoformat(),
                "first_segment": self._state.current_segment.to_dict(),
                "total_segments": len(self._workout.segments),
            }

    def advance_segment(
        self,
        stroke_count: int = 0,
        distance_m: float = 0.0,
        avg_stroke_rate: float = 0.0,
        skipped: bool = False,
    ) -> dict[str, Any]:
        """
        Complete current segment and advance to next.

        Args:
            stroke_count: Strokes in this segment
            distance_m: Distance swum in this segment
            avg_stroke_rate: Average stroke rate
            skipped: Whether segment was skipped

        Returns:
            Dict with completed segment info and next segment

        Raises:
            WorkoutNotActiveError: If workout not active
        """
        with self._lock:
            if self._phase != WorkoutPhase.ACTIVE:
                raise WorkoutNotActiveError(
                    f"Cannot advance: phase is {self._phase.value}"
                )

            now = datetime.now(timezone.utc)

            # Record completed segment
            result = SegmentResult(
                segment_index=self._state.current_segment_idx,
                segment_type=self._state.current_segment.type,
                started_at=self._state.segment_started_at,
                ended_at=now,
                actual_duration_seconds=int(
                    (now - self._state.segment_started_at).total_seconds()
                ),
                actual_distance_m=distance_m,
                stroke_count=stroke_count,
                avg_stroke_rate=avg_stroke_rate,
                skipped=skipped,
            )
            self._state.segments_completed.append(result)

            completed_info = result.to_dict()

            # Check if workout complete
            if self._state.is_last_segment:
                self._phase = WorkoutPhase.COMPLETE
                return {
                    "completed": completed_info,
                    "workout_complete": True,
                    "now_on": None,
                }

            # Advance to next segment
            self._state.current_segment_idx += 1
            self._state.segment_started_at = now

            return {
                "completed": completed_info,
                "workout_complete": False,
                "now_on": self._state.current_segment.to_dict(),
            }

    def skip_segment(self) -> dict[str, Any]:
        """
        Skip current segment and advance to next.

        Returns:
            Same as advance_segment with skipped=True
        """
        return self.advance_segment(skipped=True)

    def end_workout(self) -> dict[str, Any]:
        """
        End workout early.

        Returns:
            Workout summary dict

        Raises:
            WorkoutNotActiveError: If no active workout
        """
        with self._lock:
            if self._phase not in (WorkoutPhase.ACTIVE, WorkoutPhase.COMPLETE):
                raise WorkoutNotActiveError(
                    f"Cannot end: phase is {self._phase.value}"
                )

            now = datetime.now(timezone.utc)
            total_duration = int(
                (now - self._state.total_started_at).total_seconds()
            )

            summary = {
                "workout_id": self._workout.workout_id,
                "workout_name": self._workout.name,
                "total_duration_seconds": total_duration,
                "segments_completed": len(self._state.segments_completed),
                "segments_total": len(self._workout.segments),
                "segments": [s.to_dict() for s in self._state.segments_completed],
                "ended_early": self._phase == WorkoutPhase.ACTIVE,
            }

            self._phase = WorkoutPhase.COMPLETE
            return summary

    def get_status(self) -> dict[str, Any]:
        """
        Get current workout status.

        Returns:
            Status dict with workout info or has_active_workout=False
        """
        with self._lock:
            if self._phase == WorkoutPhase.NO_WORKOUT:
                return {"has_active_workout": False}

            now = datetime.now(timezone.utc)

            status = {
                "has_active_workout": self._phase == WorkoutPhase.ACTIVE,
                "phase": self._phase.value,
                "workout_id": self._workout.workout_id,
                "workout_name": self._workout.name,
            }

            if self._state:
                segment_elapsed = int(
                    (now - self._state.segment_started_at).total_seconds()
                )
                total_elapsed = int(
                    (now - self._state.total_started_at).total_seconds()
                )

                status.update({
                    "current_segment": {
                        "index": self._state.current_segment_idx,
                        "type": self._state.current_segment.type,
                        "elapsed_seconds": segment_elapsed,
                        **self._state.current_segment.to_dict(),
                    },
                    "progress": {
                        "segments_completed": len(self._state.segments_completed),
                        "segments_total": len(self._workout.segments),
                        "percent": self._state.progress_percent,
                    },
                    "total_elapsed_seconds": total_elapsed,
                    "next_segment": (
                        self._state.next_segment.to_dict()
                        if self._state.next_segment
                        else None
                    ),
                })

            return status

    def clear_workout(self) -> None:
        """Reset to NO_WORKOUT state."""
        with self._lock:
            self._workout = None
            self._state = None
            self._phase = WorkoutPhase.NO_WORKOUT
```

---

## Phase 3: Auto-Transitions

**Goal**: Automatic segment transitions based on duration, distance, and swimming state.

### Tests First (`tests/mcp/workout/test_transitions.py`)

```python
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
from src.mcp.workout.models import Workout, WorkoutSegment, WorkoutPhase
from src.mcp.workout.state_machine import WorkoutStateMachine
from src.mcp.workout.transitions import TransitionMonitor


class TestTransitionMonitor:
    """Test automatic segment transitions."""

    @pytest.fixture
    def mock_vision_state(self):
        """Mock vision state store."""
        mock = Mock()
        mock.get_state.return_value = Mock(
            is_swimming=True,
            stroke_count=0,
        )
        return mock

    @pytest.fixture
    def workout_with_duration(self) -> Workout:
        """Workout with duration-based segments."""
        return Workout(
            name="Duration Test",
            segments=[
                WorkoutSegment(type="warmup", target_duration_seconds=60),
                WorkoutSegment(type="work", target_duration_seconds=120),
                WorkoutSegment(type="cooldown", target_duration_seconds=60),
            ]
        )

    @pytest.fixture
    def workout_with_distance(self) -> Workout:
        """Workout with distance-based segments."""
        return Workout(
            name="Distance Test",
            segments=[
                WorkoutSegment(type="warmup", target_duration_seconds=60),
                WorkoutSegment(type="work", target_distance_m=100),
                WorkoutSegment(type="rest", target_duration_seconds=30),
            ]
        )

    @pytest.fixture
    def state_machine(self) -> WorkoutStateMachine:
        return WorkoutStateMachine()

    # Test 1: Duration transition triggers on time elapsed
    def test_duration_transition(self, state_machine, workout_with_duration, mock_vision_state):
        # Given active workout, segment target_duration=60s
        # When 60+ seconds elapsed
        # Then should_transition() returns True with reason="duration_elapsed"

    # Test 2: Duration transition does not trigger early
    def test_duration_no_early_transition(self, state_machine, workout_with_duration, mock_vision_state):
        # Given active workout, segment target_duration=60s
        # When 30 seconds elapsed
        # Then should_transition() returns False

    # Test 3: Distance transition triggers on distance reached
    def test_distance_transition(self, state_machine, workout_with_distance, mock_vision_state):
        # Given active work segment, target_distance=100m
        # When stroke_count indicates 100m+ swum
        # Then should_transition() returns True with reason="distance_reached"

    # Test 4: Distance uses DPS ratio from config
    def test_distance_uses_dps_ratio(self, state_machine, workout_with_distance, mock_vision_state):
        # Given dps_ratio=2.0, target_distance=100m
        # When stroke_count=50 (50*2.0=100m)
        # Then should_transition() returns True

    # Test 5: Swimming stop triggers transition from work
    def test_swimming_stop_work_transition(self, state_machine, workout_with_distance, mock_vision_state):
        # Given active work segment
        # When is_swimming changes False -> True (swimmer stopped)
        # Then should_transition() returns True with reason="swimming_stopped"

    # Test 6: Swimming start triggers transition from rest
    def test_swimming_start_rest_transition(self, state_machine, workout_with_distance, mock_vision_state):
        # Given active rest segment
        # When is_swimming changes True (swimmer started)
        # Then should_transition() returns True with reason="swimming_started"

    # Test 7: Rest segment waits for duration OR swimming start
    def test_rest_segment_transitions(self, state_machine, mock_vision_state):
        # Given rest segment with 30s duration
        # When 25s elapsed but swimmer starts swimming
        # Then should_transition() returns True

    # Test 8: Warmup transitions on stop swimming
    def test_warmup_stop_swimming(self, state_machine, mock_vision_state):
        # Given warmup segment
        # When swimmer stops
        # Then should_transition() returns True

    # Test 9: Cooldown transitions on stop swimming
    def test_cooldown_stop_swimming(self, state_machine, mock_vision_state):
        # Given cooldown segment
        # When swimmer stops OR duration elapsed
        # Then should_transition() returns True

    # Test 10: Monitor check returns transition info
    def test_check_returns_info(self, state_machine, workout_with_duration, mock_vision_state):
        # Given transition should happen
        # When check() called
        # Then returns {"should_transition": True, "reason": "...", "metrics": {...}}

    # Test 11: Monitor ignores transitions when not active
    def test_ignores_inactive(self, state_machine, mock_vision_state):
        # Given CREATED or COMPLETE phase
        # When check() called
        # Then returns {"should_transition": False}

    # Test 12: Swimming state debounce
    def test_swimming_state_debounce(self, state_machine, mock_vision_state):
        # Given is_swimming flickering
        # When check() called rapidly
        # Then only triggers after stable state (e.g., 2 seconds)

    # Test 13: Grace period after segment start
    def test_segment_start_grace_period(self, state_machine, mock_vision_state):
        # Given segment just started (< 5 seconds ago)
        # When check() called
        # Then returns False (grace period)


class TestTransitionRules:
    """Test transition rules by segment type."""

    # Test 14: Warmup rules
    @pytest.mark.parametrize("trigger,expected", [
        ("duration_elapsed", True),
        ("swimming_stopped", True),
        ("swimming_started", False),
        ("distance_reached", False),
    ])
    def test_warmup_rules(self, trigger, expected):
        # Given warmup segment
        # When trigger condition met
        # Then transition expected or not

    # Test 15: Work rules
    @pytest.mark.parametrize("trigger,expected", [
        ("duration_elapsed", True),
        ("distance_reached", True),
        ("swimming_stopped", True),
        ("swimming_started", False),
    ])
    def test_work_rules(self, trigger, expected):
        # Given work segment
        # When trigger condition met
        # Then transition expected or not

    # Test 16: Rest rules
    @pytest.mark.parametrize("trigger,expected", [
        ("duration_elapsed", True),
        ("swimming_started", True),
        ("swimming_stopped", False),
        ("distance_reached", False),
    ])
    def test_rest_rules(self, trigger, expected):
        # Given rest segment
        # When trigger condition met
        # Then transition expected or not

    # Test 17: Cooldown rules
    @pytest.mark.parametrize("trigger,expected", [
        ("duration_elapsed", True),
        ("swimming_stopped", True),
        ("swimming_started", False),
        ("distance_reached", False),
    ])
    def test_cooldown_rules(self, trigger, expected):
        # Given cooldown segment
        # When trigger condition met
        # Then transition expected or not
```

### Implementation

```python
# src/mcp/workout/transitions.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from src.mcp.workout.models import WorkoutPhase
from src.mcp.workout.state_machine import WorkoutStateMachine

if TYPE_CHECKING:
    from src.vision.state_store import StateStore as VisionStateStore


# Transition rules by segment type
TRANSITION_RULES = {
    "warmup": {
        "triggers": ["duration_elapsed", "swimming_stopped"],
    },
    "work": {
        "triggers": ["duration_elapsed", "distance_reached", "swimming_stopped"],
    },
    "rest": {
        "triggers": ["duration_elapsed", "swimming_started"],
    },
    "cooldown": {
        "triggers": ["duration_elapsed", "swimming_stopped"],
    },
}


@dataclass
class TransitionMonitor:
    """
    Monitors conditions for automatic segment transitions.

    Checks vision state and elapsed time to determine when
    to advance to the next segment.
    """
    state_machine: WorkoutStateMachine
    vision_state_store: "VisionStateStore"
    dps_ratio: float = 1.8
    grace_period_seconds: float = 5.0
    swimming_debounce_seconds: float = 2.0
    _last_swimming_state: bool = field(default=False, repr=False)
    _swimming_state_changed_at: datetime | None = field(default=None, repr=False)

    def check(self) -> dict[str, Any]:
        """
        Check if transition should occur.

        Returns:
            Dict with should_transition, reason, and metrics
        """
        if self.state_machine.phase != WorkoutPhase.ACTIVE:
            return {"should_transition": False}

        state = self.state_machine.state
        if state is None:
            return {"should_transition": False}

        now = datetime.now(timezone.utc)
        segment = state.current_segment
        segment_type = segment.type
        rules = TRANSITION_RULES[segment_type]

        # Grace period check
        elapsed = (now - state.segment_started_at).total_seconds()
        if elapsed < self.grace_period_seconds:
            return {"should_transition": False, "reason": "grace_period"}

        vision = self.vision_state_store.get_state()

        # Calculate current metrics
        segment_strokes = vision.stroke_count - state.segment_stroke_count_start
        segment_distance = segment_strokes * self.dps_ratio

        metrics = {
            "elapsed_seconds": int(elapsed),
            "stroke_count": segment_strokes,
            "distance_m": round(segment_distance, 1),
            "is_swimming": vision.is_swimming,
        }

        # Check each trigger
        for trigger in rules["triggers"]:
            should_trigger, reason = self._check_trigger(
                trigger, segment, elapsed, segment_distance, vision.is_swimming
            )
            if should_trigger:
                return {
                    "should_transition": True,
                    "reason": reason,
                    "metrics": metrics,
                }

        return {
            "should_transition": False,
            "metrics": metrics,
        }

    def _check_trigger(
        self,
        trigger: str,
        segment: Any,
        elapsed: float,
        distance: float,
        is_swimming: bool,
    ) -> tuple[bool, str]:
        """Check if specific trigger condition is met."""
        if trigger == "duration_elapsed":
            if segment.target_duration_seconds:
                if elapsed >= segment.target_duration_seconds:
                    return True, "duration_elapsed"

        elif trigger == "distance_reached":
            if segment.target_distance_m:
                if distance >= segment.target_distance_m:
                    return True, "distance_reached"

        elif trigger == "swimming_stopped":
            if self._is_swimming_stopped_stable(is_swimming):
                return True, "swimming_stopped"

        elif trigger == "swimming_started":
            if self._is_swimming_started_stable(is_swimming):
                return True, "swimming_started"

        return False, ""

    def _is_swimming_stopped_stable(self, is_swimming: bool) -> bool:
        """Check if swimmer has stably stopped (debounced)."""
        now = datetime.now(timezone.utc)

        if is_swimming != self._last_swimming_state:
            self._last_swimming_state = is_swimming
            self._swimming_state_changed_at = now

        if not is_swimming and self._swimming_state_changed_at:
            stable_time = (now - self._swimming_state_changed_at).total_seconds()
            return stable_time >= self.swimming_debounce_seconds

        return False

    def _is_swimming_started_stable(self, is_swimming: bool) -> bool:
        """Check if swimmer has stably started (debounced)."""
        now = datetime.now(timezone.utc)

        if is_swimming != self._last_swimming_state:
            self._last_swimming_state = is_swimming
            self._swimming_state_changed_at = now

        if is_swimming and self._swimming_state_changed_at:
            stable_time = (now - self._swimming_state_changed_at).total_seconds()
            return stable_time >= self.swimming_debounce_seconds

        return False

    def get_metrics_for_advance(self) -> dict[str, Any]:
        """
        Get current metrics for segment completion.

        Returns:
            Dict with stroke_count, distance_m, avg_stroke_rate
        """
        state = self.state_machine.state
        if state is None:
            return {}

        vision = self.vision_state_store.get_state()
        segment_strokes = vision.stroke_count - state.segment_stroke_count_start

        return {
            "stroke_count": segment_strokes,
            "distance_m": round(segment_strokes * self.dps_ratio, 1),
            "avg_stroke_rate": vision.stroke_rate,
        }
```

---

## Phase 4: MCP Workout Tools

**Goal**: MCP tools for workout management.

### Tests First (`tests/mcp/workout/test_tools.py`)

```python
import pytest
from unittest.mock import Mock, MagicMock
from src.mcp.workout.models import Workout, WorkoutSegment


class TestWorkoutTools:
    """Test MCP workout tools."""

    @pytest.fixture
    def mock_state_machine(self):
        """Mock WorkoutStateMachine."""
        return Mock()

    @pytest.fixture
    def mock_template_storage(self):
        """Mock TemplateStorage."""
        return Mock()

    # Test 1: create_workout tool
    def test_create_workout_tool(self, mock_state_machine, mock_template_storage):
        # Given valid workout params
        # When create_workout(name, segments) called
        # Then state_machine.create_workout called with Workout

    # Test 2: create_workout validates segments
    def test_create_workout_validates_segments(self, mock_state_machine):
        # Given invalid segment type
        # When create_workout called
        # Then returns error dict

    # Test 3: create_workout saves template optionally
    def test_create_workout_saves_template(self, mock_state_machine, mock_template_storage):
        # Given save_as_template=True
        # When create_workout called
        # Then template_storage.save called

    # Test 4: start_workout tool
    def test_start_workout_tool(self, mock_state_machine):
        # Given created workout
        # When start_workout() called
        # Then state_machine.start_workout called

    # Test 5: get_workout_status tool
    def test_get_workout_status_tool(self, mock_state_machine):
        # Given active workout
        # When get_workout_status() called
        # Then returns state_machine.get_status()

    # Test 6: skip_segment tool
    def test_skip_segment_tool(self, mock_state_machine):
        # Given active workout
        # When skip_segment() called
        # Then state_machine.skip_segment called

    # Test 7: end_workout tool
    def test_end_workout_tool(self, mock_state_machine):
        # Given active workout
        # When end_workout() called
        # Then state_machine.end_workout called

    # Test 8: list_workout_templates tool
    def test_list_workout_templates_tool(self, mock_template_storage):
        # Given saved templates
        # When list_workout_templates(limit=5) called
        # Then returns template_storage.list(limit=5)

    # Test 9: Tool error handling
    def test_tool_error_handling(self, mock_state_machine):
        # Given state_machine raises WorkoutExistsError
        # When create_workout called
        # Then returns {"error": "..."} without crashing

    # Test 10: create_swim_tools factory
    def test_create_workout_tools_factory(self, mock_state_machine, mock_template_storage):
        # Given state_machine and template_storage
        # When create_workout_tools(...) called
        # Then returns list of 6 tool functions


class TestWorkoutToolsIntegration:
    """Integration tests with real components."""

    @pytest.fixture
    def integration_setup(self, temp_slipstream_dir):
        """Real components for integration tests."""
        from src.mcp.workout.state_machine import WorkoutStateMachine
        from src.mcp.workout.templates import TemplateStorage
        from src.mcp.workout.tools import create_workout_tools

        state_machine = WorkoutStateMachine()
        template_storage = TemplateStorage(temp_slipstream_dir / "templates")
        tools = create_workout_tools(state_machine, template_storage)

        return state_machine, template_storage, tools

    # Test 11: Full workflow - create, start, advance, end
    def test_full_workflow(self, integration_setup):
        # Given fresh state
        # When create_workout -> start_workout -> skip 3 times -> end_workout
        # Then each step succeeds, final summary correct

    # Test 12: Template save and load
    def test_template_round_trip(self, integration_setup):
        # Given create_workout with save_as_template=True
        # When list_workout_templates called
        # Then template appears in list

    # Test 13: Tool latency
    def test_tool_latency(self, integration_setup):
        # When calling tools 100 times
        # Then average latency < 100ms
```

### Implementation

```python
# src/mcp/workout/tools.py
from __future__ import annotations

from typing import Any, Callable

from src.mcp.workout.models import Workout, WorkoutSegment
from src.mcp.workout.state_machine import (
    WorkoutStateMachine,
    WorkoutExistsError,
    NoWorkoutError,
    WorkoutAlreadyActiveError,
    WorkoutNotActiveError,
)
from src.mcp.workout.templates import TemplateStorage


def create_workout_tools(
    state_machine: WorkoutStateMachine,
    template_storage: TemplateStorage,
) -> list[Callable]:
    """
    Create workout management tools for MCP registration.

    Args:
        state_machine: WorkoutStateMachine instance
        template_storage: TemplateStorage instance

    Returns:
        List of tool functions for MCP
    """

    def create_workout(
        name: str,
        segments: list[dict[str, Any]],
        save_as_template: bool = False,
    ) -> dict[str, Any]:
        """
        Create a workout plan (does not start it).

        Creates a structured workout with multiple segments. Each segment
        can target duration, distance, or stroke rate.

        Args:
            name: Workout name (e.g., "4x100m Intervals")
            segments: List of segment definitions with type and targets
            save_as_template: If True, save for future reuse

        Returns:
            workout_id: Unique ID for this workout
            segments_count: Number of segments created
        """
        try:
            # Validate and convert segments
            workout_segments = []
            for seg in segments:
                if seg.get("type") not in ("warmup", "work", "rest", "cooldown"):
                    return {"error": f"Invalid segment type: {seg.get('type')}"}
                workout_segments.append(WorkoutSegment.from_dict(seg))

            workout = Workout(name=name, segments=workout_segments)
            result = state_machine.create_workout(workout)

            if save_as_template:
                template_storage.save(workout)

            return result

        except WorkoutExistsError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    def start_workout() -> dict[str, Any]:
        """
        Begin executing a created workout.

        Transitions the workout from CREATED to ACTIVE state
        and starts tracking segment progress.

        Returns:
            started_at: ISO timestamp when workout started
            first_segment: Details of the first segment
            total_segments: Total number of segments
        """
        try:
            return state_machine.start_workout()
        except (NoWorkoutError, WorkoutAlreadyActiveError) as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    def get_workout_status() -> dict[str, Any]:
        """
        Get current workout execution status.

        Returns comprehensive status including current segment,
        progress, elapsed time, and next segment preview.

        Returns:
            has_active_workout: Whether a workout is running
            workout_name: Name of current workout
            current_segment: Current segment details
            progress: Completion progress
            next_segment: Next segment preview
        """
        try:
            return state_machine.get_status()
        except Exception as e:
            return {"error": str(e)}

    def skip_segment() -> dict[str, Any]:
        """
        Skip current segment and advance to next.

        Marks the current segment as skipped and immediately
        advances to the next segment (or completes workout).

        Returns:
            skipped: Details of skipped segment
            now_on: Details of new current segment (or None if complete)
        """
        try:
            result = state_machine.skip_segment()
            return {
                "skipped": result.get("completed"),
                "now_on": result.get("now_on"),
                "workout_complete": result.get("workout_complete", False),
            }
        except WorkoutNotActiveError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    def end_workout() -> dict[str, Any]:
        """
        End workout early.

        Terminates the current workout and returns a summary
        of completed segments.

        Returns:
            summary: Complete workout summary with all segment results
        """
        try:
            summary = state_machine.end_workout()
            state_machine.clear_workout()
            return {"summary": summary}
        except WorkoutNotActiveError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    def list_workout_templates(limit: int = 10) -> dict[str, Any]:
        """
        List saved workout templates.

        Returns a list of previously saved workout templates
        that can be used to create new workouts.

        Args:
            limit: Maximum number of templates to return

        Returns:
            templates: List of template summaries
            count: Total number of templates
        """
        try:
            templates = template_storage.list(limit=limit)
            return {
                "templates": [t.to_dict() for t in templates],
                "count": len(templates),
            }
        except Exception as e:
            return {"error": str(e)}

    return [
        create_workout,
        start_workout,
        get_workout_status,
        skip_segment,
        end_workout,
        list_workout_templates,
    ]
```

---

## Phase 5: Template Storage

**Goal**: Save and retrieve workout templates.

### Tests First (`tests/mcp/workout/test_templates.py`)

```python
import pytest
from pathlib import Path
from src.mcp.workout.models import Workout, WorkoutSegment
from src.mcp.workout.templates import TemplateStorage


class TestTemplateStorage:
    """Test workout template storage."""

    @pytest.fixture
    def template_dir(self, tmp_path: Path) -> Path:
        """Temp directory for templates."""
        return tmp_path / "templates"

    @pytest.fixture
    def storage(self, template_dir: Path) -> TemplateStorage:
        """TemplateStorage instance."""
        return TemplateStorage(template_dir)

    @pytest.fixture
    def sample_workout(self) -> Workout:
        """Sample workout for tests."""
        return Workout(
            name="4x100m Intervals",
            segments=[
                WorkoutSegment(type="warmup", target_duration_seconds=120),
                WorkoutSegment(type="work", target_distance_m=100),
                WorkoutSegment(type="rest", target_duration_seconds=30),
                WorkoutSegment(type="work", target_distance_m=100),
                WorkoutSegment(type="rest", target_duration_seconds=30),
                WorkoutSegment(type="work", target_distance_m=100),
                WorkoutSegment(type="rest", target_duration_seconds=30),
                WorkoutSegment(type="work", target_distance_m=100),
                WorkoutSegment(type="cooldown", target_duration_seconds=120),
            ]
        )

    # Test 1: Save creates template file
    def test_save_creates_file(self, storage, sample_workout, template_dir):
        # When save(workout) called
        # Then JSON file created in template_dir

    # Test 2: Save uses workout name for filename
    def test_save_filename(self, storage, sample_workout, template_dir):
        # When save(workout) called
        # Then filename based on workout name (sanitized)

    # Test 3: Get retrieves saved template
    def test_get_template(self, storage, sample_workout):
        # Given saved workout
        # When get(workout_id) called
        # Then returns Workout with same data

    # Test 4: List returns all templates
    def test_list_templates(self, storage, sample_workout):
        # Given 3 saved workouts
        # When list() called
        # Then returns all 3

    # Test 5: List respects limit
    def test_list_limit(self, storage):
        # Given 5 saved workouts
        # When list(limit=3) called
        # Then returns 3

    # Test 6: List sorts by created_at
    def test_list_sorted(self, storage):
        # Given workouts created at different times
        # When list() called
        # Then sorted newest first

    # Test 7: Delete removes template
    def test_delete_template(self, storage, sample_workout):
        # Given saved workout
        # When delete(workout_id) called
        # Then template no longer in list

    # Test 8: Get non-existent returns None
    def test_get_nonexistent(self, storage):
        # Given no templates
        # When get("nonexistent") called
        # Then returns None

    # Test 9: Creates directory if not exists
    def test_creates_directory(self, tmp_path):
        # Given non-existent directory
        # When TemplateStorage created and used
        # Then directory created

    # Test 10: Handles invalid JSON gracefully
    def test_handles_invalid_json(self, storage, template_dir):
        # Given corrupted JSON file in templates
        # When list() called
        # Then skips bad file, returns valid templates
```

### Implementation

```python
# src/mcp/workout/templates.py
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.mcp.workout.models import Workout


def _sanitize_filename(name: str) -> str:
    """Convert workout name to safe filename."""
    safe = "".join(c if c.isalnum() or c in "- _" else "_" for c in name)
    return safe.lower().replace(" ", "_")[:50]


@dataclass
class TemplateStorage:
    """
    Storage for workout templates.

    Saves workout definitions as JSON files for reuse.
    """
    template_dir: Path

    def __post_init__(self) -> None:
        """Ensure template directory exists."""
        self.template_dir.mkdir(parents=True, exist_ok=True)

    def save(self, workout: Workout) -> Path:
        """
        Save workout as template.

        Args:
            workout: Workout to save

        Returns:
            Path to saved template file
        """
        filename = f"{_sanitize_filename(workout.name)}_{workout.workout_id}.json"
        path = self.template_dir / filename

        with open(path, "w") as f:
            json.dump(workout.to_dict(), f, indent=2)

        return path

    def get(self, workout_id: str) -> Workout | None:
        """
        Get template by workout ID.

        Args:
            workout_id: ID of workout to retrieve

        Returns:
            Workout if found, None otherwise
        """
        for path in self.template_dir.glob("*.json"):
            try:
                with open(path) as f:
                    data = json.load(f)
                if data.get("workout_id") == workout_id:
                    return Workout.from_dict(data)
            except (json.JSONDecodeError, KeyError):
                continue
        return None

    def list(self, limit: int = 10) -> list[Workout]:
        """
        List all templates.

        Args:
            limit: Maximum number to return

        Returns:
            List of Workout templates, newest first
        """
        templates: list[Workout] = []

        for path in self.template_dir.glob("*.json"):
            try:
                with open(path) as f:
                    data = json.load(f)
                templates.append(Workout.from_dict(data))
            except (json.JSONDecodeError, KeyError):
                continue

        # Sort by created_at, newest first
        templates.sort(key=lambda w: w.created_at, reverse=True)

        return templates[:limit]

    def delete(self, workout_id: str) -> bool:
        """
        Delete template by workout ID.

        Args:
            workout_id: ID of workout to delete

        Returns:
            True if deleted, False if not found
        """
        for path in self.template_dir.glob("*.json"):
            try:
                with open(path) as f:
                    data = json.load(f)
                if data.get("workout_id") == workout_id:
                    path.unlink()
                    return True
            except (json.JSONDecodeError, KeyError):
                continue
        return False
```

---

## Phase 6: WebSocket Integration

**Goal**: Extend WebSocket state to include workout data.

### Tests First (`tests/mcp/workout/test_websocket_integration.py`)

```python
import pytest
import json
from src.mcp.models.messages import StateUpdate, WorkoutStateMessage
from src.mcp.workout.models import Workout, WorkoutSegment, WorkoutPhase


class TestWorkoutStateMessage:
    """Test WorkoutStateMessage for WebSocket."""

    # Test 1: Create from workout state
    def test_from_workout_state(self):
        # Given active workout state
        # When WorkoutStateMessage.from_state(state) called
        # Then creates message with correct fields

    # Test 2: Serialize to dict
    def test_to_dict(self):
        # Given WorkoutStateMessage
        # When to_dict() called
        # Then returns complete dict

    # Test 3: No workout produces None
    def test_no_workout(self):
        # Given NO_WORKOUT phase
        # When WorkoutStateMessage.from_state(None)
        # Then returns None


class TestStateUpdateWithWorkout:
    """Test extended StateUpdate with workout."""

    # Test 4: StateUpdate includes workout field
    def test_state_update_with_workout(self):
        # Given StateUpdate with workout state
        # When to_json() called
        # Then JSON includes "workout" key

    # Test 5: StateUpdate workout is optional
    def test_state_update_no_workout(self):
        # Given StateUpdate without workout
        # When to_json() called
        # Then "workout" key is null or absent

    # Test 6: Round-trip serialization
    def test_state_update_round_trip(self):
        # Given StateUpdate with workout
        # When to_json() then from_dict()
        # Then recreates same data


class TestWebSocketWorkoutBroadcast:
    """Integration tests for workout WebSocket broadcast."""

    @pytest.fixture
    async def server_with_workout(self, temp_slipstream_dir):
        """Server with workout system."""
        from src.mcp.server import SwimCoachServer

        server = SwimCoachServer(
            websocket_port=0,
            config_dir=temp_slipstream_dir,
        )
        await server.start()
        yield server
        await server.stop()

    # Test 7: WebSocket broadcast includes workout
    async def test_broadcast_includes_workout(self, server_with_workout):
        # Given active workout
        # When WebSocket client connected
        # Then receives state with workout data

    # Test 8: Workout progress updates broadcast
    async def test_workout_progress_broadcast(self, server_with_workout):
        # Given active workout
        # When segment advanced
        # Then next broadcast includes updated progress

    # Test 9: Dashboard receives segment info
    async def test_segment_info_broadcast(self, server_with_workout):
        # Given active workout on segment 2
        # When state broadcast
        # Then includes current_segment with type, targets, elapsed
```

### Implementation

```python
# src/mcp/models/messages.py (additions)

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


# Update StateUpdate to include workout
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
        }
        if self.workout:
            data["workout"] = self.workout.to_dict()
        return json.dumps(data)
```

---

## Phase 7: Server Integration

**Goal**: Register workout tools with MCP server and integrate auto-transitions.

### Tests First (`tests/mcp/workout/test_server_integration.py`)

```python
import pytest
import asyncio


class TestWorkoutServerIntegration:
    """Test workout integration with MCP server."""

    @pytest.fixture
    async def server(self, temp_slipstream_dir, mock_vision_state_store):
        """Full server with workout system."""
        from src.mcp.server import SwimCoachServer

        server = SwimCoachServer(
            websocket_port=0,
            config_dir=temp_slipstream_dir,
            vision_state_store=mock_vision_state_store,
        )
        await server.start()
        yield server
        await server.stop()

    # Test 1: Workout tools registered
    def test_workout_tools_registered(self, server):
        # Given server started
        # When listing MCP tools
        # Then workout tools present

    # Test 2: Full MCP workflow
    async def test_mcp_workout_workflow(self, server):
        # When create_workout via MCP
        # Then workout created
        # When start_workout via MCP
        # Then workout active
        # When get_workout_status via MCP
        # Then status returned

    # Test 3: Auto-transition monitor running
    async def test_auto_transition_monitor(self, server, mock_vision_state_store):
        # Given active workout with 60s duration segment
        # When 60s elapses
        # Then segment auto-advances

    # Test 4: Workout state in WebSocket
    async def test_websocket_workout_state(self, server):
        # Given active workout
        # When WebSocket client connects
        # Then receives workout state

    # Test 5: Session and workout tools work together
    async def test_session_workout_together(self, server):
        # When start_session then create_workout then start_workout
        # Then both systems work together

    # Test 6: Workout survives session end
    async def test_workout_survives_session_end(self, server):
        # Given active workout and session
        # When end_session called
        # Then workout still active
```

### Implementation Updates

```python
# src/mcp/server.py (additions)
from src.mcp.workout.state_machine import WorkoutStateMachine
from src.mcp.workout.templates import TemplateStorage
from src.mcp.workout.tools import create_workout_tools
from src.mcp.workout.transitions import TransitionMonitor
from src.mcp.models.messages import WorkoutStateMessage


class SwimCoachServer:
    def __init__(
        self,
        websocket_port: int = 8765,
        push_interval: float = 0.25,
        config_dir: Path | None = None,
        vision_state_store: VisionStateStore | None = None,
    ):
        # ... existing init ...

        # Workout system
        self.workout_state_machine = WorkoutStateMachine()
        self.template_storage = TemplateStorage(
            config_dir / "templates" if config_dir else Path.home() / ".slipstream/templates"
        )
        self.transition_monitor = TransitionMonitor(
            state_machine=self.workout_state_machine,
            vision_state_store=self.vision_state_store,
            dps_ratio=self.config.dps_ratio,
        )

        self._register_tools()

    def _register_tools(self) -> None:
        """Register all MCP tools."""
        # ... existing tools ...

        # Workout tools
        workout_tools = create_workout_tools(
            self.workout_state_machine,
            self.template_storage,
        )
        for tool in workout_tools:
            self.mcp.tool()(tool)

    async def _run_transition_monitor(self) -> None:
        """Background task checking for auto-transitions."""
        while self._running:
            try:
                result = self.transition_monitor.check()
                if result.get("should_transition"):
                    metrics = self.transition_monitor.get_metrics_for_advance()
                    self.workout_state_machine.advance_segment(**metrics)
            except Exception:
                pass  # Log but don't crash
            await asyncio.sleep(0.5)

    def get_state_update(self) -> StateUpdate:
        """Get state including workout."""
        update = self.state_store.get_state_update()

        # Add workout state
        workout_status = self.workout_state_machine.get_status()
        update.workout = WorkoutStateMessage.from_status(workout_status)

        return update
```

---

## Test Fixtures

```python
# tests/mcp/workout/conftest.py
import pytest
from pathlib import Path
from unittest.mock import Mock
from datetime import datetime, timezone

from src.mcp.workout.models import Workout, WorkoutSegment
from src.mcp.workout.state_machine import WorkoutStateMachine
from src.mcp.workout.templates import TemplateStorage


@pytest.fixture
def sample_segments() -> list[WorkoutSegment]:
    """Standard test segments."""
    return [
        WorkoutSegment(type="warmup", target_duration_seconds=120),
        WorkoutSegment(type="work", target_distance_m=100),
        WorkoutSegment(type="rest", target_duration_seconds=30),
        WorkoutSegment(type="work", target_distance_m=100),
        WorkoutSegment(type="rest", target_duration_seconds=30),
        WorkoutSegment(type="work", target_distance_m=100),
        WorkoutSegment(type="rest", target_duration_seconds=30),
        WorkoutSegment(type="work", target_distance_m=100),
        WorkoutSegment(type="cooldown", target_duration_seconds=120),
    ]


@pytest.fixture
def sample_workout(sample_segments) -> Workout:
    """Standard test workout."""
    return Workout(
        name="4x100m Intervals",
        segments=sample_segments,
    )


@pytest.fixture
def state_machine() -> WorkoutStateMachine:
    """Fresh state machine."""
    return WorkoutStateMachine()


@pytest.fixture
def active_workout(state_machine, sample_workout) -> WorkoutStateMachine:
    """State machine with active workout."""
    state_machine.create_workout(sample_workout)
    state_machine.start_workout()
    return state_machine


@pytest.fixture
def template_storage(tmp_path: Path) -> TemplateStorage:
    """TemplateStorage with temp directory."""
    return TemplateStorage(tmp_path / "templates")


@pytest.fixture
def mock_vision_state():
    """Mock vision state for transitions."""
    mock = Mock()
    mock.get_state.return_value = Mock(
        is_swimming=True,
        stroke_count=0,
        stroke_rate=50.0,
    )
    return mock
```

---

## File Structure After TDD

```
src/mcp/
├── __init__.py
├── server.py                    # Updated with workout integration
├── state_store.py
├── websocket_server.py
├── models/
│   ├── __init__.py
│   └── messages.py              # Updated with WorkoutStateMessage
├── storage/
│   ├── __init__.py
│   ├── session_storage.py
│   └── config.py
├── tools/
│   ├── __init__.py
│   ├── session_tools.py
│   ├── swim_tools.py
│   └── metric_bridge.py
└── workout/                     # NEW MODULE
    ├── __init__.py
    ├── models.py                # WorkoutSegment, Workout, WorkoutState
    ├── state_machine.py         # WorkoutStateMachine
    ├── transitions.py           # TransitionMonitor
    ├── tools.py                 # MCP workout tools
    └── templates.py             # TemplateStorage

tests/mcp/
├── __init__.py
├── conftest.py
├── test_models.py
├── test_config.py
├── test_session_storage.py
├── test_state_store.py
├── test_websocket_server.py
├── test_session_tools.py
├── test_swim_tools.py
├── test_metric_bridge.py
├── test_state_sync.py
├── test_integration.py
└── workout/                     # NEW TEST MODULE
    ├── __init__.py
    ├── conftest.py              # Workout-specific fixtures
    ├── test_models.py           # Model tests
    ├── test_state_machine.py    # State machine tests
    ├── test_transitions.py      # Auto-transition tests
    ├── test_tools.py            # MCP tool tests
    ├── test_templates.py        # Template storage tests
    ├── test_websocket_integration.py  # WebSocket tests
    └── test_server_integration.py     # Full integration tests
```

---

## Implementation Order (TDD Red-Green-Refactor)

| Order | Phase | Tests | Implementation |
|-------|-------|-------|----------------|
| 1 | Models | `workout/test_models.py` | `workout/models.py` |
| 2 | State Machine | `workout/test_state_machine.py` | `workout/state_machine.py` |
| 3 | Templates | `workout/test_templates.py` | `workout/templates.py` |
| 4 | MCP Tools | `workout/test_tools.py` | `workout/tools.py` |
| 5 | Auto-Transitions | `workout/test_transitions.py` | `workout/transitions.py` |
| 6 | WebSocket | `workout/test_websocket_integration.py` | Update `messages.py` |
| 7 | Server | `workout/test_server_integration.py` | Update `server.py` |

---

## Test Execution

```bash
# Phase 1: Models
uv run pytest tests/mcp/workout/test_models.py -v

# Phase 2: State Machine
uv run pytest tests/mcp/workout/test_state_machine.py -v

# Phase 3: Templates
uv run pytest tests/mcp/workout/test_templates.py -v

# Phase 4: MCP Tools
uv run pytest tests/mcp/workout/test_tools.py -v

# Phase 5: Auto-Transitions
uv run pytest tests/mcp/workout/test_transitions.py -v

# Phase 6-7: Integration
uv run pytest tests/mcp/workout/test_websocket_integration.py -v
uv run pytest tests/mcp/workout/test_server_integration.py -v

# All workout tests
uv run pytest tests/mcp/workout/ -v

# Full MCP test suite (including workout)
uv run pytest tests/mcp/ -v
```

---

## Success Criteria

From the requirements:

- [ ] Can create workouts with all segment types (warmup, work, rest, cooldown)
- [ ] State machine transitions correctly (NO_WORKOUT -> CREATED -> ACTIVE -> COMPLETE)
- [ ] Auto-transitions work based on duration/distance
- [ ] Workout data saved in session files
- [ ] Templates can be saved and retrieved

Additional criteria:

- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] >90% code coverage on workout module
- [ ] Thread safety verified
- [ ] WebSocket broadcasts include workout state
- [ ] MCP tools respond within 100ms
- [ ] Dashboard receives workout progress updates

---

## Notes

1. **State Machine Pattern**: Clean separation of concerns. All state changes go through the state machine, making testing and debugging straightforward.

2. **Auto-Transitions**: The TransitionMonitor runs as a background task, checking conditions every 500ms. Debouncing prevents false triggers from flickering swimming state.

3. **Template Storage**: Simple file-based storage in `~/.slipstream/templates/`. Templates are full Workout definitions that can be loaded and used to create new workouts.

4. **WebSocket Extension**: Rather than creating a separate broadcast, workout state piggybacks on the existing StateUpdate. Dashboard already handles state updates, just needs to render the new workout field.

5. **Error Handling**: All tools wrap operations in try/except and return error dicts. The state machine raises specific exceptions for invalid transitions.

6. **Testing Strategy**: Heavy use of fixtures to create consistent test scenarios. Mock vision state allows testing transitions without running the vision pipeline.

7. **Segment Types**: Each type has specific transition rules. Warmup/cooldown use duration or swimming stop. Work uses duration, distance, or swimming stop. Rest uses duration or swimming start.
