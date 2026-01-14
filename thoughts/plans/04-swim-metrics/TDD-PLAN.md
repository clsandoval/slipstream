# Swim Metrics - TDD Implementation Plan

## Overview

Test-Driven Development plan for Branch 4: Swim Metrics. MCP tools that expose real-time swim metrics to Claude, bridging the vision pipeline to the MCP server.

**Dependencies**: Branch 1 (vision-pipeline) + Branch 2 (mcp-server-core)
**Complexity**: Low

---

## Architecture

The swim-metrics branch creates a bridge between the vision pipeline's state and MCP tools that Claude can call.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SWIM METRICS ARCHITECTURE                            │
│                                                                              │
│  Vision Pipeline                    MCP Server                               │
│  ┌──────────────────┐              ┌──────────────────────────────────────┐ │
│  │ src/vision/      │              │ src/mcp/                             │ │
│  │ state_store.py   │──────────────│ tools/swim_tools.py                  │ │
│  │   └─ SwimState   │  reads from  │   ├─ get_stroke_rate()               │ │
│  │      stroke_count │              │   ├─ get_stroke_count()              │ │
│  │      stroke_rate  │              │   └─ get_session_time()              │ │
│  │      rate_history │              │                                      │ │
│  │      is_swimming  │              │ tools/metric_bridge.py               │ │
│  │      session_*    │              │   └─ MetricBridge (adapter)          │ │
│  └──────────────────┘              └──────────────────────────────────────┘ │
│           │                                       │                          │
│           │                                       │                          │
│           ▼                                       ▼                          │
│  Rate history list                       Config.dps_ratio                    │
│  [RateSample(t, rate)]                   for distance calculation            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **MetricBridge as Adapter**: Rather than having tools directly access vision state, we use a MetricBridge class that encapsulates the coupling. This allows:
   - Easy mocking for tool tests
   - Single point of integration between vision and MCP
   - Future flexibility if vision state changes

2. **Trend Calculation**: MCP state_store already calculates trends from rate history. Swim tools will use the existing `StateStore.get_state_update()` which includes `stroke_rate_trend`.

3. **No Duplicate State**: Tools read from vision state and MCP state - they don't maintain their own copy.

---

## Phase 1: Metric Bridge

**Goal**: Adapter connecting vision pipeline state to MCP tools.

### Tests First (`tests/mcp/test_metric_bridge.py`)

```python
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
from src.vision.state_store import SwimState, StateStore as VisionStateStore
from src.vision.rate_calculator import RateSample
from src.mcp.storage.config import Config


class TestMetricBridge:
    """Test MetricBridge adapter between vision and MCP."""

    # Test 1: Get stroke rate from vision state
    def test_get_stroke_rate_returns_current_rate(self):
        # Given vision state with stroke_rate=54.5
        # When get_stroke_rate() called
        # Then returns rate=54.5

    # Test 2: Get stroke rate trend
    def test_get_stroke_rate_includes_trend(self):
        # Given rate_history showing increasing pattern [50, 52, 54, 56]
        # When get_stroke_rate() called
        # Then returns trend="increasing"

    # Test 3: Get stroke rate when not swimming
    def test_get_stroke_rate_not_swimming(self):
        # Given is_swimming=False, no active session
        # When get_stroke_rate() called
        # Then returns rate=0, trend="stable"

    # Test 4: Get stroke count
    def test_get_stroke_count_returns_total(self):
        # Given vision state with stroke_count=142
        # When get_stroke_count() called
        # Then returns count=142

    # Test 5: Get stroke count with distance estimation
    def test_get_stroke_count_includes_distance(self):
        # Given stroke_count=100 and config.dps_ratio=1.5
        # When get_stroke_count() called
        # Then returns estimated_distance_m=150.0

    # Test 6: Distance uses config DPS ratio
    def test_distance_uses_config_dps_ratio(self):
        # Given config.dps_ratio=2.0, stroke_count=50
        # When get_stroke_count() called
        # Then returns estimated_distance_m=100.0

    # Test 7: Get session time with active session
    def test_get_session_time_active(self):
        # Given session started 5 minutes ago
        # When get_session_time() called
        # Then returns elapsed_seconds=300, formatted="5:00"

    # Test 8: Get session time formats correctly
    @pytest.mark.parametrize("seconds,expected", [
        (0, "0:00"),
        (59, "0:59"),
        (60, "1:00"),
        (125, "2:05"),
        (3661, "61:01"),  # Over an hour
    ])
    def test_get_session_time_formatting(self, seconds, expected):
        # Given session elapsed for `seconds`
        # When get_session_time() called
        # Then formatted matches expected

    # Test 9: Get session time when no session
    def test_get_session_time_no_session(self):
        # Given no active session
        # When get_session_time() called
        # Then returns elapsed_seconds=0, formatted="0:00"

    # Test 10: Bridge handles missing vision state gracefully
    def test_handles_no_vision_state(self):
        # Given vision state_store returns default SwimState
        # When bridge methods called
        # Then returns safe defaults, no errors

    # Test 11: Rate window seconds from config
    def test_get_stroke_rate_includes_window(self):
        # Given rate_calculator with 15s window
        # When get_stroke_rate() called
        # Then returns window_seconds=15

    # Test 12: Get all metrics at once
    def test_get_all_metrics(self):
        # Given active session with data
        # When get_all_metrics() called
        # Then returns combined dict with rate, count, time
```

