"""Workout-specific pytest fixtures."""

import pytest
from pathlib import Path
from unittest.mock import Mock
from dataclasses import dataclass
from datetime import datetime, timezone

from src.mcp.workout.models import Workout, WorkoutSegment
from src.mcp.workout.state_machine import WorkoutStateMachine
from src.mcp.workout.templates import TemplateStorage


@dataclass
class MockVisionState:
    """Mock vision state for testing."""

    is_swimming: bool = True
    stroke_count: int = 0
    stroke_rate: float = 50.0


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
def mock_vision_state_store():
    """Mock vision state for transitions."""
    mock = Mock()
    mock.get_state.return_value = MockVisionState(
        is_swimming=True,
        stroke_count=0,
        stroke_rate=50.0,
    )
    return mock


@pytest.fixture
def temp_slipstream_dir(tmp_path: Path) -> Path:
    """Temp .slipstream directory structure."""
    config_dir = tmp_path / ".slipstream"
    config_dir.mkdir()
    (config_dir / "sessions").mkdir()
    (config_dir / "templates").mkdir()
    return config_dir
