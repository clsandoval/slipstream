"""Workout state machine.

Manages workout lifecycle transitions:
NO_WORKOUT -> CREATED -> ACTIVE -> COMPLETE

Thread-safe for concurrent access.
"""

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

                status.update(
                    {
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
                    }
                )

            return status

    def clear_workout(self) -> None:
        """Reset to NO_WORKOUT state."""
        with self._lock:
            self._workout = None
            self._state = None
            self._phase = WorkoutPhase.NO_WORKOUT
