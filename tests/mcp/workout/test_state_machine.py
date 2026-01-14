"""Tests for workout state machine (Phase 2 TDD)."""

import pytest
import threading
from datetime import datetime, timezone

from src.mcp.workout.models import (
    Workout,
    WorkoutSegment,
    WorkoutState,
    WorkoutPhase,
    SegmentResult,
)
from src.mcp.workout.state_machine import (
    WorkoutStateMachine,
    WorkoutExistsError,
    NoWorkoutError,
    WorkoutAlreadyActiveError,
    WorkoutNotActiveError,
)


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
            ],
        )

    @pytest.fixture
    def state_machine(self) -> WorkoutStateMachine:
        """Create state machine instance."""
        return WorkoutStateMachine()

    def test_initial_state(self, state_machine):
        """Test initial state is NO_WORKOUT."""
        assert state_machine.phase == WorkoutPhase.NO_WORKOUT

    def test_create_workout(self, state_machine, sample_workout):
        """Test create workout transitions to CREATED."""
        result = state_machine.create_workout(sample_workout)

        assert state_machine.phase == WorkoutPhase.CREATED
        assert result["workout_id"] == sample_workout.workout_id
        assert result["segments_count"] == 5

    def test_create_workout_already_exists(self, state_machine, sample_workout):
        """Test cannot create workout if one exists."""
        state_machine.create_workout(sample_workout)

        with pytest.raises(WorkoutExistsError):
            state_machine.create_workout(sample_workout)

    def test_start_workout(self, state_machine, sample_workout):
        """Test start workout transitions to ACTIVE."""
        state_machine.create_workout(sample_workout)
        result = state_machine.start_workout()

        assert state_machine.phase == WorkoutPhase.ACTIVE
        assert "started_at" in result
        assert result["total_segments"] == 5
        assert result["first_segment"]["type"] == "warmup"

    def test_start_workout_not_created(self, state_machine):
        """Test cannot start workout if not created."""
        with pytest.raises(NoWorkoutError):
            state_machine.start_workout()

    def test_start_workout_already_active(self, state_machine, sample_workout):
        """Test cannot start already active workout."""
        state_machine.create_workout(sample_workout)
        state_machine.start_workout()

        with pytest.raises(WorkoutAlreadyActiveError):
            state_machine.start_workout()

    def test_advance_segment(self, state_machine, sample_workout):
        """Test advance segment moves to next."""
        state_machine.create_workout(sample_workout)
        state_machine.start_workout()

        result = state_machine.advance_segment(
            stroke_count=0, distance_m=0, avg_stroke_rate=0
        )

        assert result["workout_complete"] is False
        assert result["now_on"]["type"] == "work"
        assert state_machine.state.current_segment_idx == 1

    def test_advance_segment_captures_result(self, state_machine, sample_workout):
        """Test advance segment captures result with metrics."""
        state_machine.create_workout(sample_workout)
        state_machine.start_workout()

        result = state_machine.advance_segment(
            stroke_count=50, distance_m=90.0, avg_stroke_rate=52.5
        )

        completed = result["completed"]
        assert completed["stroke_count"] == 50
        assert completed["actual_distance_m"] == 90.0
        assert completed["avg_stroke_rate"] == 52.5
        assert len(state_machine.state.segments_completed) == 1

    def test_advance_last_segment(self, state_machine, sample_workout):
        """Test advance past last segment completes workout."""
        state_machine.create_workout(sample_workout)
        state_machine.start_workout()

        # Advance through all segments
        for _ in range(5):
            result = state_machine.advance_segment()

        assert result["workout_complete"] is True
        assert result["now_on"] is None
        assert state_machine.phase == WorkoutPhase.COMPLETE

    def test_skip_segment(self, state_machine, sample_workout):
        """Test skip segment marks as skipped."""
        state_machine.create_workout(sample_workout)
        state_machine.start_workout()

        result = state_machine.skip_segment()

        assert result["completed"]["skipped"] is True
        assert result["now_on"]["type"] == "work"

    def test_end_workout(self, state_machine, sample_workout):
        """Test end workout early."""
        state_machine.create_workout(sample_workout)
        state_machine.start_workout()
        state_machine.advance_segment()

        result = state_machine.end_workout()

        assert state_machine.phase == WorkoutPhase.COMPLETE
        assert result["segments_completed"] == 1
        assert result["ended_early"] is True

    def test_end_workout_summary(self, state_machine, sample_workout):
        """Test end workout returns complete summary."""
        state_machine.create_workout(sample_workout)
        state_machine.start_workout()
        state_machine.advance_segment(stroke_count=10, distance_m=50)
        state_machine.advance_segment(stroke_count=40, distance_m=100)

        result = state_machine.end_workout()

        assert result["workout_id"] == sample_workout.workout_id
        assert result["workout_name"] == "Test Workout"
        assert result["segments_completed"] == 2
        assert result["segments_total"] == 5
        assert len(result["segments"]) == 2

    def test_get_status(self, state_machine, sample_workout):
        """Test get status returns current state."""
        state_machine.create_workout(sample_workout)
        state_machine.start_workout()

        status = state_machine.get_status()

        assert status["has_active_workout"] is True
        assert status["phase"] == "active"
        assert status["workout_name"] == "Test Workout"
        assert status["current_segment"]["type"] == "warmup"
        assert status["progress"]["segments_completed"] == 0
        assert status["progress"]["segments_total"] == 5

    def test_get_status_no_workout(self, state_machine):
        """Test get status with no workout."""
        status = state_machine.get_status()

        assert status["has_active_workout"] is False

    def test_thread_safety(self, state_machine, sample_workout):
        """Test concurrent operations maintain consistent state."""
        state_machine.create_workout(sample_workout)
        state_machine.start_workout()

        results = []
        errors = []

        def advance():
            try:
                result = state_machine.advance_segment()
                results.append(result)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=advance) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All 5 advances should succeed (workout has 5 segments)
        # No race conditions should occur
        assert len(errors) == 0
        assert state_machine.phase == WorkoutPhase.COMPLETE