### Implementation

```python
# src/mcp/tools/metric_bridge.py
from dataclasses import dataclass
from datetime import datetime
from src.vision.state_store import StateStore as VisionStateStore
from src.mcp.storage.config import Config


@dataclass
class MetricBridge:
    """
    Adapter connecting vision pipeline state to MCP tools.

    Encapsulates the coupling between vision and MCP modules,
    providing a clean interface for swim metric tools.
    """
    vision_state_store: VisionStateStore
    config: Config
    rate_window_seconds: float = 15.0

    def get_stroke_rate(self) -> dict:
        """
        Get current stroke rate and trend.

        Returns:
            {
                "rate": float,           # strokes per minute
                "trend": str,            # "increasing" | "stable" | "decreasing"
                "window_seconds": float  # rate calculation window
            }
        """
        state = self.vision_state_store.get_state()
        trend = self._calculate_trend(state.rate_history)

        return {
            "rate": round(state.stroke_rate, 1),
            "trend": trend,
            "window_seconds": self.rate_window_seconds,
        }

    def get_stroke_count(self) -> dict:
        """
        Get total strokes and estimated distance.

        Returns:
            {
                "count": int,               # total strokes in session
                "estimated_distance_m": float  # count * dps_ratio
            }
        """
        state = self.vision_state_store.get_state()
        distance = state.stroke_count * self.config.dps_ratio

        return {
            "count": state.stroke_count,
            "estimated_distance_m": round(distance, 1),
        }

    def get_session_time(self) -> dict:
        """
        Get elapsed session time.

        Returns:
            {
                "elapsed_seconds": int,
                "formatted": str  # "MM:SS" format
            }
        """
        state = self.vision_state_store.get_state()

        if not state.session_active or state.session_start is None:
            return {"elapsed_seconds": 0, "formatted": "0:00"}

        elapsed = (datetime.now() - state.session_start).total_seconds()
        elapsed_int = int(elapsed)

        minutes = elapsed_int // 60
        seconds = elapsed_int % 60
        formatted = f"{minutes}:{seconds:02d}"

        return {
            "elapsed_seconds": elapsed_int,
            "formatted": formatted,
        }

    def get_all_metrics(self) -> dict:
        """Get all metrics in a single call."""
        return {
            "stroke_rate": self.get_stroke_rate(),
            "stroke_count": self.get_stroke_count(),
            "session_time": self.get_session_time(),
        }

    def _calculate_trend(self, rate_history: list) -> str:
        """
        Calculate trend from rate history.

        Uses last 4 samples to determine direction.
        Threshold of ±2.0 strokes/min for trend detection.
        """
        if len(rate_history) < 2:
            return "stable"

        # Take last 4 samples (or all if fewer)
        recent = rate_history[-4:]
        rates = [sample.rate for sample in recent]

        # Simple linear trend: compare first and last
        diff = rates[-1] - rates[0]

        if diff > 2.0:
            return "increasing"
        elif diff < -2.0:
            return "decreasing"
        else:
            return "stable"
```

