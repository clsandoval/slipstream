# Verification - TDD Implementation Plan

## Overview

Test-Driven Development plan for Branch 8: Verification. Integration testing infrastructure with mocked vision, simulated transcripts, and an E2E harness for manual verification.

**Dependencies**: Branches 1-4, 6, 7 (all core infrastructure)
**Complexity**: Medium

---

## Architecture

The verification system enables testing the full stack without real hardware (camera, microphone).

```
+--------------------------------------------------------------------------------+
|                         VERIFICATION ARCHITECTURE                               |
|                                                                                 |
|  What's MOCKED                          What's REAL                             |
|  +---------------------------+          +----------------------------------+    |
|  | MockVisionStateStore      |          | MCP Server (SwimCoachServer)     |    |
|  |   - is_swimming           |          | WebSocket Server                 |    |
|  |   - stroke_count          |          | State Store                      |    |
|  |   - stroke_rate           |          | Session Storage                  |    |
|  |   - Controllable via API  |          | Workout State Machine            |    |
|  +---------------------------+          | Dashboard (React)                |    |
|                                         +----------------------------------+    |
|  +---------------------------+                                                  |
|  | MockTranscriptStream      |          Integration Points                      |
|  |   - Simulates STT output  |          +----------------------------------+    |
|  |   - Scripted utterances   |          | WebSocket Client (test)          |    |
|  |   - Timing control        |          |   - Connects to server           |    |
|  +---------------------------+          |   - Receives StateUpdate         |    |
|                                         |   - Asserts state changes        |    |
|  +---------------------------+          +----------------------------------+    |
|  | ScenarioRunner            |                                                  |
|  |   - Executes test scripts |          E2E Harness (manual)                    |
|  |   - Coordinates mocks     |          +----------------------------------+    |
|  |   - Verifies outcomes     |          | Starts server + dashboard        |    |
|  +---------------------------+          | Optional real STT connection     |    |
|                                         | Prints verification checklist    |    |
|                                         +----------------------------------+    |
+--------------------------------------------------------------------------------+
```

### Key Design Decisions

1. **Vision is Always Mocked**: CV requires hardware. `MockVisionStateStore` provides controllable stroke/swimming state.

2. **Two Testing Modes**:
   - **Automated**: Mock transcript stream, programmatic MCP calls, WebSocket assertions
   - **Manual E2E**: Real dashboard, optional real voice, human verification

3. **WebSocket as Verification Point**: The dashboard receives state via WebSocket. If WebSocket state is correct, dashboard will render correctly.

4. **Scenario-Based Testing**: Pre-defined scenarios (workout flow, stroke queries) that exercise the full stack.

5. **Minimal Agent Mocking**: For automated tests, we call MCP tools directly rather than mocking the full Claude agent. The agent's behavior is tested via the E2E harness.

---

## Phase 1: Mock Infrastructure

**Goal**: Create controllable mocks for vision and transcript input.

### Tests First (`tests/verification/test_mocks.py`)

```python
import pytest
from datetime import datetime
from verification.mocks.vision import MockVisionStateStore
from verification.mocks.transcript import MockTranscriptStream, Utterance


class TestMockVisionStateStore:
    """Test mock vision state store."""

    # Test 1: Default state
    def test_default_state(self):
        # Given new MockVisionStateStore
        # When get_state() called
        # Then returns default values (not swimming, 0 strokes)

    # Test 2: Set swimming state
    def test_set_swimming(self):
        # Given mock store
        # When set_swimming(True) called
        # Then get_state().is_swimming is True

    # Test 3: Set stroke count
    def test_set_stroke_count(self):
        # Given mock store
        # When set_stroke_count(50) called
        # Then get_state().stroke_count is 50

    # Test 4: Set stroke rate
    def test_set_stroke_rate(self):
        # Given mock store
        # When set_stroke_rate(52.5) called
        # Then get_state().stroke_rate is 52.5

    # Test 5: Increment strokes
    def test_increment_strokes(self):
        # Given mock store with 10 strokes
        # When increment_strokes(5) called
        # Then stroke_count is 15

    # Test 6: Simulate swimming burst
    def test_simulate_swimming_burst(self):
        # Given mock store
        # When simulate_swimming(duration_seconds=10, stroke_rate=50) called
        # Then is_swimming=True, strokes increment over time

    # Test 7: Reset state
    def test_reset(self):
        # Given mock store with modified state
        # When reset() called
        # Then returns to default state

    # Test 8: Compatible with real interface
    def test_interface_compatibility(self):
        # Given MockVisionStateStore
        # When used where VisionStateStore expected
        # Then works (duck typing)


class TestMockTranscriptStream:
    """Test mock transcript stream."""

    # Test 9: Create with utterances
    def test_create_with_utterances(self):
        # Given list of Utterance objects
        # When MockTranscriptStream created
        # Then utterances stored in order

    # Test 10: Get next utterance
    def test_get_next(self):
        # Given stream with 3 utterances
        # When get_next() called 3 times
        # Then returns utterances in order

    # Test 11: Get next returns None when empty
    def test_get_next_empty(self):
        # Given stream with all utterances consumed
        # When get_next() called
        # Then returns None

    # Test 12: Utterance with delay
    def test_utterance_delay(self):
        # Given Utterance with delay_seconds=1.0
        # When get_next() called
        # Then waits 1 second before returning

    # Test 13: Reset stream
    def test_reset(self):
        # Given consumed stream
        # When reset() called
        # Then can iterate from beginning again

    # Test 14: Async iteration
    async def test_async_iteration(self):
        # Given stream with utterances
        # When async for utterance in stream
        # Then yields all utterances

    # Test 15: Utterance format matches STT output
    def test_utterance_format(self):
        # Given Utterance with text and timestamp
        # When to_dict() called
        # Then matches expected transcript.log format


class TestUtterance:
    """Test Utterance data model."""

    # Test 16: Create utterance
    def test_create_utterance(self):
        # Given text="what's my stroke rate"
        # When Utterance created
        # Then text stored, timestamp generated

    # Test 17: Utterance with custom timestamp
    def test_custom_timestamp(self):
        # Given specific timestamp
        # When Utterance created with timestamp
        # Then uses provided timestamp

    # Test 18: Utterance sequence ID
    def test_sequence_id(self):
        # Given multiple utterances
        # When created in sequence
        # Then each has incrementing sequence_id
```

