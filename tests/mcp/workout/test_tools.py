"""Tests for MCP workout tools (Phase 4 TDD)."""

import pytest
from pathlib import Path
from unittest.mock import Mock

from src.mcp.workout.models import Workout, WorkoutSegment
from src.mcp.workout.state_machine import (
    WorkoutStateMachine,
    WorkoutExistsError,
    NoWorkoutError,
    WorkoutAlreadyActiveError,
    WorkoutNotActiveError,
)
from src.mcp.workout.templates import TemplateStorage
from src.mcp.workout.tools import create_workout_tools


class TestWorkoutTools:
    """Test MCP workout tools."""

    @pytest.fixture
    def state_machine(self) -> WorkoutStateMachine:
        """Fresh state machine."""
        return WorkoutStateMachine()

    @pytest.fixture
    def template_storage(self, tmp_path: Path) -> TemplateStorage:
        """TemplateStorage with temp directory."""
        return TemplateStorage(tmp_path / "templates")

    @pytest.fixture
    def tools(self, state_machine, template_storage):
        """Create workout tools."""
        return create_workout_tools(state_machine, template_storage)

    @pytest.fixture
    def create_workout(self, tools):
        """Get create_workout tool."""
        return tools[0]

    @pytest.fixture
    def start_workout(self, tools):
        """Get start_workout tool."""
        return tools[1]

    @pytest.fixture
    def get_workout_status(self, tools):
        """Get get_workout_status tool."""
        return tools[2]

    @pytest.fixture
    def skip_segment(self, tools):
        """Get skip_segment tool."""
        return tools[3]

    @pytest.fixture
    def end_workout(self, tools):
        """Get end_workout tool."""
        return tools[4]

    @pytest.fixture
    def list_workout_templates(self, tools):
        """Get list_workout_templates tool."""
        return tools[5]

    def test_create_workout_tool(self, create_workout, state_machine):
        """Test create_workout tool creates workout."""
        segments = [
            {"type": "warmup", "target_duration_seconds": 60},
            {"type": "work", "target_distance_m": 100},
        ]

        result = create_workout(name="Test Workout", segments=segments)

        assert "workout_id" in result
        assert result["segments_count"] == 2
        assert state_machine.workout is not None

    def test_create_workout_validates_segments(self, create_workout):
        """Test create_workout validates segment types."""
        segments = [{"type": "invalid_type", "target_duration_seconds": 60}]

        result = create_workout(name="Test", segments=segments)

        assert "error" in result

    def test_create_workout_saves_template(
        self, create_workout, template_storage, state_machine
    ):
        """Test create_workout saves template when requested."""
        segments = [{"type": "warmup", "target_duration_seconds": 60}]

        result = create_workout(
            name="Template Workout", segments=segments, save_as_template=True
        )

        templates = template_storage.list()
        assert len(templates) == 1
        assert templates[0].name == "Template Workout"

    def test_start_workout_tool(self, create_workout, start_workout, state_machine):
        """Test start_workout tool starts created workout."""
        segments = [{"type": "warmup", "target_duration_seconds": 60}]
        create_workout(name="Test", segments=segments)

        result = start_workout()

        assert "started_at" in result
        assert "first_segment" in result
        from src.mcp.workout.models import WorkoutPhase

        assert state_machine.phase == WorkoutPhase.ACTIVE

    def test_get_workout_status_tool(
        self, create_workout, start_workout, get_workout_status
    ):
        """Test get_workout_status tool returns status."""
        segments = [
            {"type": "warmup", "target_duration_seconds": 60},
            {"type": "work", "target_distance_m": 100},
        ]
        create_workout(name="Test", segments=segments)
        start_workout()

        result = get_workout_status()

        assert result["has_active_workout"] is True
        assert result["workout_name"] == "Test"
        assert "current_segment" in result
        assert "progress" in result

    def test_skip_segment_tool(
        self, create_workout, start_workout, skip_segment, state_machine
    ):
        """Test skip_segment tool skips current segment."""
        segments = [
            {"type": "warmup", "target_duration_seconds": 60},
            {"type": "work", "target_distance_m": 100},
        ]
        create_workout(name="Test", segments=segments)
        start_workout()

        result = skip_segment()

        assert "skipped" in result
        assert result["skipped"]["skipped"] is True
        assert result["now_on"]["type"] == "work"

    def test_end_workout_tool(
        self, create_workout, start_workout, skip_segment, end_workout, state_machine
    ):
        """Test end_workout tool ends workout."""
        segments = [
            {"type": "warmup", "target_duration_seconds": 60},
            {"type": "work", "target_distance_m": 100},
        ]
        create_workout(name="Test", segments=segments)
        start_workout()
        skip_segment()

        result = end_workout()

        assert "summary" in result
        assert result["summary"]["workout_name"] == "Test"
        assert result["summary"]["segments_completed"] == 1

    def test_list_workout_templates_tool(self, template_storage):
        """Test list_workout_templates tool lists templates."""
        # Create and save templates using separate state machines
        for i in range(3):
            sm = WorkoutStateMachine()
            tools = create_workout_tools(sm, template_storage)
            create_wkt = tools[0]
            segments = [{"type": "warmup", "target_duration_seconds": 60}]
            create_wkt(
                name=f"Template {i}", segments=segments, save_as_template=True
            )

        # List templates
        sm = WorkoutStateMachine()
        tools = create_workout_tools(sm, template_storage)
        list_templates = tools[5]

        result = list_templates(limit=5)

        assert result["count"] == 3

    def test_tool_error_handling(self, create_workout, start_workout):
        """Test tool returns error dict instead of raising."""
        segments = [{"type": "warmup", "target_duration_seconds": 60}]
        create_workout(name="Test", segments=segments)

        # Try to create another workout (should fail but not raise)
        result = create_workout(name="Test2", segments=segments)

        assert "error" in result

    def test_create_workout_tools_factory(self, state_machine, template_storage):
        """Test factory returns all 6 tools."""
        tools = create_workout_tools(state_machine, template_storage)

        assert len(tools) == 6
        # All should be callable
        for tool in tools:
            assert callable(tool)


