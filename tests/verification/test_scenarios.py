"""Tests for scenario-based integration testing."""

import pytest
import pytest_asyncio
from pathlib import Path

from verification.scenarios import ScenarioRunner, Scenario, Step, StepResult
from verification.mocks import MockVisionStateStore


class TestScenarioModels:
    """Test scenario model classes."""

    def test_load_scenario_yaml(self, tmp_path):
        """Test 12: Load scenario from YAML."""
        yaml_content = """
name: Basic Session Test
description: Test session start/stop
tags: [core, session]
steps:
  - action: start_session
    expect:
      session.active: true
  - action: wait
    params:
      duration: 0.1
  - action: end_session
    expect:
      session.active: false
"""
        path = tmp_path / "test_scenario.yaml"
        path.write_text(yaml_content)

        scenario = Scenario.from_yaml(path)
        assert scenario.name == "Basic Session Test"
        assert len(scenario.steps) == 3
        assert scenario.tags == ["core", "session"]

    def test_step_from_dict(self):
        """Test Step.from_dict creates step correctly."""
        data = {
            "action": "set_swimming",
            "params": {"value": True},
            "expect": {"system.is_swimming": True},
            "description": "Start swimming",
        }

        step = Step.from_dict(data)
        assert step.action == "set_swimming"
        assert step.params == {"value": True}
        assert step.expect == {"system.is_swimming": True}
        assert step.description == "Start swimming"

    def test_scenario_from_dict(self):
        """Test Scenario.from_dict creates scenario correctly."""
        data = {
            "name": "Test Scenario",
            "description": "A test",
            "steps": [
                {"action": "start_session", "expect": {"session.active": True}},
            ],
            "tags": ["test"],
        }

        scenario = Scenario.from_dict(data)
        assert scenario.name == "Test Scenario"
        assert len(scenario.steps) == 1
        assert scenario.steps[0].action == "start_session"

    def test_step_result_creation(self):
        """Test StepResult creation."""
        step = Step(action="start_session")
        result = StepResult(
            step=step,
            success=True,
            actual={"session": {"active": True}},
            duration_ms=50.0,
        )

        assert result.success is True
        assert result.duration_ms == 50.0


class TestScenarioRunner:
    """Test scenario runner execution."""

    @pytest.fixture
    def mock_vision(self):
        return MockVisionStateStore()

    @pytest_asyncio.fixture
    async def runner(self, tmp_path: Path, mock_vision):
        """Set up scenario runner."""
        config_dir = tmp_path / ".slipstream"
        config_dir.mkdir(parents=True)
        (config_dir / "sessions").mkdir()

        runner = ScenarioRunner(
            config_dir=config_dir,
            mock_vision=mock_vision,
        )
        await runner.setup()
        yield runner
        await runner.teardown()

    @pytest.mark.asyncio
    async def test_execute_simple_scenario(self, runner):
        """Test 13: Execute a simple scenario."""
        scenario = Scenario(
            name="Simple Test",
            description="Start and end session",
            steps=[
                Step(action="start_session", expect={"session.active": True}),
                Step(action="wait", params={"duration": 0.1}),
                Step(action="end_session", expect={"session.active": False}),
            ],
        )

        result = await runner.run(scenario)
        assert result.success is True
        assert len(result.step_results) == 3

    @pytest.mark.asyncio
    async def test_scenario_with_vision_control(self, runner, mock_vision):
        """Test 14: Scenario with vision mock control."""
        mock_vision.start_session()

        scenario = Scenario(
            name="Vision Control",
            description="Test vision mock",
            steps=[
                Step(action="set_swimming", params={"value": True}),
                Step(action="set_stroke_rate", params={"rate": 50.0}),
                Step(action="wait", params={"duration": 0.1}),
            ],
        )

        result = await runner.run(scenario)
        assert result.success is True

        # Verify mock was updated
        state = mock_vision.get_state()
        assert state.is_swimming is True
        assert state.stroke_rate == 50.0

    @pytest.mark.asyncio
    async def test_scenario_failure_reporting(self, runner):
        """Test 16: Scenario failure reports details."""
        scenario = Scenario(
            name="Failing Test",
            description="Should fail expectation",
            steps=[
                Step(
                    action="wait",
                    params={"duration": 0.1},
                    expect={"session.active": True},  # Will fail - no session started
                ),
            ],
        )

        result = await runner.run(scenario)
        assert result.success is False
        assert len(result.failed_steps) == 1
        assert "session.active" in result.failed_steps[0].error

    @pytest.mark.asyncio
    async def test_run_multiple_scenarios(self, runner):
        """Test 17: Run multiple scenarios."""
        scenarios = [
            Scenario(
                name="Scenario 1",
                description="First",
                steps=[
                    Step(action="start_session", expect={"session.active": True}),
                    Step(action="end_session", expect={"session.active": False}),
                ],
            ),
            Scenario(
                name="Scenario 2",
                description="Second",
                steps=[
                    Step(action="wait", params={"duration": 0.1}),
                ],
            ),
        ]

        results = await runner.run_all(scenarios)
        assert len(results) == 2
        assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_scenario_result_summary(self, runner):
        """Test ScenarioResult.summary() output."""
        scenario = Scenario(
            name="Summary Test",
            description="Test summary",
            steps=[
                Step(action="start_session", expect={"session.active": True}),
            ],
        )

        result = await runner.run(scenario)
        summary = result.summary()

        assert "Summary Test" in summary
        assert "PASSED" in summary