### Implementation

```python
# verification/mocks/__init__.py
from verification.mocks.vision import MockVisionStateStore
from verification.mocks.transcript import MockTranscriptStream, Utterance

__all__ = ["MockVisionStateStore", "MockTranscriptStream", "Utterance"]
```

```python
# verification/mocks/vision.py
from __future__ import annotations

import asyncio
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class MockVisionState:
    """Mock vision state matching real VisionState interface."""
    is_swimming: bool = False
    stroke_count: int = 0
    stroke_rate: float = 0.0
    pose_detected: bool = False
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MockVisionStateStore:
    """
    Mock vision state store for testing.

    Provides controllable vision state without requiring
    actual camera/pose estimation hardware.

    Thread-safe for use in async contexts.
    """

    def __init__(self) -> None:
        self._state = MockVisionState()
        self._lock = threading.Lock()
        self._swimming_task: asyncio.Task | None = None

    def get_state(self) -> MockVisionState:
        """Get current vision state."""
        with self._lock:
            return MockVisionState(
                is_swimming=self._state.is_swimming,
                stroke_count=self._state.stroke_count,
                stroke_rate=self._state.stroke_rate,
                pose_detected=self._state.pose_detected,
                confidence=self._state.confidence,
                timestamp=datetime.now(timezone.utc),
            )

    def set_swimming(self, is_swimming: bool) -> None:
        """Set swimming state."""
        with self._lock:
            self._state.is_swimming = is_swimming
            self._state.pose_detected = is_swimming

    def set_stroke_count(self, count: int) -> None:
        """Set stroke count."""
        with self._lock:
            self._state.stroke_count = count

    def set_stroke_rate(self, rate: float) -> None:
        """Set stroke rate."""
        with self._lock:
            self._state.stroke_rate = rate

    def increment_strokes(self, count: int = 1) -> None:
        """Increment stroke count."""
        with self._lock:
            self._state.stroke_count += count

    async def simulate_swimming(
        self,
        duration_seconds: float,
        stroke_rate: float = 50.0,
        start_strokes: int | None = None,
    ) -> None:
        """
        Simulate a swimming burst.

        Args:
            duration_seconds: How long to swim
            stroke_rate: Strokes per minute
            start_strokes: Starting stroke count (None = keep current)
        """
        with self._lock:
            self._state.is_swimming = True
            self._state.pose_detected = True
            self._state.stroke_rate = stroke_rate
            if start_strokes is not None:
                self._state.stroke_count = start_strokes

        strokes_per_second = stroke_rate / 60.0
        elapsed = 0.0
        interval = 0.1  # Update every 100ms

        while elapsed < duration_seconds:
            await asyncio.sleep(interval)
            elapsed += interval

            with self._lock:
                self._state.stroke_count += int(strokes_per_second * interval)

        with self._lock:
            self._state.is_swimming = False

    def reset(self) -> None:
        """Reset to default state."""
        with self._lock:
            self._state = MockVisionState()
```

```python
# verification/mocks/transcript.py
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Iterator


_sequence_counter = 0


def _next_sequence_id() -> int:
    """Get next sequence ID."""
    global _sequence_counter
    _sequence_counter += 1
    return _sequence_counter


def _reset_sequence_counter() -> None:
    """Reset sequence counter (for testing)."""
    global _sequence_counter
    _sequence_counter = 0


@dataclass
class Utterance:
    """
    A simulated voice utterance.

    Matches the format expected from the STT service.
    """
    text: str
    delay_seconds: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sequence_id: int = field(default_factory=_next_sequence_id)
    confidence: float = 0.95

    def to_dict(self) -> dict[str, Any]:
        """Convert to transcript log format."""
        return {
            "sequence_id": self.sequence_id,
            "timestamp": self.timestamp.isoformat(),
            "text": self.text,
            "confidence": self.confidence,
        }

    def to_log_line(self) -> str:
        """Convert to transcript.log line format."""
        return f"[{self.sequence_id}] {self.timestamp.isoformat()} | {self.text}"


class MockTranscriptStream:
    """
    Mock transcript stream for testing.

    Simulates STT output with controllable timing.
    """

    def __init__(self, utterances: list[Utterance] | None = None) -> None:
        self._utterances = list(utterances) if utterances else []
        self._index = 0

    def add(self, text: str, delay_seconds: float = 0.0) -> Utterance:
        """Add an utterance to the stream."""
        utterance = Utterance(text=text, delay_seconds=delay_seconds)
        self._utterances.append(utterance)
        return utterance

    def get_next(self) -> Utterance | None:
        """Get next utterance (blocking if delay specified)."""
        if self._index >= len(self._utterances):
            return None

        utterance = self._utterances[self._index]
        self._index += 1

        if utterance.delay_seconds > 0:
            import time
            time.sleep(utterance.delay_seconds)

        return utterance

    async def get_next_async(self) -> Utterance | None:
        """Get next utterance (async, respects delay)."""
        if self._index >= len(self._utterances):
            return None

        utterance = self._utterances[self._index]
        self._index += 1

        if utterance.delay_seconds > 0:
            await asyncio.sleep(utterance.delay_seconds)

        return utterance

    def reset(self) -> None:
        """Reset to beginning of stream."""
        self._index = 0

    def __iter__(self) -> Iterator[Utterance]:
        """Iterate over utterances."""
        self.reset()
        while True:
            utterance = self.get_next()
            if utterance is None:
                break
            yield utterance

    async def __aiter__(self) -> AsyncIterator[Utterance]:
        """Async iterate over utterances."""
        self.reset()
        while True:
            utterance = await self.get_next_async()
            if utterance is None:
                break
            yield utterance

    def __len__(self) -> int:
        """Number of utterances."""
        return len(self._utterances)

    @property
    def remaining(self) -> int:
        """Number of utterances remaining."""
        return len(self._utterances) - self._index
```

