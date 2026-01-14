"""Tests for workout template storage (Phase 5 TDD)."""

import pytest
import json
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
            ],
        )

    def test_save_creates_file(self, storage, sample_workout, template_dir):
        """Test save creates template file."""
        storage.save(sample_workout)

        files = list(template_dir.glob("*.json"))
        assert len(files) == 1

    def test_save_filename(self, storage, sample_workout, template_dir):
        """Test save uses workout name for filename."""
        storage.save(sample_workout)

        files = list(template_dir.glob("*.json"))
        filename = files[0].name
        assert "4x100m_intervals" in filename.lower()

    def test_get_template(self, storage, sample_workout):
        """Test get retrieves saved template."""
        storage.save(sample_workout)

        retrieved = storage.get(sample_workout.workout_id)

        assert retrieved is not None
        assert retrieved.name == sample_workout.name
        assert len(retrieved.segments) == len(sample_workout.segments)

    def test_list_templates(self, storage, sample_workout):
        """Test list returns all templates."""
        # Save 3 workouts
        for i in range(3):
            workout = Workout(
                name=f"Workout {i}",
                segments=[WorkoutSegment(type="warmup", target_duration_seconds=60)],
            )
            storage.save(workout)

        templates = storage.list()

        assert len(templates) == 3

    def test_list_limit(self, storage):
        """Test list respects limit."""
        # Save 5 workouts
        for i in range(5):
            workout = Workout(
                name=f"Workout {i}",
                segments=[WorkoutSegment(type="warmup", target_duration_seconds=60)],
            )
            storage.save(workout)

        templates = storage.list(limit=3)

        assert len(templates) == 3

    def test_list_sorted(self, storage):
        """Test list sorted by created_at, newest first."""
        from datetime import datetime, timezone, timedelta

        # Save workouts with different creation times
        for i in range(3):
            workout = Workout(
                name=f"Workout {i}",
                segments=[WorkoutSegment(type="warmup", target_duration_seconds=60)],
            )
            # Manually set created_at for deterministic ordering
            workout.created_at = datetime.now(timezone.utc) + timedelta(seconds=i)
            storage.save(workout)

        templates = storage.list()

        # Newest first (Workout 2 created last)
        assert templates[0].name == "Workout 2"
        assert templates[1].name == "Workout 1"
        assert templates[2].name == "Workout 0"

    def test_delete_template(self, storage, sample_workout):
        """Test delete removes template."""
        storage.save(sample_workout)
        assert storage.get(sample_workout.workout_id) is not None

        result = storage.delete(sample_workout.workout_id)

        assert result is True
        assert storage.get(sample_workout.workout_id) is None

    def test_get_nonexistent(self, storage):
        """Test get non-existent returns None."""
        result = storage.get("nonexistent_id")

        assert result is None

    def test_creates_directory(self, tmp_path):
        """Test creates directory if not exists."""
        non_existent = tmp_path / "new_dir" / "templates"
        storage = TemplateStorage(non_existent)

        assert non_existent.exists()

    def test_handles_invalid_json(self, storage, template_dir, sample_workout):
        """Test handles invalid JSON gracefully."""
        # Save a valid workout
        storage.save(sample_workout)

        # Create a corrupted JSON file
        bad_file = template_dir / "corrupted.json"
        bad_file.write_text("not valid json{{{")

        # Should not raise, should return valid templates only
        templates = storage.list()

        assert len(templates) == 1
        assert templates[0].workout_id == sample_workout.workout_id

    def test_delete_nonexistent(self, storage):
        """Test delete non-existent returns False."""
        result = storage.delete("nonexistent_id")

        assert result is False