---

## Phase 2: Swim Metric Tools

**Goal**: MCP tools using the MetricBridge.

### Tests First (`tests/mcp/test_swim_tools.py`)

```python
import pytest
from unittest.mock import Mock, MagicMock


class TestSwimTools:
    """Test MCP swim metric tools."""

    @pytest.fixture
    def mock_bridge(self):
        """Mock MetricBridge for tool tests."""
        bridge = Mock()
        bridge.get_stroke_rate.return_value = {
            "rate": 54.0,
            "trend": "stable",
            "window_seconds": 15.0,
        }
        bridge.get_stroke_count.return_value = {
            "count": 142,
            "estimated_distance_m": 255.6,
        }
        bridge.get_session_time.return_value = {
            "elapsed_seconds": 300,
            "formatted": "5:00",
        }
        return bridge

    # Test 1: get_stroke_rate tool returns bridge data
    def test_get_stroke_rate_tool(self, mock_bridge):
        # Given swim tools created with mock bridge
        # When get_stroke_rate() tool called
        # Then returns bridge.get_stroke_rate() result

    # Test 2: get_stroke_count tool returns bridge data
    def test_get_stroke_count_tool(self, mock_bridge):
        # Given swim tools created with mock bridge
        # When get_stroke_count() tool called
        # Then returns bridge.get_stroke_count() result

    # Test 3: get_session_time tool returns bridge data
    def test_get_session_time_tool(self, mock_bridge):
        # Given swim tools created with mock bridge
        # When get_session_time() tool called
        # Then returns bridge.get_session_time() result

    # Test 4: Tools have correct descriptions
    def test_tool_descriptions(self, mock_bridge):
        # Given swim tools
        # When inspecting tool functions
        # Then each has descriptive docstring for Claude

    # Test 5: Tools respond within latency budget
    def test_tool_latency(self, mock_bridge):
        # Given swim tools
        # When calling get_stroke_rate() 100 times
        # Then average latency < 100ms

    # Test 6: Tools handle bridge errors gracefully
    def test_tool_handles_bridge_error(self, mock_bridge):
        # Given bridge.get_stroke_rate raises exception
        # When get_stroke_rate() tool called
        # Then returns error dict, doesn't crash

    # Test 7: create_swim_tools factory
    def test_create_swim_tools_factory(self, mock_bridge):
        # Given MetricBridge instance
        # When create_swim_tools(bridge) called
        # Then returns list of 3 tool functions


class TestSwimToolsIntegration:
    """Integration tests with real MetricBridge."""

    @pytest.fixture
    def integration_setup(self, temp_slipstream_dir):
        """Real components for integration tests."""
        from src.vision.state_store import StateStore as VisionStateStore
        from src.mcp.storage.config import Config
        from src.mcp.tools.metric_bridge import MetricBridge

        vision_store = VisionStateStore()
        config = Config(config_path=temp_slipstream_dir / "config.json")
        bridge = MetricBridge(vision_store, config)

        return vision_store, config, bridge

    # Test 8: Full integration - stroke rate
    def test_integration_stroke_rate(self, integration_setup):
        # Given vision state with stroke data
        # When get_stroke_rate() called through tools
        # Then returns correct rate from vision pipeline

    # Test 9: Full integration - stroke count with distance
    def test_integration_stroke_count(self, integration_setup):
        # Given vision state with 100 strokes, config dps=1.8
        # When get_stroke_count() called
        # Then returns count=100, distance=180.0

    # Test 10: Full integration - session time
    def test_integration_session_time(self, integration_setup):
        # Given active session started 2 minutes ago
        # When get_session_time() called
        # Then returns elapsed_seconds≈120
```