---

## Phase 2: Integration Test Harness

**Goal**: Test server + WebSocket + state flow with mocks.

### Tests First (`tests/verification/test_integration.py`)

```python
import pytest
import asyncio
import json
import websockets
from pathlib import Path

from verification.mocks import MockVisionStateStore
from src.mcp.server import SwimCoachServer


class TestServerIntegration:
    """Integration tests for full server stack."""

    @pytest.fixture
    async def mock_vision(self):
        """Mock vision state store."""
        return MockVisionStateStore()

    @pytest.fixture
    async def server(self, tmp_path: Path, mock_vision):
        """Running server with mocked vision."""
        server = SwimCoachServer(
            websocket_port=0,  # Random port
            config_dir=tmp_path / ".slipstream",
            vision_state_store=mock_vision,
        )
        await server.start()
        yield server
        await server.stop()

    @pytest.fixture
    async def ws_client(self, server):
        """WebSocket client connected to server."""
        uri = f"ws://localhost:{server.websocket_server.port}"
        async with websockets.connect(uri) as ws:
            yield ws

    # Test 1: Server starts with mocked vision
    async def test_server_starts(self, server):
        # Given server with mock vision
        # Then server is running
        # And websocket port is assigned
        assert server.websocket_server.port > 0

    # Test 2: WebSocket receives initial state
    async def test_websocket_initial_state(self, ws_client):
        # Given connected WebSocket client
        # When first message received
        # Then it's a state_update with default values
        msg = await asyncio.wait_for(ws_client.recv(), timeout=2.0)
        data = json.loads(msg)
        assert data["type"] == "state_update"
        assert data["session"]["active"] is False

    # Test 3: Start session updates WebSocket
    async def test_start_session_updates_websocket(self, server, ws_client):
        # Given server and connected client
        # When start_session called
        # Then WebSocket receives state with active=True

        # Consume initial state
        await ws_client.recv()

        # Start session via tool
        result = server._start_session()
        assert "session_id" in result

        # Wait for state update
        msg = await asyncio.wait_for(ws_client.recv(), timeout=2.0)
        data = json.loads(msg)
        assert data["session"]["active"] is True

    # Test 4: Mock vision state flows to WebSocket
    async def test_vision_state_flows_to_websocket(self, server, ws_client, mock_vision):
        # Given server with mock vision
        # When mock vision set to swimming with strokes
        # Then WebSocket receives updated state

        await ws_client.recv()  # Consume initial

        mock_vision.set_swimming(True)
        mock_vision.set_stroke_count(25)
        mock_vision.set_stroke_rate(52.0)

        # Wait for next push (within push_interval)
        msg = await asyncio.wait_for(ws_client.recv(), timeout=1.0)
        data = json.loads(msg)
        assert data["system"]["is_swimming"] is True

    # Test 5: End session updates WebSocket
    async def test_end_session_updates_websocket(self, server, ws_client):
        # Given active session
        # When end_session called
        # Then WebSocket receives state with active=False

        await ws_client.recv()
        server._start_session()
        await ws_client.recv()  # Consume start update

        server._end_session()

        msg = await asyncio.wait_for(ws_client.recv(), timeout=2.0)
        data = json.loads(msg)
        assert data["session"]["active"] is False

    # Test 6: Stroke rate query returns mock data
    async def test_stroke_rate_query(self, server, mock_vision):
        # Given mock vision with stroke rate 55.0
        # When get_stroke_rate tool called
        # Then returns 55.0

        mock_vision.set_stroke_rate(55.0)
        mock_vision.set_swimming(True)

        result = server._get_stroke_rate()
        assert result["stroke_rate"] == 55.0

    # Test 7: Distance calculation uses mock strokes
    async def test_distance_calculation(self, server, mock_vision):
        # Given mock vision with 100 strokes, DPS=1.8
        # When get_estimated_distance called
        # Then returns ~180m

        server._start_session()
        mock_vision.set_stroke_count(100)

        result = server._get_estimated_distance()
        assert result["estimated_distance_m"] == pytest.approx(180.0, rel=0.1)

    # Test 8: Multiple WebSocket clients receive updates
    async def test_multiple_clients(self, server):
        # Given 3 WebSocket clients
        # When state changes
        # Then all clients receive update

        uri = f"ws://localhost:{server.websocket_server.port}"

        async with websockets.connect(uri) as ws1, \
                   websockets.connect(uri) as ws2, \
                   websockets.connect(uri) as ws3:

            # Consume initial states
            await asyncio.gather(ws1.recv(), ws2.recv(), ws3.recv())

            # Trigger change
            server._start_session()

            # All should receive
            msgs = await asyncio.gather(
                asyncio.wait_for(ws1.recv(), timeout=2.0),
                asyncio.wait_for(ws2.recv(), timeout=2.0),
                asyncio.wait_for(ws3.recv(), timeout=2.0),
            )

            for msg in msgs:
                data = json.loads(msg)
                assert data["session"]["active"] is True


class TestWorkoutIntegration:
    """Integration tests for workout system with mocks."""

    @pytest.fixture
    async def mock_vision(self):
        return MockVisionStateStore()

    @pytest.fixture
    async def server(self, tmp_path: Path, mock_vision):
        server = SwimCoachServer(
            websocket_port=0,
            config_dir=tmp_path / ".slipstream",
            vision_state_store=mock_vision,
        )
        await server.start()
        yield server
        await server.stop()

    # Test 9: Create workout via MCP tool
    async def test_create_workout(self, server):
        # Given server
        # When create_workout tool called
        # Then workout created successfully

        result = server._create_workout(
            name="Test Workout",
            segments=[
                {"type": "warmup", "target_duration_seconds": 60},
                {"type": "work", "target_distance_m": 100},
                {"type": "cooldown", "target_duration_seconds": 60},
            ]
        )
        assert "workout_id" in result
        assert result["segments_count"] == 3

    # Test 10: Workout state in WebSocket
    async def test_workout_state_in_websocket(self, server):
        # Given created and started workout
        # When WebSocket message received
        # Then includes workout state

        uri = f"ws://localhost:{server.websocket_server.port}"

        async with websockets.connect(uri) as ws:
            await ws.recv()  # Initial

            server._create_workout(
                name="Test",
                segments=[{"type": "work", "target_duration_seconds": 60}]
            )
            server._start_workout()

            msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
            data = json.loads(msg)

            assert data["workout"] is not None
            assert data["workout"]["has_active_workout"] is True

    # Test 11: Full workout flow
    async def test_full_workout_flow(self, server, mock_vision):
        # Given server with mock vision
        # When full workout executed (create, start, advance, end)
        # Then all steps succeed

        # Create
        result = server._create_workout(
            name="Quick Test",
            segments=[
                {"type": "warmup", "target_duration_seconds": 10},
                {"type": "work", "target_duration_seconds": 10},
            ]
        )
        assert "error" not in result

        # Start
        result = server._start_workout()
        assert "error" not in result

        # Skip to advance
        result = server._skip_segment()
        assert "error" not in result

        # End
        result = server._end_workout()
        assert "summary" in result
```