class TestWorkoutToolsIntegration:
    """Integration tests with real components."""

    @pytest.fixture
    def integration_setup(self, tmp_path: Path):
        """Real components for integration tests."""
        state_machine = WorkoutStateMachine()
        template_storage = TemplateStorage(tmp_path / "templates")
        tools = create_workout_tools(state_machine, template_storage)

        return {
            "state_machine": state_machine,
            "template_storage": template_storage,
            "create_workout": tools[0],
            "start_workout": tools[1],
            "get_workout_status": tools[2],
            "skip_segment": tools[3],
            "end_workout": tools[4],
            "list_workout_templates": tools[5],
        }

    def test_full_workflow(self, integration_setup):
        """Test full workflow: create, start, advance, end."""
        s = integration_setup

        # Create workout
        result = s["create_workout"](
            name="Full Test",
            segments=[
                {"type": "warmup", "target_duration_seconds": 60},
                {"type": "work", "target_distance_m": 100},
                {"type": "rest", "target_duration_seconds": 30},
                {"type": "cooldown", "target_duration_seconds": 60},
            ],
        )
        assert "workout_id" in result

        # Start
        result = s["start_workout"]()
        assert "started_at" in result

        # Check status
        result = s["get_workout_status"]()
        assert result["has_active_workout"] is True

        # Skip 3 segments
        for _ in range(3):
            result = s["skip_segment"]()

        # End
        result = s["end_workout"]()
        assert result["summary"]["segments_completed"] == 3

    def test_template_round_trip(self, integration_setup):
        """Test template save and load."""
        s = integration_setup

        # Create with template save
        s["create_workout"](
            name="Template Test",
            segments=[{"type": "warmup", "target_duration_seconds": 60}],
            save_as_template=True,
        )

        # List templates
        result = s["list_workout_templates"](limit=10)

        assert result["count"] == 1
        assert result["templates"][0]["name"] == "Template Test"

    def test_tool_latency(self, integration_setup):
        """Test tools respond quickly."""
        import time

        s = integration_setup

        # Create workout
        start = time.time()
        s["create_workout"](
            name="Latency Test",
            segments=[{"type": "warmup", "target_duration_seconds": 60}],
        )
        create_time = time.time() - start

        # Start workout
        start = time.time()
        s["start_workout"]()
        start_time = time.time() - start

        # Get status
        start = time.time()
        for _ in range(10):
            s["get_workout_status"]()
        status_time = (time.time() - start) / 10

        # All should be under 100ms
        assert create_time < 0.1
        assert start_time < 0.1
        assert status_time < 0.1