### Implementation

```python
# src/mcp/tools/swim_tools.py
from typing import Callable
from src.mcp.tools.metric_bridge import MetricBridge


def create_swim_tools(bridge: MetricBridge) -> list[Callable]:
    """
    Create swim metric tools for MCP registration.

    Args:
        bridge: MetricBridge adapter connecting to vision pipeline

    Returns:
        List of tool functions to register with FastMCP
    """

    def get_stroke_rate() -> dict:
        """
        Get current stroke rate and trend.

        Returns the swimmer's current stroke rate (strokes per minute),
        the trend direction, and the time window used for calculation.

        Returns:
            rate: Current strokes per minute
            trend: "increasing", "stable", or "decreasing"
            window_seconds: Time window for rate calculation (typically 15s)
        """
        try:
            return bridge.get_stroke_rate()
        except Exception as e:
            return {"error": str(e)}

    def get_stroke_count() -> dict:
        """
        Get total strokes and estimated distance.

        Returns the total stroke count for the current session
        and an estimated distance based on the user's DPS ratio
        (distance per stroke) setting.

        Returns:
            count: Total strokes in current session
            estimated_distance_m: Estimated distance swum in meters
        """
        try:
            return bridge.get_stroke_count()
        except Exception as e:
            return {"error": str(e)}

    def get_session_time() -> dict:
        """
        Get elapsed session time.

        Returns the total time elapsed since the session started,
        both as raw seconds and as a formatted string.

        Returns:
            elapsed_seconds: Total seconds since session start
            formatted: Human-readable time (e.g., "20:34")
        """
        try:
            return bridge.get_session_time()
        except Exception as e:
            return {"error": str(e)}

    return [get_stroke_rate, get_stroke_count, get_session_time]
```

---

## Phase 3: Server Integration

**Goal**: Register swim tools with MCP server.

### Tests First (`tests/mcp/test_swim_tools_integration.py`)

```python
import pytest


class TestSwimToolsServerIntegration:
    """Test swim tools registration with MCP server."""

    # Test 1: Tools registered on server
    def test_tools_registered(self, server_with_swim_tools):
        # Given SwimCoachServer with swim tools
        # When listing registered tools
        # Then get_stroke_rate, get_stroke_count, get_session_time present

    # Test 2: Tool call through MCP protocol
    async def test_mcp_tool_call_stroke_rate(self, server_with_swim_tools):
        # Given running server
        # When MCP call to get_stroke_rate
        # Then returns valid response

    # Test 3: WebSocket state includes swim metrics
    async def test_websocket_includes_metrics(self, server_with_swim_tools):
        # Given connected WebSocket client
        # When state update received
        # Then includes stroke_rate, stroke_count from vision

    # Test 4: Swim tools work alongside session tools
    async def test_swim_and_session_tools_together(self, server_with_swim_tools):
        # Given running server
        # When calling start_session then get_stroke_rate
        # Then both work correctly

    # Test 5: Vision state updates propagate to swim tools
    async def test_vision_state_propagation(self, server_with_swim_tools):
        # Given vision state_store updated with new stroke count
        # When get_stroke_count called
        # Then returns updated count
```

### Implementation Updates

```python
# src/mcp/server.py (updates)
from src.vision.state_store import StateStore as VisionStateStore
from src.mcp.tools.metric_bridge import MetricBridge
from src.mcp.tools.swim_tools import create_swim_tools


class SwimCoachServer:
    def __init__(
        self,
        websocket_port: int = 8765,
        push_interval: float = 0.25,
        vision_state_store: VisionStateStore | None = None,
    ):
        self.mcp = FastMCP("swim-coach")
        self.config = Config.load()
        self.state_store = StateStore()
        self.session_storage = SessionStorage()

        # Vision integration
        self.vision_state_store = vision_state_store or VisionStateStore()
        self.metric_bridge = MetricBridge(
            vision_state_store=self.vision_state_store,
            config=self.config,
        )

        self.websocket_server = WebSocketServer(
            self.state_store,
            port=websocket_port,
            push_interval=push_interval,
        )
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all MCP tools."""
        # Session tools
        session_tools = create_session_tools(self.state_store, self.session_storage)
        for tool in session_tools:
            self.mcp.tool()(tool)

        # Swim metric tools
        swim_tools = create_swim_tools(self.metric_bridge)
        for tool in swim_tools:
            self.mcp.tool()(tool)
```