### Tests for Scenario Runner (`tests/verification/test_scenarios.py`)

```python
import pytest
import asyncio
from pathlib import Path

from verification.scenarios import ScenarioRunner, Scenario, Step
from verification.mocks import MockVisionStateStore, MockTranscriptStream


class TestScenarioRunner:
    """Test scenario-based integration testing."""

    @pytest.fixture
    def mock_vision(self):
        return MockVisionStateStore()

    @pytest.fixture
    def mock_transcript(self):
        return MockTranscriptStream()

    # Test 12: Load scenario from YAML
    def test_load_scenario_yaml(self, tmp_path):
        # Given YAML scenario file
        # When Scenario.from_yaml(path) called
        # Then scenario loaded with steps

        yaml_content = """
name: Basic Session Test
description: Test session start/stop
steps:
  - action: start_session
    expect:
      session.active: true
  - action: wait
    duration: 1.0
  - action: end_session
    expect:
      session.active: false
"""
        path = tmp_path / "test_scenario.yaml"
        path.write_text(yaml_content)

        scenario = Scenario.from_yaml(path)
        assert scenario.name == "Basic Session Test"
        assert len(scenario.steps) == 3

    # Test 13: Execute scenario step
    async def test_execute_step(self, mock_vision):
        # Given scenario runner and step
        # When step executed
        # Then action performed and expectation checked
        pass  # Implementation detail

    # Test 14: Scenario with vision mock control
    def test_scenario_vision_control(self):
        # Given scenario with set_swimming step
        # When executed
        # Then mock vision state updated
        pass

    # Test 15: Scenario with transcript simulation
    def test_scenario_transcript(self):
        # Given scenario with utterance step
        # When executed
        # Then transcript stream produces utterance
        pass

    # Test 16: Scenario failure reporting
    async def test_scenario_failure(self):
        # Given scenario with failing expectation
        # When executed
        # Then reports which step failed and why
        pass

    # Test 17: Run multiple scenarios
    async def test_run_multiple_scenarios(self):
        # Given list of scenarios
        # When runner.run_all() called
        # Then all scenarios executed, results aggregated
        pass


class TestBuiltInScenarios:
    """Test pre-defined verification scenarios."""

    # Test 18: Session lifecycle scenario passes
    async def test_session_lifecycle_scenario(self, tmp_path):
        # Given session_lifecycle scenario
        # When executed with mocked server
        # Then passes
        pass

    # Test 19: Stroke query scenario passes
    async def test_stroke_query_scenario(self, tmp_path):
        # Given stroke_query scenario
        # When executed
        # Then passes
        pass

    # Test 20: Workout flow scenario passes
    async def test_workout_flow_scenario(self, tmp_path):
        # Given workout_flow scenario
        # When executed
        # Then passes
        pass
```

### Implementation

```python
# verification/scenarios/__init__.py
from verification.scenarios.runner import ScenarioRunner
from verification.scenarios.models import Scenario, Step, StepResult

__all__ = ["ScenarioRunner", "Scenario", "Step", "StepResult"]
```

