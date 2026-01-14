"""Tests for workout WebSocket integration (Phase 6 TDD)."""

import pytest
import json
from datetime import datetime, timezone

from src.mcp.models.messages import StateUpdate, WorkoutStateMessage
from src.mcp.workout.models import Workout, WorkoutSegment, WorkoutPhase


class TestWorkoutStateMessage:
    """Test WorkoutStateMessage for WebSocket."""

    def test_from_status_active(self):
        """Test creating from active workout status."""
        status = {
            "has_active_workout": True,
            "phase": "active",
            "workout_name": "4x100m Intervals",
            "current_segment": {
                "index": 1,
                "type": "work",
                "elapsed_seconds": 45,
            },
            "progress": {
                "segments_completed": 1,
                "segments_total": 5,
                "percent": 20.0,
            },
            "next_segment": {
                "type": "rest",
                "target_duration_seconds": 30,
            },
        }

        message = WorkoutStateMessage.from_status(status)

        assert message.has_active_workout is True
        assert message.phase == "active"
        assert message.workout_name == "4x100m Intervals"
        assert message.current_segment["type"] == "work"
        assert message.progress["percent"] == 20.0

    def test_to_dict(self):
        """Test serialization to dict."""
        message = WorkoutStateMessage(
            has_active_workout=True,
            phase="active",
            workout_name="Test",
            current_segment={"type": "work", "index": 0},
            progress={"percent": 50.0},
            next_segment={"type": "rest"},
        )

        data = message.to_dict()

        assert data["has_active_workout"] is True
        assert data["phase"] == "active"
        assert data["workout_name"] == "Test"
        assert data["current_segment"]["type"] == "work"

    def test_no_workout(self):
        """Test creating from no workout status."""
        status = {"has_active_workout": False}

        message = WorkoutStateMessage.from_status(status)

        assert message.has_active_workout is False
        assert message.phase == "no_workout"
        assert message.workout_name is None

    def test_from_status_complete(self):
        """Test creating from complete workout status."""
        status = {
            "has_active_workout": False,
            "phase": "complete",
            "workout_name": "Finished Workout",
        }

        message = WorkoutStateMessage.from_status(status)

        assert message.has_active_workout is False
        assert message.phase == "complete"


class TestStateUpdateWithWorkout:
    """Test extended StateUpdate with workout."""

    def test_state_update_with_workout(self):
        """Test StateUpdate includes workout field."""
        workout_msg = WorkoutStateMessage(
            has_active_workout=True,
            phase="active",
            workout_name="Test Workout",
        )

        update = StateUpdate(workout=workout_msg)
        json_str = update.to_json()
        data = json.loads(json_str)

        assert "workout" in data
        assert data["workout"]["has_active_workout"] is True
        assert data["workout"]["workout_name"] == "Test Workout"

    def test_state_update_no_workout(self):
        """Test StateUpdate without workout."""
        update = StateUpdate()
        json_str = update.to_json()
        data = json.loads(json_str)

        # workout should be absent or null when not set
        assert data.get("workout") is None

    def test_state_update_round_trip(self):
        """Test round-trip serialization."""
        workout_msg = WorkoutStateMessage(
            has_active_workout=True,
            phase="active",
            workout_name="Round Trip Test",
            current_segment={"type": "work", "index": 2},
            progress={"percent": 40.0},
        )

        original = StateUpdate(workout=workout_msg)
        json_str = original.to_json()
        data = json.loads(json_str)

        reconstructed = StateUpdate.from_dict(data)

        assert reconstructed.workout is not None
        assert reconstructed.workout.has_active_workout is True
        assert reconstructed.workout.workout_name == "Round Trip Test"
        assert reconstructed.workout.phase == "active"


class TestWorkoutStateMessageFields:
    """Test individual fields of WorkoutStateMessage."""

    def test_default_values(self):
        """Test default values are set correctly."""
        msg = WorkoutStateMessage()

        assert msg.has_active_workout is False
        assert msg.phase == "no_workout"
        assert msg.workout_name is None
        assert msg.current_segment is None
        assert msg.progress is None
        assert msg.next_segment is None

    def test_all_fields_set(self):
        """Test all fields can be set."""
        msg = WorkoutStateMessage(
            has_active_workout=True,
            phase="active",
            workout_name="Full Workout",
            current_segment={"type": "warmup", "index": 0, "elapsed_seconds": 30},
            progress={
                "segments_completed": 0,
                "segments_total": 5,
                "percent": 0.0,
            },
            next_segment={"type": "work", "target_distance_m": 100},
        )

        assert msg.has_active_workout is True
        assert msg.current_segment["elapsed_seconds"] == 30
        assert msg.progress["segments_total"] == 5
        assert msg.next_segment["target_distance_m"] == 100