---

## Phase 4: Vision State Sync

**Goal**: Ensure MCP state stays synchronized with vision pipeline.

### Tests First (`tests/mcp/test_state_sync.py`)

```python
import pytest
import asyncio
from datetime import datetime


class TestVisionMCPStateSync:
    """Test synchronization between vision and MCP state."""

    # Test 1: Vision stroke count syncs to MCP
    async def test_stroke_count_sync(self, integrated_server):
        # Given vision pipeline detects 50 strokes
        # When vision state_store.update(stroke_count=50)
        # Then MCP state reflects 50 strokes

    # Test 2: Vision stroke rate syncs to MCP
    async def test_stroke_rate_sync(self, integrated_server):
        # Given vision pipeline calculates rate=52.5
        # When vision state updated
        # Then MCP get_stroke_rate returns 52.5

    # Test 3: WebSocket broadcasts include vision data
    async def test_websocket_vision_data(self, integrated_server, ws_client):
        # Given vision state updated with new metrics
        # When WebSocket push occurs
        # Then client receives updated metrics

    # Test 4: Session start/end syncs correctly
    async def test_session_lifecycle_sync(self, integrated_server):
        # Given start_session called via MCP
        # When vision state updated during session
        # Then all data synced
        # When end_session called
        # Then final state captured correctly

    # Test 5: Distance calculation uses current config
    async def test_distance_config_update(self, integrated_server):
        # Given stroke_count=100, config.dps_ratio=1.5
        # When get_stroke_count called
        # Then distance=150
        # When config.dps_ratio changed to 2.0
        # Then get_stroke_count returns distance=200

    # Test 6: Rate trend calculated correctly
    async def test_rate_trend_calculation(self, integrated_server):
        # Given rate_history=[50, 52, 54, 56, 58]
        # When get_stroke_rate called
        # Then trend="increasing"
```

### Implementation Notes

The sync happens automatically because `MetricBridge` reads directly from `VisionStateStore`. No explicit sync mechanism needed - tools always get current state.

For WebSocket broadcasts to include vision data, the `StateStore.get_state_update()` method needs to pull from vision state:

```python
# src/mcp/state_store.py (addition)
def sync_from_vision(self, vision_state: SwimState) -> None:
    """
    Sync MCP state from vision pipeline.

    Called by the server to keep states aligned.
    """
    with self._lock:
        self.session.stroke_count = vision_state.stroke_count
        self.session.stroke_rate = vision_state.stroke_rate
        # Calculate trend from vision rate_history
        if vision_state.rate_history:
            self._stroke_rate_history = [s.rate for s in vision_state.rate_history[-10:]]
```

---

## Test Fixtures

```python
# tests/mcp/conftest.py (additions)

@pytest.fixture
def mock_vision_state_store():
    """Mock VisionStateStore with controllable state."""
    from unittest.mock import Mock
    from src.vision.state_store import SwimState

    store = Mock()
    store.get_state.return_value = SwimState(
        session_active=True,
        session_start=datetime.now(),
        stroke_count=100,
        stroke_rate=54.0,
        rate_history=[],
        is_swimming=True,
        pose_detected=True,
    )
    return store


@pytest.fixture
def metric_bridge(mock_vision_state_store, config):
    """MetricBridge with mock vision state."""
    from src.mcp.tools.metric_bridge import MetricBridge
    return MetricBridge(mock_vision_state_store, config)


@pytest.fixture
def swim_tools(metric_bridge):
    """Swim tools for testing."""
    from src.mcp.tools.swim_tools import create_swim_tools
    return create_swim_tools(metric_bridge)


@pytest.fixture
async def server_with_swim_tools(temp_slipstream_dir, mock_vision_state_store):
    """SwimCoachServer with swim tools registered."""
    from src.mcp.server import SwimCoachServer

    server = SwimCoachServer(
        websocket_port=0,  # Random port
        vision_state_store=mock_vision_state_store,
    )
    await server.start()
    yield server
    await server.stop()
```