```python
# verification/scenarios/models.py
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Step:
    """A single step in a scenario."""
    action: str
    params: dict[str, Any] = field(default_factory=dict)
    expect: dict[str, Any] = field(default_factory=dict)
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Step:
        """Create step from dictionary."""
        return cls(
            action=data["action"],
            params=data.get("params", {}),
            expect=data.get("expect", {}),
            description=data.get("description", ""),
        )


@dataclass
class StepResult:
    """Result of executing a step."""
    step: Step
    success: bool
    actual: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    duration_ms: float = 0.0


@dataclass
class Scenario:
    """A test scenario with multiple steps."""
    name: str
    description: str
    steps: list[Step]
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, path: Path) -> Scenario:
        """Load scenario from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)

        return cls(
            name=data["name"],
            description=data.get("description", ""),
            steps=[Step.from_dict(s) for s in data["steps"]],
            tags=data.get("tags", []),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Scenario:
        """Create scenario from dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            steps=[Step.from_dict(s) for s in data["steps"]],
            tags=data.get("tags", []),
        )


@dataclass
class ScenarioResult:
    """Result of running a scenario."""
    scenario: Scenario
    success: bool
    step_results: list[StepResult]
    duration_ms: float = 0.0

    @property
    def failed_steps(self) -> list[StepResult]:
        """Get failed step results."""
        return [r for r in self.step_results if not r.success]
```

```python
# verification/scenarios/runner.py
from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import websockets

from src.mcp.server import SwimCoachServer
from verification.mocks import MockVisionStateStore, MockTranscriptStream
from verification.scenarios.models import (
    Scenario,
    Step,
    StepResult,
    ScenarioResult,
)


@dataclass
class ScenarioRunner:
    """
    Executes test scenarios against the server.

    Coordinates mocks, server, and WebSocket client
    to run integration tests.
    """
    config_dir: Path
    mock_vision: MockVisionStateStore | None = None
    mock_transcript: MockTranscriptStream | None = None

    _server: SwimCoachServer | None = None
    _ws: Any = None
    _last_state: dict[str, Any] | None = None

    async def setup(self) -> None:
        """Initialize server and connections."""
        self.mock_vision = self.mock_vision or MockVisionStateStore()

        self._server = SwimCoachServer(
            websocket_port=0,
            config_dir=self.config_dir,
            vision_state_store=self.mock_vision,
        )
        await self._server.start()

        # Connect WebSocket
        uri = f"ws://localhost:{self._server.websocket_server.port}"
        self._ws = await websockets.connect(uri)

        # Get initial state
        msg = await self._ws.recv()
        self._last_state = json.loads(msg)

    async def teardown(self) -> None:
        """Clean up resources."""
        if self._ws:
            await self._ws.close()
        if self._server:
            await self._server.stop()

    async def run(self, scenario: Scenario) -> ScenarioResult:
        """
        Run a scenario.

        Args:
            scenario: Scenario to execute

        Returns:
            ScenarioResult with pass/fail and details
        """
        start = time.perf_counter()
        step_results: list[StepResult] = []

        for step in scenario.steps:
            result = await self._execute_step(step)
            step_results.append(result)

            if not result.success:
                break  # Stop on first failure

        duration = (time.perf_counter() - start) * 1000
        success = all(r.success for r in step_results)

        return ScenarioResult(
            scenario=scenario,
            success=success,
            step_results=step_results,
            duration_ms=duration,
        )

    async def _execute_step(self, step: Step) -> StepResult:
        """Execute a single step."""
        start = time.perf_counter()

        try:
            # Execute action
            await self._execute_action(step.action, step.params)

            # Wait for state update if needed
            if step.expect:
                await self._wait_for_state_update()

            # Check expectations
            if step.expect:
                errors = self._check_expectations(step.expect)
                if errors:
                    return StepResult(
                        step=step,
                        success=False,
                        actual=self._last_state,
                        error="; ".join(errors),
                        duration_ms=(time.perf_counter() - start) * 1000,
                    )

            return StepResult(
                step=step,
                success=True,
                actual=self._last_state,
                duration_ms=(time.perf_counter() - start) * 1000,
            )

        except Exception as e:
            return StepResult(
                step=step,
                success=False,
                error=str(e),
                duration_ms=(time.perf_counter() - start) * 1000,
            )

    async def _execute_action(self, action: str, params: dict[str, Any]) -> Any:
        """Execute an action."""
        if action == "start_session":
            return self._server._start_session()
        elif action == "end_session":
            return self._server._end_session()
        elif action == "wait":
            await asyncio.sleep(params.get("duration", 1.0))
        elif action == "set_swimming":
            self.mock_vision.set_swimming(params.get("value", True))
        elif action == "set_stroke_count":
            self.mock_vision.set_stroke_count(params["count"])
        elif action == "set_stroke_rate":
            self.mock_vision.set_stroke_rate(params["rate"])
        elif action == "create_workout":
            return self._server._create_workout(**params)
        elif action == "start_workout":
            return self._server._start_workout()
        elif action == "skip_segment":
            return self._server._skip_segment()
        elif action == "end_workout":
            return self._server._end_workout()
        elif action == "get_stroke_rate":
            return self._server._get_stroke_rate()
        else:
            raise ValueError(f"Unknown action: {action}")

    async def _wait_for_state_update(self, timeout: float = 2.0) -> None:
        """Wait for next WebSocket state update."""
        try:
            msg = await asyncio.wait_for(self._ws.recv(), timeout=timeout)
            self._last_state = json.loads(msg)
        except asyncio.TimeoutError:
            pass  # Use last known state

    def _check_expectations(self, expect: dict[str, Any]) -> list[str]:
        """Check expectations against current state."""
        errors = []

        for path, expected in expect.items():
            actual = self._get_nested(self._last_state, path)
            if actual != expected:
                errors.append(f"{path}: expected {expected}, got {actual}")

        return errors

    def _get_nested(self, obj: dict, path: str) -> Any:
        """Get nested value by dot-separated path."""
        parts = path.split(".")
        current = obj
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current
```

