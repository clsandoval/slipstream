"""Tests for workout server integration (Phase 7 TDD)."""

import pytest
from pathlib import Path
from unittest.mock import Mock
from dataclasses import dataclass

from src.mcp.workout.models import WorkoutPhase
from src.mcp.workout.state_machine import WorkoutStateMachine
from src.mcp.workout.templates import TemplateStorage
from src.mcp.workout.tools import create_workout_tools
from src.mcp.workout.transitions import TransitionMonitor


@dataclass
class MockVisionState:
    """Mock vision state."""

    is_swimming: bool = True
    stroke_count: int = 0
    stroke_rate: float = 50.0


class TestWorkoutServerComponents:
    """Test workout components work with server structure."""

    @pytest.fixture
    def config_dir(self, tmp_path: Path) -> Path:
        """Temp config directory."""
        config_dir = tmp_path / ".slipstream"
        config_dir.mkdir()
        (config_dir / "templates").mkdir()
        return config_dir

    @pytest.fixture
    def mock_vision_state_store(self):
        """Mock vision state store."""
        mock = Mock()
        mock.get_state.return_value = MockVisionState()
        return mock

    @pytest.fixture
    def workout_components(self, config_dir, mock_vision_state_store):
        """Create all workout components."""
        state_machine = WorkoutStateMachine()
        template_storage = TemplateStorage(config_dir / "templates")
        tools = create_workout_tools(state_machine, template_storage)
        transition_monitor = TransitionMonitor(
            state_machine=state_machine,
            vision_state_store=mock_vision_state_store,
        )

        return {
            "state_machine": state_machine,
            "template_storage": template_storage,
            "tools": tools,
            "transition_monitor": transition_monitor,
            "create_workout": tools[0],
            "start_workout": tools[1],
            "get_workout_status": tools[2],
            "skip_segment": tools[3],
            "end_workout": tools[4],
            "list_workout_templates": tools[5],
        }

    def test_workout_tools_created(self, workout_components):
        """Test workout tools are created correctly."""
        assert len(workout_components["tools"]) == 6
        for tool in workout_components["tools"]:
            assert callable(tool)

    def test_full_mcp_workflow(self, workout_components):
        """Test full workflow via MCP tools."""
        c = workout_components

        # Create workout
        result = c["create_workout"](
            name="4x100m Intervals",
            segments=[
                {"type": "warmup", "target_duration_seconds": 120},
                {"type": "work", "target_distance_m": 100},
                {"type": "rest", "target_duration_seconds": 30},
                {"type": "work", "target_distance_m": 100},
                {"type": "cooldown", "target_duration_seconds": 120},
            ],
        )
        assert "workout_id" in result
        assert result["segments_count"] == 5

        # Start workout
        result = c["start_workout"]()
        assert "started_at" in result
        assert c["state_machine"].phase == WorkoutPhase.ACTIVE

        # Get status
        result = c["get_workout_status"]()
        assert result["has_active_workout"] is True
        assert result["current_segment"]["type"] == "warmup"

        # Skip segments
        for _ in range(4):
            c["skip_segment"]()

        # End workout
        result = c["end_workout"]()
        assert result["summary"]["segments_completed"] == 4

    def test_transition_monitor_integration(
        self, workout_components, mock_vision_state_store
    ):
        """Test transition monitor works with state machine."""
        c = workout_components

        # Create and start workout
        c["create_workout"](
            name="Duration Test",
            segments=[
                {"type": "warmup", "target_duration_seconds": 60},
                {"type": "work", "target_distance_m": 100},
            ],
        )
        c["start_workout"]()

        # Initially should not transition (grace period)
        result = c["transition_monitor"].check()
        assert result["should_transition"] is False

    def test_template_storage_persistence(self, workout_components, config_dir):
        """Test templates persist to filesystem."""
        c = workout_components

        # Create with save as template
        c["create_workout"](
            name="Persistent Template",
            segments=[{"type": "warmup", "target_duration_seconds": 60}],
            save_as_template=True,
        )

        # Verify file exists
        templates = list((config_dir / "templates").glob("*.json"))
        assert len(templates) == 1

        # Create new storage pointing to same dir
        new_storage = TemplateStorage(config_dir / "templates")
        templates = new_storage.list()
        assert len(templates) == 1
        assert templates[0].name == "Persistent Template"