---

## File Structure After TDD

```
src/mcp/
├── __init__.py
├── server.py                 # Updated to include swim tools
├── state_store.py            # Updated with sync_from_vision
├── websocket_server.py
├── models/
│   ├── __init__.py
│   └── messages.py
├── storage/
│   ├── __init__.py
│   ├── session_storage.py
│   └── config.py
└── tools/
    ├── __init__.py
    ├── session_tools.py
    ├── swim_tools.py         # NEW: get_stroke_rate, etc.
    └── metric_bridge.py      # NEW: Vision → MCP adapter

tests/mcp/
├── __init__.py
├── conftest.py               # Updated with new fixtures
├── test_models.py
├── test_config.py
├── test_session_storage.py
├── test_state_store.py
├── test_websocket_server.py
├── test_session_tools.py
├── test_server.py
├── test_integration.py
├── test_metric_bridge.py     # NEW
├── test_swim_tools.py        # NEW
├── test_swim_tools_integration.py  # NEW
└── test_state_sync.py        # NEW
```

---

## Implementation Order (TDD Red-Green-Refactor)

| Order | Component | Tests | Implementation |
|-------|-----------|-------|----------------|
| 1 | MetricBridge | `test_metric_bridge.py` | `tools/metric_bridge.py` |
| 2 | Swim Tools | `test_swim_tools.py` | `tools/swim_tools.py` |
| 3 | Server Integration | `test_swim_tools_integration.py` | Update `server.py` |
| 4 | State Sync | `test_state_sync.py` | Update `state_store.py` |

---

## Test Execution

```bash
# Phase 1: Metric Bridge
uv run pytest tests/mcp/test_metric_bridge.py -v

# Phase 2: Swim Tools
uv run pytest tests/mcp/test_swim_tools.py -v

# Phase 3-4: Integration
uv run pytest tests/mcp/test_swim_tools_integration.py -v
uv run pytest tests/mcp/test_state_sync.py -v

# All swim metrics tests
uv run pytest tests/mcp/test_metric_bridge.py tests/mcp/test_swim_tools.py tests/mcp/test_swim_tools_integration.py tests/mcp/test_state_sync.py -v

# Full MCP test suite
uv run pytest tests/mcp/ -v
```

---

## Success Criteria

From the requirements:

- [x] `get_stroke_rate` returns data within 100ms
- [x] Distance estimation uses config DPS ratio
- [x] Tools return correct data from vision pipeline
- [x] Tools handle "no session active" gracefully

Additional criteria:

- [ ] All unit tests pass
- [ ] Integration tests pass with real components
- [ ] >90% code coverage on new files
- [ ] Tools work through MCP protocol
- [ ] WebSocket broadcasts include vision metrics
- [ ] State sync works correctly between vision and MCP

---

## Notes

1. **Trend calculation**: Uses last 4 rate samples with ±2.0 threshold. Simple but effective for coaching purposes.

2. **Error handling**: All tools wrap bridge calls in try/except and return error dict. Prevents crashes from propagating to Claude.

3. **Latency**: Since MetricBridge reads directly from in-memory state stores, latency should be <1ms. The 100ms budget is conservative.

4. **Testing without vision**: Mock fixtures allow full testing of swim tools without running the vision pipeline.

5. **DPS ratio**: Default 1.8 meters/stroke is typical for recreational freestyle. Users can customize in config.json.