---

## Phase 3: E2E Harness

**Goal**: Script for manual end-to-end testing with optional real voice.

### Tests First (`tests/verification/test_e2e_harness.py`)

```python
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from verification.e2e_harness import E2EHarness, HarnessConfig


class TestE2EHarness:
    """Test E2E harness setup and control."""

    # Test 21: Harness starts server
    async def test_harness_starts_server(self, tmp_path):
        # Given harness config
        # When harness.start() called
        # Then server running on expected port
        pass

    # Test 22: Harness opens dashboard URL
    def test_harness_dashboard_url(self, tmp_path):
        # Given running harness
        # When get_dashboard_url() called
        # Then returns correct URL
        pass

    # Test 23: Harness provides mock controls
    async def test_harness_mock_controls(self, tmp_path):
        # Given running harness
        # When harness.set_swimming(True) called
        # Then mock vision updated
        pass

    # Test 24: Harness CLI interface
    def test_harness_cli(self):
        # Given harness CLI args
        # When parsed
        # Then correct config created
        pass

    # Test 25: Harness prints checklist
    def test_harness_checklist(self, capsys):
        # When harness prints checklist
        # Then all verification items shown
        pass
```

### Implementation

```python
# verification/e2e_harness.py
"""
End-to-end testing harness for manual verification.

Usage:
    uv run python -m verification.e2e_harness [--port PORT] [--no-browser]

This starts the server with mocked vision and provides an interactive
console for controlling the mock state while you test the dashboard.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import webbrowser
from dataclasses import dataclass
from pathlib import Path

from src.mcp.server import SwimCoachServer
from verification.mocks import MockVisionStateStore


VERIFICATION_CHECKLIST = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                         VERIFICATION CHECKLIST                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  DASHBOARD DISPLAY (verify from 10ft)                                        ║
║  [ ] Large stroke rate number visible                                        ║
║  [ ] Stroke count displays correctly                                         ║
║  [ ] Session timer updates                                                   ║
║  [ ] Swimming/not-swimming indicator works                                   ║
║  [ ] Workout segment info displays (if workout active)                       ║
║                                                                              ║
║  SESSION FLOW                                                                ║
║  [ ] "Start session" creates new session                                     ║
║  [ ] Metrics update during session                                           ║
║  [ ] "End session" saves and shows summary                                   ║
║                                                                              ║
║  STROKE QUERIES (if testing voice)                                           ║
║  [ ] "What's my stroke rate?" returns current rate                           ║
║  [ ] "How many strokes?" returns stroke count                                ║
║  [ ] "How far have I swum?" returns distance estimate                        ║
║                                                                              ║
║  WORKOUT FLOW                                                                ║
║  [ ] Can create workout via voice/tool                                       ║
║  [ ] Segment transitions display correctly                                   ║
║  [ ] Progress indicator updates                                              ║
║  [ ] "Skip this segment" advances to next                                    ║
║  [ ] Workout completion shows summary                                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

INTERACTIVE_HELP = """
Interactive Commands:
  swim [rate]     - Start swimming (default rate: 50 spm)
  stop            - Stop swimming
  strokes <n>     - Set stroke count to n
  rate <n>        - Set stroke rate to n
  session start   - Start a session
  session end     - End current session
  workout         - Create a test workout
  status          - Show current mock state
  checklist       - Show verification checklist
  help            - Show this help
  quit            - Exit harness
"""


@dataclass
class HarnessConfig:
    """Configuration for E2E harness."""
    websocket_port: int = 8765
    dashboard_port: int = 5173
    config_dir: Path = Path.home() / ".slipstream-test"
    open_browser: bool = True


class E2EHarness:
    """
    Interactive harness for end-to-end testing.

    Runs the server with mocked vision and provides
    console commands for controlling mock state.
    """

    def __init__(self, config: HarnessConfig | None = None) -> None:
        self.config = config or HarnessConfig()
        self.mock_vision = MockVisionStateStore()
        self.server: SwimCoachServer | None = None
        self._running = False

    async def start(self) -> None:
        """Start the harness."""
        self.config.config_dir.mkdir(parents=True, exist_ok=True)
        (self.config.config_dir / "sessions").mkdir(exist_ok=True)

        self.server = SwimCoachServer(
            websocket_port=self.config.websocket_port,
            config_dir=self.config.config_dir,
            vision_state_store=self.mock_vision,
        )
        await self.server.start()
        self._running = True

        print(f"\n✓ Server started on WebSocket port {self.server.websocket_server.port}")
        print(f"✓ Dashboard should connect to ws://localhost:{self.server.websocket_server.port}")

        if self.config.open_browser:
            url = f"http://localhost:{self.config.dashboard_port}"
            print(f"✓ Opening dashboard at {url}")
            webbrowser.open(url)

    async def stop(self) -> None:
        """Stop the harness."""
        self._running = False
        if self.server:
            await self.server.stop()
        print("\n✓ Harness stopped")

    def get_dashboard_url(self) -> str:
        """Get dashboard URL."""
        return f"http://localhost:{self.config.dashboard_port}"

    async def run_interactive(self) -> None:
        """Run interactive console."""
        print(INTERACTIVE_HELP)
        print("\nReady for commands. Type 'checklist' to see verification items.\n")

        while self._running:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: input("harness> ")
                )
                await self._handle_command(line.strip())
            except (EOFError, KeyboardInterrupt):
                break

    async def _handle_command(self, line: str) -> None:
        """Handle a console command."""
        if not line:
            return

        parts = line.split()
        cmd = parts[0].lower()
        args = parts[1:]

        try:
            if cmd == "swim":
                rate = float(args[0]) if args else 50.0
                self.mock_vision.set_swimming(True)
                self.mock_vision.set_stroke_rate(rate)
                print(f"Swimming at {rate} spm")

            elif cmd == "stop":
                self.mock_vision.set_swimming(False)
                print("Stopped swimming")

            elif cmd == "strokes":
                count = int(args[0])
                self.mock_vision.set_stroke_count(count)
                print(f"Stroke count: {count}")

            elif cmd == "rate":
                rate = float(args[0])
                self.mock_vision.set_stroke_rate(rate)
                print(f"Stroke rate: {rate}")

            elif cmd == "session":
                if args and args[0] == "start":
                    result = self.server._start_session()
                    print(f"Session started: {result.get('session_id', 'unknown')}")
                elif args and args[0] == "end":
                    result = self.server._end_session()
                    print(f"Session ended: {result}")
                else:
                    print("Usage: session start|end")

            elif cmd == "workout":
                result = self.server._create_workout(
                    name="Test Workout",
                    segments=[
                        {"type": "warmup", "target_duration_seconds": 60},
                        {"type": "work", "target_distance_m": 100},
                        {"type": "rest", "target_duration_seconds": 30},
                        {"type": "work", "target_distance_m": 100},
                        {"type": "cooldown", "target_duration_seconds": 60},
                    ]
                )
                print(f"Workout created: {result}")
                self.server._start_workout()
                print("Workout started")

            elif cmd == "status":
                state = self.mock_vision.get_state()
                print(f"Swimming: {state.is_swimming}")
                print(f"Strokes: {state.stroke_count}")
                print(f"Rate: {state.stroke_rate}")

            elif cmd == "checklist":
                print(VERIFICATION_CHECKLIST)

            elif cmd == "help":
                print(INTERACTIVE_HELP)

            elif cmd in ("quit", "exit", "q"):
                self._running = False

            else:
                print(f"Unknown command: {cmd}. Type 'help' for commands.")

        except Exception as e:
            print(f"Error: {e}")

    def print_checklist(self) -> None:
        """Print verification checklist."""
        print(VERIFICATION_CHECKLIST)


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="E2E Testing Harness")
    parser.add_argument("--port", type=int, default=8765, help="WebSocket port")
    parser.add_argument("--dashboard-port", type=int, default=5173, help="Dashboard port")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser")
    parser.add_argument("--config-dir", type=Path, help="Config directory")
    args = parser.parse_args()

    config = HarnessConfig(
        websocket_port=args.port,
        dashboard_port=args.dashboard_port,
        open_browser=not args.no_browser,
        config_dir=args.config_dir or Path.home() / ".slipstream-test",
    )

    harness = E2EHarness(config)

    try:
        await harness.start()
        await harness.run_interactive()
    finally:
        await harness.stop()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Phase 4: Built-in Scenarios

**Goal**: Pre-defined test scenarios covering critical paths.

### Scenario Files

```yaml
# verification/scenarios/data/session_lifecycle.yaml
name: Session Lifecycle
description: Test basic session start/stop flow
tags: [core, session]

