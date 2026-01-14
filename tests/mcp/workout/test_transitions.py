"""Tests for automatic segment transitions (Phase 3 TDD)."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, MagicMock
from dataclasses import dataclass

from src.mcp.workout.models import Workout, WorkoutSegment, WorkoutPhase
from src.mcp.workout.state_machine import WorkoutStateMachine
from src.mcp.workout.transitions import TransitionMonitor, TRANSITION_RULES


@dataclass
class MockVisionState:
    """Mock vision state for testing."""

    is_swimming: bool = True
    stroke_count: int = 0
    stroke_rate: float = 50.0


class TestTransitionMonitor:
    """Test automatic segment transitions."""

    @pytest.fixture
    def mock_vision_state_store(self):
        """Mock vision state store."""
        mock = Mock()
        mock.get_state.return_value = MockVisionState(
            is_swimming=True,
            stroke_count=0,
            stroke_rate=50.0,
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
            ],
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
            ],
        )

    @pytest.fixture
    def state_machine(self) -> WorkoutStateMachine:
        return WorkoutStateMachine()

    def test_duration_transition(
        self, state_machine, workout_with_duration, mock_vision_state_store
    ):
        """Test duration transition triggers on time elapsed."""
        state_machine.create_workout(workout_with_duration)
        state_machine.start_workout()

        # Set segment started well in the past (60+ seconds ago)
        state_machine._state.segment_started_at = datetime.now(
            timezone.utc
        ) - timedelta(seconds=65)

        monitor = TransitionMonitor(
            state_machine=state_machine,
            vision_state_store=mock_vision_state_store,
            grace_period_seconds=0,
        )

        result = monitor.check()

        assert result["should_transition"] is True
        assert result["reason"] == "duration_elapsed"

    def test_duration_no_early_transition(
        self, state_machine, workout_with_duration, mock_vision_state_store
    ):
        """Test duration transition does not trigger early."""
        state_machine.create_workout(workout_with_duration)
        state_machine.start_workout()

        # Set segment started 30 seconds ago (< 60 second target)
        state_machine._state.segment_started_at = datetime.now(
            timezone.utc
        ) - timedelta(seconds=30)

        monitor = TransitionMonitor(
            state_machine=state_machine,
            vision_state_store=mock_vision_state_store,
            grace_period_seconds=0,
        )

        result = monitor.check()

        assert result["should_transition"] is False

    def test_distance_transition(
        self, state_machine, workout_with_distance, mock_vision_state_store
    ):
        """Test distance transition triggers on distance reached."""
        state_machine.create_workout(workout_with_distance)
        state_machine.start_workout()
        state_machine.advance_segment()  # Move to work segment (100m target)

        # Set enough strokes to cover 100m (at 1.8 dps, need ~56 strokes)
        mock_vision_state_store.get_state.return_value = MockVisionState(
            is_swimming=True,
            stroke_count=60,  # 60 * 1.8 = 108m
        )

        # Set segment started far enough back to clear grace period
        state_machine._state.segment_started_at = datetime.now(
            timezone.utc
        ) - timedelta(seconds=10)
        state_machine._state.segment_stroke_count_start = 0

        monitor = TransitionMonitor(
            state_machine=state_machine,
            vision_state_store=mock_vision_state_store,
            dps_ratio=1.8,
            grace_period_seconds=0,
        )

        result = monitor.check()

        assert result["should_transition"] is True
        assert result["reason"] == "distance_reached"

    def test_distance_uses_dps_ratio(
        self, state_machine, workout_with_distance, mock_vision_state_store
    ):
        """Test distance uses DPS ratio from config."""
        state_machine.create_workout(workout_with_distance)
        state_machine.start_workout()
        state_machine.advance_segment()  # Move to work segment

        # With dps_ratio=2.0, 50 strokes = 100m
        mock_vision_state_store.get_state.return_value = MockVisionState(
            is_swimming=True,
            stroke_count=50,
        )

        state_machine._state.segment_started_at = datetime.now(
            timezone.utc
        ) - timedelta(seconds=10)
        state_machine._state.segment_stroke_count_start = 0

        monitor = TransitionMonitor(
            state_machine=state_machine,
            vision_state_store=mock_vision_state_store,
            dps_ratio=2.0,  # 50 * 2.0 = 100m exactly
            grace_period_seconds=0,
        )

        result = monitor.check()

        assert result["should_transition"] is True

    def test_swimming_stop_work_transition(
        self, state_machine, workout_with_distance, mock_vision_state_store
    ):
        """Test swimming stop triggers transition from work."""
        state_machine.create_workout(workout_with_distance)
        state_machine.start_workout()
        state_machine.advance_segment()  # Move to work segment

        state_machine._state.segment_started_at = datetime.now(
            timezone.utc
        ) - timedelta(seconds=10)

        monitor = TransitionMonitor(
            state_machine=state_machine,
            vision_state_store=mock_vision_state_store,
            grace_period_seconds=0,
            swimming_debounce_seconds=0,
        )

        # First call with swimming=True to establish state
        mock_vision_state_store.get_state.return_value = MockVisionState(
            is_swimming=True
        )
        monitor.check()

        # Then swimming stops
        mock_vision_state_store.get_state.return_value = MockVisionState(
            is_swimming=False
        )
        result = monitor.check()

        assert result["should_transition"] is True
        assert result["reason"] == "swimming_stopped"

    def test_swimming_start_rest_transition(
        self, state_machine, workout_with_distance, mock_vision_state_store
    ):
        """Test swimming start triggers transition from rest."""
        state_machine.create_workout(workout_with_distance)
        state_machine.start_workout()
        state_machine.advance_segment()  # warmup -> work
        state_machine.advance_segment()  # work -> rest

        state_machine._state.segment_started_at = datetime.now(
            timezone.utc
        ) - timedelta(seconds=10)

        monitor = TransitionMonitor(
            state_machine=state_machine,
            vision_state_store=mock_vision_state_store,
            grace_period_seconds=0,
            swimming_debounce_seconds=0,
        )

        # First call with swimming=False to establish state
        mock_vision_state_store.get_state.return_value = MockVisionState(
            is_swimming=False
        )
        monitor.check()

        # Then swimmer starts
        mock_vision_state_store.get_state.return_value = MockVisionState(
            is_swimming=True
        )
        result = monitor.check()

        assert result["should_transition"] is True
        assert result["reason"] == "swimming_started"

    def test_rest_segment_transitions(self, state_machine, mock_vision_state_store):
        """Test rest segment transitions on duration OR swimming start."""
        workout = Workout(
            name="Test",
            segments=[
                WorkoutSegment(type="warmup", target_duration_seconds=60),
                WorkoutSegment(type="rest", target_duration_seconds=30),
            ],
        )
        state_machine.create_workout(workout)
        state_machine.start_workout()
        state_machine.advance_segment()  # Move to rest

        # Only 25s elapsed, but swimmer starts swimming
        state_machine._state.segment_started_at = datetime.now(
            timezone.utc
        ) - timedelta(seconds=25)

        monitor = TransitionMonitor(
            state_machine=state_machine,
            vision_state_store=mock_vision_state_store,
            grace_period_seconds=0,
            swimming_debounce_seconds=0,
        )

        # Establish not swimming state
        mock_vision_state_store.get_state.return_value = MockVisionState(
            is_swimming=False
        )
        monitor.check()

        # Start swimming
        mock_vision_state_store.get_state.return_value = MockVisionState(
            is_swimming=True
        )
        result = monitor.check()

        assert result["should_transition"] is True

    def test_warmup_stop_swimming(self, state_machine, mock_vision_state_store):
        """Test warmup transitions on stop swimming."""
        workout = Workout(
            name="Test",
            segments=[
                WorkoutSegment(type="warmup", target_duration_seconds=120),
                WorkoutSegment(type="work", target_distance_m=100),
            ],
        )
        state_machine.create_workout(workout)
        state_machine.start_workout()

        state_machine._state.segment_started_at = datetime.now(
            timezone.utc
        ) - timedelta(seconds=30)

        monitor = TransitionMonitor(
            state_machine=state_machine,
            vision_state_store=mock_vision_state_store,
            grace_period_seconds=0,
            swimming_debounce_seconds=0,
        )

        # Establish swimming state
        mock_vision_state_store.get_state.return_value = MockVisionState(
            is_swimming=True
        )
        monitor.check()

        # Stop swimming
        mock_vision_state_store.get_state.return_value = MockVisionState(
            is_swimming=False
        )
        result = monitor.check()

        assert result["should_transition"] is True
        assert result["reason"] == "swimming_stopped"

    def test_cooldown_stop_swimming(self, state_machine, mock_vision_state_store):
        """Test cooldown transitions on stop swimming or duration."""
        workout = Workout(
            name="Test",
            segments=[
                WorkoutSegment(type="warmup", target_duration_seconds=60),
                WorkoutSegment(type="cooldown", target_duration_seconds=120),
            ],
        )
        state_machine.create_workout(workout)
        state_machine.start_workout()
        state_machine.advance_segment()  # Move to cooldown

        state_machine._state.segment_started_at = datetime.now(
            timezone.utc
        ) - timedelta(seconds=30)

        monitor = TransitionMonitor(
            state_machine=state_machine,
            vision_state_store=mock_vision_state_store,
            grace_period_seconds=0,
            swimming_debounce_seconds=0,
        )

        # Establish swimming state
        mock_vision_state_store.get_state.return_value = MockVisionState(
            is_swimming=True
        )
        monitor.check()

        # Stop swimming
        mock_vision_state_store.get_state.return_value = MockVisionState(
            is_swimming=False
        )
        result = monitor.check()

        assert result["should_transition"] is True

    def test_check_returns_info(
        self, state_machine, workout_with_duration, mock_vision_state_store
    ):
        """Test check returns transition info."""
        state_machine.create_workout(workout_with_duration)
        state_machine.start_workout()

        state_machine._state.segment_started_at = datetime.now(
            timezone.utc
        ) - timedelta(seconds=65)

        monitor = TransitionMonitor(
            state_machine=state_machine,
            vision_state_store=mock_vision_state_store,
            grace_period_seconds=0,
        )

        result = monitor.check()

        assert "should_transition" in result
        assert "reason" in result
        assert "metrics" in result
        assert "elapsed_seconds" in result["metrics"]
        assert "is_swimming" in result["metrics"]

    def test_ignores_inactive(self, state_machine, mock_vision_state_store):
        """Test monitor ignores transitions when not active."""
        workout = Workout(
            name="Test",
            segments=[WorkoutSegment(type="warmup", target_duration_seconds=60)],
        )
        state_machine.create_workout(workout)
        # Don't start - still in CREATED phase

        monitor = TransitionMonitor(
            state_machine=state_machine,
            vision_state_store=mock_vision_state_store,
        )

        result = monitor.check()

        assert result["should_transition"] is False

    def test_swimming_state_debounce(self, state_machine, mock_vision_state_store):
        """Test swimming state debounce prevents flickering triggers."""
        workout = Workout(
            name="Test",
            segments=[
                WorkoutSegment(type="warmup", target_duration_seconds=60),
                WorkoutSegment(type="work", target_distance_m=100),
            ],
        )
        state_machine.create_workout(workout)
        state_machine.start_workout()
        state_machine.advance_segment()  # Move to work

        state_machine._state.segment_started_at = datetime.now(
            timezone.utc
        ) - timedelta(seconds=10)

        monitor = TransitionMonitor(
            state_machine=state_machine,
            vision_state_store=mock_vision_state_store,
            grace_period_seconds=0,
            swimming_debounce_seconds=2.0,  # Require 2s stable state
        )

        # First call with swimming=True
        mock_vision_state_store.get_state.return_value = MockVisionState(
            is_swimming=True
        )
        monitor.check()

        # Quick flicker to False - should not trigger due to debounce
        mock_vision_state_store.get_state.return_value = MockVisionState(
            is_swimming=False
        )
        result = monitor.check()

        # With debounce, should NOT trigger immediately
        assert result["should_transition"] is False

    def test_segment_start_grace_period(self, state_machine, mock_vision_state_store):
        """Test grace period after segment start."""
        workout = Workout(
            name="Test",
            segments=[
                WorkoutSegment(type="warmup", target_duration_seconds=5),
                WorkoutSegment(type="work", target_distance_m=100),
            ],
        )
        state_machine.create_workout(workout)
        state_machine.start_workout()

        # Segment just started - within grace period
        state_machine._state.segment_started_at = datetime.now(
            timezone.utc
        ) - timedelta(seconds=2)

        monitor = TransitionMonitor(
            state_machine=state_machine,
            vision_state_store=mock_vision_state_store,
            grace_period_seconds=5.0,
        )

        result = monitor.check()

        assert result["should_transition"] is False
        assert result.get("reason") == "grace_period"


class TestTransitionRules:
    """Test transition rules by segment type."""

    def test_rules_defined(self):
        """Test all segment types have rules."""
        assert "warmup" in TRANSITION_RULES
        assert "work" in TRANSITION_RULES
        assert "rest" in TRANSITION_RULES
        assert "cooldown" in TRANSITION_RULES

    def test_warmup_rules(self):
        """Test warmup rules include duration and swimming_stopped."""
        rules = TRANSITION_RULES["warmup"]
        assert "duration_elapsed" in rules["triggers"]
        assert "swimming_stopped" in rules["triggers"]
        assert "swimming_started" not in rules["triggers"]
        assert "distance_reached" not in rules["triggers"]

    def test_work_rules(self):
        """Test work rules include duration, distance, and swimming_stopped."""
        rules = TRANSITION_RULES["work"]
        assert "duration_elapsed" in rules["triggers"]
        assert "distance_reached" in rules["triggers"]
        assert "swimming_stopped" in rules["triggers"]
        assert "swimming_started" not in rules["triggers"]

    def test_rest_rules(self):
        """Test rest rules include duration and swimming_started."""
        rules = TRANSITION_RULES["rest"]
        assert "duration_elapsed" in rules["triggers"]
        assert "swimming_started" in rules["triggers"]
        assert "swimming_stopped" not in rules["triggers"]
        assert "distance_reached" not in rules["triggers"]

    def test_cooldown_rules(self):
        """Test cooldown rules include duration and swimming_stopped."""
        rules = TRANSITION_RULES["cooldown"]
        assert "duration_elapsed" in rules["triggers"]
        assert "swimming_stopped" in rules["triggers"]
        assert "swimming_started" not in rules["triggers"]
        assert "distance_reached" not in rules["triggers"]


class TestTransitionMetrics:
    """Test metrics for segment advancement."""

    @pytest.fixture
    def mock_vision_state_store(self):
        mock = Mock()
        mock.get_state.return_value = MockVisionState(
            is_swimming=True, stroke_count=100, stroke_rate=52.0
        )
        return mock

    def test_get_metrics_for_advance(self, mock_vision_state_store):
        """Test getting metrics for segment completion."""
        workout = Workout(
            name="Test",
            segments=[WorkoutSegment(type="work", target_distance_m=100)],
        )
        state_machine = WorkoutStateMachine()
        state_machine.create_workout(workout)
        state_machine.start_workout()
        state_machine._state.segment_stroke_count_start = 50

        monitor = TransitionMonitor(
            state_machine=state_machine,
            vision_state_store=mock_vision_state_store,
            dps_ratio=2.0,
        )

        metrics = monitor.get_metrics_for_advance()

        assert metrics["stroke_count"] == 50  # 100 - 50
        assert metrics["distance_m"] == 100.0  # 50 * 2.0
        assert metrics["avg_stroke_rate"] == 52.0
