"""Automatic segment transitions.

Monitors vision state for duration/distance/swimming changes
and determines when to auto-advance segments.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from src.mcp.workout.models import WorkoutPhase
from src.mcp.workout.state_machine import WorkoutStateMachine

if TYPE_CHECKING:
    from typing import Protocol

    class VisionState(Protocol):
        is_swimming: bool
        stroke_count: int
        stroke_rate: float

    class VisionStateStore(Protocol):
        def get_state(self) -> VisionState: ...


# Transition rules by segment type
TRANSITION_RULES: dict[str, dict[str, list[str]]] = {
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
    vision_state_store: Any  # VisionStateStore protocol
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