steps:
  - action: start_session
    description: Start a new session
    expect:
      session.active: true

  - action: set_swimming
    params:
      value: true
    description: Swimmer starts swimming

  - action: set_stroke_count
    params:
      count: 50
    description: Simulate 50 strokes

  - action: wait
    params:
      duration: 0.5
    description: Let state propagate

  - action: end_session
    description: End the session
    expect:
      session.active: false
```

```yaml
# verification/scenarios/data/stroke_queries.yaml
name: Stroke Queries
description: Test stroke rate and count queries
tags: [core, metrics]

steps:
  - action: start_session
    expect:
      session.active: true

  - action: set_swimming
    params:
      value: true

  - action: set_stroke_rate
    params:
      rate: 52.5

  - action: set_stroke_count
    params:
      count: 100

  - action: wait
    params:
      duration: 0.3

  - action: get_stroke_rate
    expect_result:
      stroke_rate: 52.5

  - action: end_session
```

```yaml
# verification/scenarios/data/workout_flow.yaml
name: Workout Flow
description: Test complete workout lifecycle
tags: [workout]

steps:
  - action: start_session
    expect:
      session.active: true

  - action: create_workout
    params:
      name: Test Intervals
      segments:
        - type: warmup
          target_duration_seconds: 30
        - type: work
          target_distance_m: 50
        - type: rest
          target_duration_seconds: 15
        - type: cooldown
          target_duration_seconds: 30
    expect_result:
      segments_count: 4

  - action: start_workout
    expect:
      workout.has_active_workout: true
      workout.phase: active

  - action: skip_segment
    description: Skip warmup

  - action: wait
    params:
      duration: 0.3
    expect:
      workout.current_segment.type: work

  - action: skip_segment
    description: Skip work segment

  - action: skip_segment
    description: Skip rest segment

  - action: skip_segment
    description: Skip cooldown - should complete workout
    expect:
      workout.has_active_workout: false

  - action: end_session
