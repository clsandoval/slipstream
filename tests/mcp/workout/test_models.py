"""Tests for workout data models (Phase 1 TDD)."""

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

    def test_segment_with_duration(self):
        """Test creating segment with duration target."""
        segment = WorkoutSegment(
            type="work",
            target_duration_seconds=240,
        )
        assert segment.target_duration_seconds == 240
        assert segment.target_distance_m is None

    def test_segment_with_distance(self):
        """Test creating segment with distance target."""
        segment = WorkoutSegment(
            type="work",
            target_distance_m=100,
        )
        assert segment.target_distance_m == 100
        assert segment.target_duration_seconds is None

    def test_segment_with_stroke_rate_range(self):
        """Test creating segment with stroke rate target range."""
        segment = WorkoutSegment(
            type="work",
            target_stroke_rate=(50, 55),
        )
        assert segment.target_stroke_rate == (50, 55)

    @pytest.mark.parametrize("segment_type", ["warmup", "work", "rest", "cooldown"])
    def test_valid_segment_types(self, segment_type):
        """Test that all valid segment types can be created."""
        segment = WorkoutSegment(type=segment_type)
        assert segment.type == segment_type

    def test_segment_to_dict(self):
        """Test segment serialization to dictionary."""
        segment = WorkoutSegment(
            type="work",
            target_duration_seconds=240,
            target_distance_m=100,
            target_stroke_rate=(50, 55),
            notes="Maintain pace",
        )
        result = segment.to_dict()

        assert result["type"] == "work"
        assert result["target_duration_seconds"] == 240
        assert result["target_distance_m"] == 100
        assert result["target_stroke_rate"] == [50, 55]
        assert result["notes"] == "Maintain pace"

    def test_segment_from_dict(self):
        """Test segment deserialization from dictionary."""
        data = {
            "type": "work",
            "target_duration_seconds": 240,
            "target_distance_m": 100,
            "target_stroke_rate": [50, 55],
            "notes": "Keep steady",
        }
        segment = WorkoutSegment.from_dict(data)

        assert segment.type == "work"
        assert segment.target_duration_seconds == 240
        assert segment.target_distance_m == 100
        assert segment.target_stroke_rate == (50, 55)
        assert segment.notes == "Keep steady"


class TestWorkout:
    """Test Workout data model."""

    @pytest.fixture
    def sample_segments(self) -> list[WorkoutSegment]:
        return [
            WorkoutSegment(type="warmup", target_duration_seconds=60),
            WorkoutSegment(type="work", target_distance_m=100),
            WorkoutSegment(type="rest", target_duration_seconds=30),
            WorkoutSegment(type="cooldown", target_duration_seconds=60),
        ]

    def test_workout_creation(self, sample_segments):
        """Test workout creation with segments."""
        workout = Workout(name="4x100m Intervals", segments=sample_segments)

        assert workout.name == "4x100m Intervals"
        assert len(workout.segments) == 4
        assert workout.workout_id is not None
        assert workout.created_at is not None

    def test_workout_id_format(self):
        """Test workout ID follows expected pattern."""
        workout = Workout(name="Test", segments=[])
        # Format: wkt_YYYYMMDD_HHMMSS
        assert workout.workout_id.startswith("wkt_")
        assert len(workout.workout_id) == 19

    def test_workout_total_duration(self):
        """Test total duration calculation."""
        segments = [
            WorkoutSegment(type="warmup", target_duration_seconds=60),
            WorkoutSegment(type="work", target_duration_seconds=240),
            WorkoutSegment(type="rest", target_duration_seconds=30),
            WorkoutSegment(type="work", target_duration_seconds=240),
            WorkoutSegment(type="rest", target_duration_seconds=30),
            WorkoutSegment(type="work", target_duration_seconds=240),
            WorkoutSegment(type="rest", target_duration_seconds=30),
            WorkoutSegment(type="cooldown", target_duration_seconds=60),
        ]
        workout = Workout(name="Test", segments=segments)
        assert workout.total_duration_seconds == 930

    def test_workout_total_distance(self):
        """Test total distance calculation."""
        segments = [
            WorkoutSegment(type="warmup", target_duration_seconds=60),
            WorkoutSegment(type="work", target_distance_m=100),
            WorkoutSegment(type="rest", target_duration_seconds=30),
            WorkoutSegment(type="work", target_distance_m=100),
            WorkoutSegment(type="rest", target_duration_seconds=30),
            WorkoutSegment(type="work", target_distance_m=100),
        ]
        workout = Workout(name="Test", segments=segments)
        assert workout.total_distance_m == 300

    def test_workout_segment_count(self, sample_segments):
        """Test segment count."""
        workout = Workout(name="Test", segments=sample_segments)
        assert len(workout.segments) == 4

    def test_workout_to_dict(self, sample_segments):
        """Test workout serialization to dictionary."""
        workout = Workout(
            name="4x100m Intervals",
            segments=sample_segments,
            workout_id="wkt_20250114_120000",
        )
        result = workout.to_dict()

        assert result["workout_id"] == "wkt_20250114_120000"
        assert result["name"] == "4x100m Intervals"
        assert len(result["segments"]) == 4
        assert "created_at" in result
        assert result["created_by"] == "claude"

    def test_workout_from_dict(self, sample_segments):
        """Test workout deserialization from dictionary."""
        data = {
            "workout_id": "wkt_20250114_120000",
            "name": "Test Workout",
            "segments": [s.to_dict() for s in sample_segments],
            "created_at": "2025-01-14T12:00:00+00:00",
            "created_by": "claude",
        }
        workout = Workout.from_dict(data)

        assert workout.workout_id == "wkt_20250114_120000"
        assert workout.name == "Test Workout"
        assert len(workout.segments) == 4
        assert workout.created_by == "claude"