class TestBuiltInScenarios:
    """Test pre-defined verification scenarios."""

    @pytest.fixture
    def mock_vision(self):
        return MockVisionStateStore()

    @pytest_asyncio.fixture
    async def runner(self, tmp_path: Path, mock_vision):
        """Set up scenario runner."""
        config_dir = tmp_path / ".slipstream"
        config_dir.mkdir(parents=True)
        (config_dir / "sessions").mkdir()

        runner = ScenarioRunner(
            config_dir=config_dir,
            mock_vision=mock_vision,
        )
        await runner.setup()
        yield runner
        await runner.teardown()

    @pytest.mark.asyncio
    async def test_session_lifecycle_scenario(self, runner, tmp_path):
        """Test 18: Session lifecycle scenario passes."""
        scenario_yaml = """
name: Session Lifecycle
description: Test basic session start/stop flow
tags: [core, session]

steps:
  - action: start_session
    description: Start a new session
    expect:
      session.active: true

  - action: wait
    params:
      duration: 0.2
    description: Let state propagate

  - action: end_session
    description: End the session
    expect:
      session.active: false
"""
        path = tmp_path / "session_lifecycle.yaml"
        path.write_text(scenario_yaml)

        scenario = Scenario.from_yaml(path)
        result = await runner.run(scenario)

        assert result.success is True, result.summary()

    @pytest.mark.asyncio
    async def test_stroke_query_scenario(self, runner, mock_vision, tmp_path):
        """Test 19: Stroke query scenario passes."""
        # Pre-configure vision state
        mock_vision.start_session()
        mock_vision.set_stroke_rate(52.5)
        mock_vision.set_stroke_count(100)

        scenario_yaml = """
name: Stroke Queries
description: Test stroke rate and count queries
tags: [core, metrics]

steps:
  - action: get_stroke_rate
    expect_result:
      rate: 52.5

  - action: get_stroke_count
    expect_result:
      count: 100
"""
        path = tmp_path / "stroke_queries.yaml"
        path.write_text(scenario_yaml)

        scenario = Scenario.from_yaml(path)
        result = await runner.run(scenario)

        assert result.success is True, result.summary()

    @pytest.mark.asyncio
    async def test_websocket_updates_scenario(self, runner, tmp_path):
        """Test 20: WebSocket state updates scenario passes."""
        scenario_yaml = """
name: WebSocket State Updates
description: Verify WebSocket broadcasts state changes
tags: [core, websocket]

steps:
  - action: wait
    params:
      duration: 0.1
    description: Wait for initial state
    expect:
      session.active: false

  - action: start_session
    expect:
      session.active: true

  - action: end_session
    expect:
      session.active: false
"""
        path = tmp_path / "websocket_updates.yaml"
        path.write_text(scenario_yaml)

        scenario = Scenario.from_yaml(path)
        result = await runner.run(scenario)

        assert result.success is True, result.summary()