```

```yaml
# verification/scenarios/data/websocket_updates.yaml
name: WebSocket State Updates
description: Verify WebSocket broadcasts state changes
tags: [core, websocket]

steps:
  - action: wait
    params:
      duration: 0.3
    description: Wait for initial state
    expect:
      session.active: false
      system.is_swimming: false

  - action: set_swimming
    params:
      value: true

  - action: wait
    params:
      duration: 0.5
    expect:
      system.is_swimming: true

  - action: set_stroke_rate
    params:
      rate: 48.0

  - action: set_stroke_count
    params:
      count: 25

  - action: start_session

  - action: wait
    params:
      duration: 0.5
    expect:
      session.active: true
      session.stroke_rate: 48.0
```

---

## File Structure After TDD

```
verification/
├── __init__.py
├── __main__.py                    # Entry point for verification suite
├── e2e_harness.py                 # Interactive E2E testing harness
├── mocks/
│   ├── __init__.py
│   ├── vision.py                  # MockVisionStateStore
│   └── transcript.py              # MockTranscriptStream, Utterance
├── scenarios/
│   ├── __init__.py
│   ├── models.py                  # Scenario, Step, StepResult
│   ├── runner.py                  # ScenarioRunner
│   └── data/
│       ├── session_lifecycle.yaml
│       ├── stroke_queries.yaml
│       ├── workout_flow.yaml
│       └── websocket_updates.yaml
└── cli.py                         # CLI for running scenarios

tests/verification/
├── __init__.py
├── conftest.py                    # Shared fixtures
├── test_mocks.py                  # Mock infrastructure tests
├── test_integration.py            # Server integration tests
├── test_scenarios.py              # Scenario runner tests
└── test_e2e_harness.py            # E2E harness tests
```

---

## Implementation Order (TDD Red-Green-Refactor)

| Order | Phase | Tests | Implementation |
|-------|-------|-------|----------------|
| 1 | Mock Vision | `test_mocks.py` (1-8) | `mocks/vision.py` |
| 2 | Mock Transcript | `test_mocks.py` (9-18) | `mocks/transcript.py` |
| 3 | Server Integration | `test_integration.py` (1-8) | Uses existing server |
| 4 | Workout Integration | `test_integration.py` (9-11) | Uses existing server |
| 5 | Scenario Models | `test_scenarios.py` (12-17) | `scenarios/models.py` |
| 6 | Scenario Runner | `test_scenarios.py` | `scenarios/runner.py` |
| 7 | Built-in Scenarios | `test_scenarios.py` (18-20) | `scenarios/data/*.yaml` |
| 8 | E2E Harness | `test_e2e_harness.py` | `e2e_harness.py` |

---

## Test Execution

```bash
# Phase 1-2: Mocks
uv run pytest tests/verification/test_mocks.py -v

# Phase 3-4: Integration
uv run pytest tests/verification/test_integration.py -v

# Phase 5-7: Scenarios
uv run pytest tests/verification/test_scenarios.py -v

# Phase 8: E2E Harness
uv run pytest tests/verification/test_e2e_harness.py -v

# All verification tests
uv run pytest tests/verification/ -v

# Run scenario suite (after implementation)
uv run python -m verification --scenarios all

# Run E2E harness for manual testing
uv run python -m verification.e2e_harness
```

---

## Success Criteria

### Automated Tests
- [ ] All mock tests pass (18 tests)
- [ ] All integration tests pass (11 tests)
- [ ] All scenario tests pass (9 tests)
- [ ] All E2E harness tests pass (5 tests)
- [ ] Built-in scenarios execute successfully
- [ ] >90% code coverage on verification module

### Manual Verification (E2E Harness)
- [ ] Dashboard displays stroke rate readable from 10ft
- [ ] Dashboard updates in real-time (<500ms latency)
- [ ] Session start/stop reflects on dashboard
- [ ] Workout segment info displays correctly
- [ ] Swimming indicator responds to mock state changes

### Integration Confidence
- [ ] WebSocket state propagation verified
- [ ] MCP tools return expected data
- [ ] Mock vision state flows through entire pipeline
- [ ] Multiple WebSocket clients receive updates

---

## CLI Usage (After Implementation)

```bash
# Run all automated scenarios
uv run python -m verification --scenarios all

# Run specific scenario
uv run python -m verification --scenario session_lifecycle

# Run scenarios by tag
uv run python -m verification --tag core

# Start E2E harness for manual testing
uv run python -m verification --e2e

# Start E2E harness without opening browser
uv run python -m verification --e2e --no-browser

# Run with verbose output
uv run python -m verification --scenarios all -v
```

---

## Notes

1. **Vision Always Mocked**: Real CV requires camera hardware. The `MockVisionStateStore` is injectable via `SwimCoachServer.__init__`, so no code changes needed.

2. **Transcript Mocking Optional**: The `MockTranscriptStream` is for fully automated tests. For semi-manual testing, you can use real STT or just call MCP tools directly.

3. **WebSocket as Verification Point**: If the WebSocket state is correct, the dashboard will render correctly. This lets us automate most verification without needing visual assertions.

4. **Scenario-Based Testing**: YAML scenarios are easy to write and understand. They document expected behavior while also serving as tests.

5. **E2E Harness for Final Verification**: The interactive harness lets you manually control mock state while watching the dashboard. This catches visual/UX issues that automated tests miss.

6. **No Agent Mocking**: We don't mock the Claude agent. Automated tests call MCP tools directly. The agent's behavior is verified via the E2E harness with real or simulated voice.