class TestWorkoutStateInWebSocket:
    """Test workout state in WebSocket updates."""

    def test_workout_state_in_state_update(self):
        """Test workout state can be included in StateUpdate."""
        from src.mcp.models.messages import StateUpdate, WorkoutStateMessage

        workout_msg = WorkoutStateMessage(
            has_active_workout=True,
            phase="active",
            workout_name="Test Workout",
            current_segment={"type": "work", "index": 1},
            progress={"percent": 40.0, "segments_completed": 2},
        )

        update = StateUpdate(workout=workout_msg)
        json_str = update.to_json()

        assert "workout" in json_str
        assert "Test Workout" in json_str
        assert "active" in json_str


class TestWorkoutToolsErrorHandling:
    """Test workout tools handle errors gracefully."""

    @pytest.fixture
    def setup(self, tmp_path: Path):
        """Setup tools."""
        sm = WorkoutStateMachine()
        ts = TemplateStorage(tmp_path / "templates")
        tools = create_workout_tools(sm, ts)
        return {
            "state_machine": sm,
            "create_workout": tools[0],
            "start_workout": tools[1],
            "skip_segment": tools[3],
            "end_workout": tools[4],
        }

    def test_start_without_create(self, setup):
        """Test starting without creating returns error."""
        result = setup["start_workout"]()
        assert "error" in result

    def test_skip_without_active(self, setup):
        """Test skipping without active workout returns error."""
        result = setup["skip_segment"]()
        assert "error" in result

    def test_end_without_active(self, setup):
        """Test ending without active workout returns error."""
        result = setup["end_workout"]()
        assert "error" in result

    def test_double_create(self, setup):
        """Test creating twice returns error."""
        setup["create_workout"](
            name="First",
            segments=[{"type": "warmup", "target_duration_seconds": 60}],
        )
        result = setup["create_workout"](
            name="Second",
            segments=[{"type": "warmup", "target_duration_seconds": 60}],
        )
        assert "error" in result

    def test_double_start(self, setup):
        """Test starting twice returns error."""
        setup["create_workout"](
            name="Test",
            segments=[{"type": "warmup", "target_duration_seconds": 60}],
        )
        setup["start_workout"]()
        result = setup["start_workout"]()
        assert "error" in result


class TestWorkoutWithSessionIntegration:
    """Test workout alongside session functionality."""

    @pytest.fixture
    def full_setup(self, tmp_path: Path):
        """Setup with all components."""
        from src.mcp.state_store import StateStore
        from src.mcp.storage.session_storage import SessionStorage
        from src.mcp.tools.session_tools import create_session_tools

        config_dir = tmp_path / ".slipstream"
        config_dir.mkdir()
        (config_dir / "sessions").mkdir()
        (config_dir / "templates").mkdir()

        state_store = StateStore()
        session_storage = SessionStorage(config_dir / "sessions")
        session_tools = create_session_tools(state_store, session_storage)

        workout_sm = WorkoutStateMachine()
        template_storage = TemplateStorage(config_dir / "templates")
        workout_tools = create_workout_tools(workout_sm, template_storage)

        return {
            "state_store": state_store,
            "workout_state_machine": workout_sm,
            "start_session": session_tools[0],
            "end_session": session_tools[1],
            "create_workout": workout_tools[0],
            "start_workout": workout_tools[1],
            "get_workout_status": workout_tools[2],
            "end_workout": workout_tools[4],
        }

    def test_session_and_workout_together(self, full_setup):
        """Test session and workout can run together."""
        s = full_setup

        # Start session
        result = s["start_session"]()
        assert "session_id" in result

        # Create and start workout
        s["create_workout"](
            name="Session Workout",
            segments=[
                {"type": "warmup", "target_duration_seconds": 60},
                {"type": "work", "target_distance_m": 100},
            ],
        )
        s["start_workout"]()

        # Both should be active
        assert s["state_store"].session.active is True
        assert s["workout_state_machine"].phase == WorkoutPhase.ACTIVE

    def test_workout_survives_session_end(self, full_setup):
        """Test workout continues after session ends."""
        s = full_setup

        # Start both
        s["start_session"]()
        s["create_workout"](
            name="Surviving Workout",
            segments=[{"type": "warmup", "target_duration_seconds": 60}],
        )
        s["start_workout"]()

        # End session
        s["end_session"]()

        # Workout should still be active
        assert s["workout_state_machine"].phase == WorkoutPhase.ACTIVE
        status = s["get_workout_status"]()
        assert status["has_active_workout"] is True