class TestSegmentResult:
    """Test SegmentResult data model."""

    def test_segment_result_creation(self):
        """Test creating segment result."""
        now = datetime.now(timezone.utc)
        result = SegmentResult(
            segment_index=0,
            segment_type="work",
            started_at=now,
            ended_at=now,
            actual_duration_seconds=120,
            actual_distance_m=95.5,
            stroke_count=50,
            avg_stroke_rate=52.0,
        )

        assert result.segment_index == 0
        assert result.segment_type == "work"
        assert result.actual_duration_seconds == 120
        assert result.actual_distance_m == 95.5
        assert result.skipped is False

    def test_segment_result_with_strokes(self):
        """Test segment result with stroke metrics."""
        now = datetime.now(timezone.utc)
        result = SegmentResult(
            segment_index=1,
            segment_type="work",
            started_at=now,
            ended_at=now,
            actual_duration_seconds=90,
            actual_distance_m=100.0,
            stroke_count=80,
            avg_stroke_rate=52.0,
        )

        assert result.stroke_count == 80
        assert result.avg_stroke_rate == 52.0

    def test_segment_result_skipped(self):
        """Test segment result when skipped."""
        now = datetime.now(timezone.utc)
        result = SegmentResult(
            segment_index=2,
            segment_type="rest",
            started_at=now,
            ended_at=now,
            actual_duration_seconds=10,
            actual_distance_m=0.0,
            stroke_count=0,
            avg_stroke_rate=0.0,
            skipped=True,
        )

        assert result.skipped is True
        assert result.actual_duration_seconds == 10

    def test_segment_result_to_dict(self):
        """Test segment result serialization."""
        now = datetime.now(timezone.utc)
        result = SegmentResult(
            segment_index=0,
            segment_type="work",
            started_at=now,
            ended_at=now,
            actual_duration_seconds=120,
            actual_distance_m=100.0,
            stroke_count=50,
            avg_stroke_rate=52.0,
            skipped=False,
        )
        data = result.to_dict()

        assert data["segment_index"] == 0
        assert data["segment_type"] == "work"
        assert data["actual_duration_seconds"] == 120
        assert data["stroke_count"] == 50
        assert data["skipped"] is False


class TestWorkoutState:
    """Test WorkoutState data model."""

    @pytest.fixture
    def sample_workout(self) -> Workout:
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

    def test_workout_state_creation(self, sample_workout):
        """Test creating workout state."""
        state = WorkoutState(workout=sample_workout)

        assert state.current_segment_idx == 0
        assert state.phase == WorkoutPhase.ACTIVE
        assert state.workout == sample_workout

    def test_current_segment(self, sample_workout):
        """Test current segment accessor."""
        state = WorkoutState(workout=sample_workout, current_segment_idx=2)

        assert state.current_segment.type == "rest"

    def test_next_segment(self, sample_workout):
        """Test next segment accessor."""
        state = WorkoutState(workout=sample_workout, current_segment_idx=2)

        assert state.next_segment is not None
        assert state.next_segment.type == "work"

    def test_next_segment_at_end(self, sample_workout):
        """Test next segment at end returns None."""
        state = WorkoutState(workout=sample_workout, current_segment_idx=4)

        assert state.next_segment is None

    def test_is_last_segment(self, sample_workout):
        """Test is_last_segment property."""
        state = WorkoutState(workout=sample_workout, current_segment_idx=4)

        assert state.is_last_segment is True

        state.current_segment_idx = 2
        assert state.is_last_segment is False

    def test_progress_percentage(self, sample_workout):
        """Test progress calculation."""
        now = datetime.now(timezone.utc)
        state = WorkoutState(
            workout=sample_workout,
            segments_completed=[
                SegmentResult(
                    segment_index=0,
                    segment_type="warmup",
                    started_at=now,
                    ended_at=now,
                    actual_duration_seconds=60,
                    actual_distance_m=0,
                    stroke_count=0,
                    avg_stroke_rate=0,
                ),
                SegmentResult(
                    segment_index=1,
                    segment_type="work",
                    started_at=now,
                    ended_at=now,
                    actual_duration_seconds=90,
                    actual_distance_m=100,
                    stroke_count=50,
                    avg_stroke_rate=52,
                ),
            ],
        )
        # 2 of 5 segments completed = 40%
        assert state.progress_percent == 40.0

    def test_workout_state_to_dict(self, sample_workout):
        """Test workout state serialization."""
        state = WorkoutState(workout=sample_workout)
        data = state.to_dict()

        assert "workout" in data
        assert data["current_segment_idx"] == 0
        assert data["phase"] == "active"
        assert "segment_started_at" in data


class TestWorkoutPhase:
    """Test WorkoutPhase enum."""

    def test_phases_defined(self):
        """Test all phases are defined."""
        assert WorkoutPhase.NO_WORKOUT.value == "no_workout"
        assert WorkoutPhase.CREATED.value == "created"
        assert WorkoutPhase.ACTIVE.value == "active"
        assert WorkoutPhase.COMPLETE.value == "complete"