class TestWorkoutStateMachineErrors:
    """Test error conditions."""

    @pytest.fixture
    def state_machine(self) -> WorkoutStateMachine:
        return WorkoutStateMachine()

    @pytest.fixture
    def sample_workout(self) -> Workout:
        return Workout(
            name="Test",
            segments=[
                WorkoutSegment(type="warmup", target_duration_seconds=60),
                WorkoutSegment(type="work", target_distance_m=100),
            ],
        )

    def test_advance_not_active(self, state_machine, sample_workout):
        """Test cannot advance in CREATED state."""
        state_machine.create_workout(sample_workout)

        with pytest.raises(WorkoutNotActiveError):
            state_machine.advance_segment()

    def test_advance_complete(self, state_machine, sample_workout):
        """Test cannot advance in COMPLETE state."""
        state_machine.create_workout(sample_workout)
        state_machine.start_workout()
        state_machine.advance_segment()
        state_machine.advance_segment()  # Completes workout

        with pytest.raises(WorkoutNotActiveError):
            state_machine.advance_segment()

    def test_skip_complete(self, state_machine, sample_workout):
        """Test cannot skip in COMPLETE state."""
        state_machine.create_workout(sample_workout)
        state_machine.start_workout()
        state_machine.advance_segment()
        state_machine.advance_segment()  # Completes workout

        with pytest.raises(WorkoutNotActiveError):
            state_machine.skip_segment()

    def test_clear_workout(self, state_machine, sample_workout):
        """Test clear workout resets to NO_WORKOUT."""
        state_machine.create_workout(sample_workout)
        state_machine.start_workout()
        state_machine.advance_segment()
        state_machine.end_workout()

        state_machine.clear_workout()

        assert state_machine.phase == WorkoutPhase.NO_WORKOUT
        assert state_machine.workout is None
        assert state_machine.state is None
