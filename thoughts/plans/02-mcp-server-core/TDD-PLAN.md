# MCP Server Core - TDD Implementation Plan

## Overview

Test-Driven Development plan for Branch 2: MCP Server Core. FastMCP server with session management and WebSocket dashboard updates.

---

## Phase 1: Models & Config

**Goal**: Data structures and user configuration management.

### Tests First (`tests/mcp/test_models.py`)

```python
# Test 1: StateUpdate message serialization
def test_state_update_to_json():
    # Given StateUpdate with session and system data
    # When to_json() called
    # Then returns valid JSON with ISO timestamp

# Test 2: StateUpdate from dict
def test_state_update_from_dict():
    # Given dict with state data
    # When StateUpdate.from_dict() called
    # Then object created correctly

# Test 3: SessionState defaults
def test_session_state_defaults():
    # Given new SessionState()
    # Then active=False, stroke_count=0, etc.

# Test 4: SystemState defaults
def test_system_state_defaults():
    # Given new SystemState()
    # Then is_swimming=False, pose_detected=False, voice_state="idle"
```

### Tests First (`tests/mcp/test_config.py`)

```python
# Test 1: Load config from file
def test_load_config():
    # Given config.json exists with valid data
    # When Config.load() called
    # Then config object populated correctly

# Test 2: Load creates default if missing
def test_load_creates_default():
    # Given no config.json exists
    # When Config.load() called
    # Then default config created and saved

# Test 3: Save config
def test_save_config():
    # Given Config object with changes
    # When config.save() called
    # Then file updated with new values

# Test 4: Get/set DPS ratio
def test_dps_ratio():
    # Given config with dps_ratio=1.8
    # When config.dps_ratio accessed
    # Then returns 1.8

# Test 5: Notification settings
def test_notification_settings():
    # Given config with telegram_enabled=True
    # When config.notifications accessed
    # Then returns correct notification config
```

### Implementation

```python
# src/mcp/models/messages.py
@dataclass
class SessionState:
    active: bool = False
    elapsed_seconds: int = 0
    stroke_count: int = 0
    stroke_rate: float = 0.0
    stroke_rate_trend: str = "stable"  # "increasing" | "stable" | "decreasing"
    estimated_distance_m: float = 0.0

@dataclass
class SystemState:
    is_swimming: bool = False
    pose_detected: bool = False
    voice_state: str = "idle"  # "idle" | "listening" | "speaking"

@dataclass
class StateUpdate:
    type: str = "state_update"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    session: SessionState = field(default_factory=SessionState)
    system: SystemState = field(default_factory=SystemState)

    def to_json(self) -> str
    @classmethod
    def from_dict(cls, data: dict) -> "StateUpdate"

# src/mcp/storage/config.py
@dataclass
class NotificationConfig:
    telegram_enabled: bool = False
    telegram_chat_id: str | None = None
    sms_enabled: bool = False
    sms_phone: str | None = None

@dataclass
class Config:
    dps_ratio: float = 1.8
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    config_path: Path = Path.home() / ".slipstream" / "config.json"

    @classmethod
    def load(cls, path: Path | None = None) -> "Config"
    def save(self) -> None
```

---

## Phase 2: Session Storage

**Goal**: Session file I/O to `~/.slipstream/sessions/`.

### Tests First (`tests/mcp/test_session_storage.py`)

```python
# Test 1: Create new session file
def test_create_session():
    # Given session_id and start time
    # When create_session() called
    # Then JSON file created with correct structure

# Test 2: Get session by ID
def test_get_session():
    # Given existing session file
    # When get_session(session_id) called
    # Then returns session data dict

# Test 3: Update session
def test_update_session():
    # Given existing session
    # When update_session(session_id, updates) called
    # Then file updated with new data

# Test 4: List sessions
def test_list_sessions():
    # Given multiple session files
    # When list_sessions() called
    # Then returns list sorted by date (newest first)

# Test 5: Session not found
def test_session_not_found():
    # Given no session with ID "nonexistent"
    # When get_session("nonexistent") called
    # Then returns None

# Test 6: Creates sessions directory
def test_creates_sessions_dir():
    # Given ~/.slipstream/sessions/ doesn't exist
    # When create_session() called
    # Then directory created

# Test 7: Session filename format
def test_session_filename():
    # Given session started at 2026-01-14 08:30
    # When create_session() called
    # Then file named "2026-01-14_0830.json"

# Test 8: Delete session
def test_delete_session():
    # Given existing session file
    # When delete_session(session_id) called
    # Then file removed
```

### Implementation

```python
# src/mcp/storage/session_storage.py
@dataclass
class SessionStorage:
    sessions_dir: Path = Path.home() / ".slipstream" / "sessions"

    def create_session(self, session_id: str, started_at: datetime) -> dict
    def get_session(self, session_id: str) -> dict | None
    def update_session(self, session_id: str, updates: dict) -> None
    def list_sessions(self, limit: int = 10) -> list[dict]
    def delete_session(self, session_id: str) -> bool
    def _session_path(self, session_id: str) -> Path
```

---

## Phase 3: State Store

**Goal**: In-memory state management with thread safety.

### Tests First (`tests/mcp/test_state_store.py`)

```python
# Test 1: Initial state
def test_initial_state():
    # Given new StateStore()
    # Then session.active=False, system.is_swimming=False

# Test 2: Start session
def test_start_session():
    # Given inactive state
    # When start_session() called
    # Then session.active=True, session_id generated

# Test 3: End session
def test_end_session():
    # Given active session
    # When end_session() called
    # Then session.active=False, returns summary

# Test 4: Update stroke metrics
def test_update_stroke_metrics():
    # Given active session
    # When update_strokes(count=10, rate=52.5) called
    # Then session.stroke_count=10, stroke_rate=52.5

# Test 5: Update system state
def test_update_system_state():
    # Given state store
    # When update_system(is_swimming=True, pose_detected=True) called
    # Then system state updated

# Test 6: Get current state update
def test_get_state_update():
    # Given state store with data
    # When get_state_update() called
    # Then returns StateUpdate object

# Test 7: Calculate stroke rate trend
def test_stroke_rate_trend():
    # Given history of stroke rates [50, 52, 54, 56]
    # When trend calculated
    # Then returns "increasing"

# Test 8: Elapsed time calculation
def test_elapsed_time():
    # Given session started 2 minutes ago
    # When get_state_update() called
    # Then elapsed_seconds=120

# Test 9: Thread-safe updates
def test_thread_safety():
    # Given multiple threads updating state
    # When concurrent updates occur
    # Then no race conditions (use threading test)

# Test 10: Session already active error
def test_start_session_when_active():
    # Given active session
    # When start_session() called again
    # Then raises SessionActiveError
```

### Implementation

```python
# src/mcp/state_store.py
class SessionActiveError(Exception):
    pass

class NoActiveSessionError(Exception):
    pass

@dataclass
class StateStore:
    session: SessionState = field(default_factory=SessionState)
    system: SystemState = field(default_factory=SystemState)
    _session_id: str | None = None
    _started_at: datetime | None = None
    _stroke_rate_history: list[float] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def start_session(self) -> str  # Returns session_id
    def end_session(self) -> dict   # Returns summary
    def update_strokes(self, count: int, rate: float) -> None
    def update_system(self, **kwargs) -> None
    def get_state_update(self) -> StateUpdate
    def _calculate_trend(self) -> str
```

---

## Phase 4: WebSocket Server

**Goal**: Push state to dashboard at 500ms intervals.

### Tests First (`tests/mcp/test_websocket_server.py`)

```python
# Test 1: Server starts on port
def test_server_starts():
    # Given WebSocketServer(port=8765)
    # When start() called
    # Then server listening on port 8765

# Test 2: Client connects
def test_client_connects():
    # Given running server
    # When client connects
    # Then connection accepted

# Test 3: Client receives state updates
def test_client_receives_updates(mock_state_store):
    # Given connected client and state store with data
    # When 500ms passes
    # Then client receives StateUpdate JSON

# Test 4: Multiple clients
def test_multiple_clients():
    # Given 3 connected clients
    # When state update pushed
    # Then all 3 clients receive it

# Test 5: Client disconnects gracefully
def test_client_disconnect():
    # Given connected client
    # When client disconnects
    # Then no errors, other clients unaffected

# Test 6: Server shutdown
def test_server_shutdown():
    # Given running server with clients
    # When stop() called
    # Then all connections closed, port freed

# Test 7: Push interval timing
def test_push_interval():
    # Given server with 500ms interval
    # When running for 2 seconds
    # Then ~4 updates sent

# Test 8: Broadcast specific message
def test_broadcast_message():
    # Given connected clients
    # When broadcast({"custom": "msg"}) called
    # Then all clients receive custom message
```

### Implementation

```python
# src/mcp/websocket_server.py
class WebSocketServer:
    def __init__(
        self,
        state_store: StateStore,
        port: int = 8765,
        push_interval: float = 0.5,
    ):
        self.state_store = state_store
        self.port = port
        self.push_interval = push_interval
        self._clients: set[websockets.WebSocketServerProtocol] = set()
        self._server: websockets.WebSocketServer | None = None
        self._push_task: asyncio.Task | None = None

    async def start(self) -> None
    async def stop(self) -> None
    async def broadcast(self, message: dict) -> None
    async def _handle_client(self, websocket: websockets.WebSocketServerProtocol) -> None
    async def _push_loop(self) -> None
```

---

## Phase 5: Session Tools

**Goal**: MCP tools for session management.

### Tests First (`tests/mcp/test_session_tools.py`)

```python
# Test 1: start_session tool
def test_start_session_tool():
    # Given no active session
    # When start_session() called
    # Then returns {"session_id": "...", "started_at": "..."}

# Test 2: start_session when already active
def test_start_session_already_active():
    # Given active session
    # When start_session() called
    # Then returns error response

# Test 3: end_session tool
def test_end_session_tool():
    # Given active session with strokes
    # When end_session() called
    # Then returns summary with stroke_count, duration, etc.

# Test 4: end_session when not active
def test_end_session_not_active():
    # Given no active session
    # When end_session() called
    # Then returns error response

# Test 5: get_status tool
def test_get_status_tool():
    # Given active session
    # When get_status() called
    # Then returns full status dict

# Test 6: get_status when idle
def test_get_status_idle():
    # Given no active session
    # When get_status() called
    # Then returns status with session_active=False

# Test 7: Session persisted to storage
def test_session_persisted():
    # Given start_session, then end_session
    # When checking storage
    # Then session file exists with correct data
```

### Implementation

```python
# src/mcp/tools/session_tools.py
def create_session_tools(
    state_store: StateStore,
    session_storage: SessionStorage,
) -> list[Callable]:
    """Create session management tools for MCP registration."""

    def start_session() -> dict:
        """Begin a new swim session."""
        ...

    def end_session() -> dict:
        """End current session and save data."""
        ...

    def get_status() -> dict:
        """Get current system status."""
        ...

    return [start_session, end_session, get_status]
```

---

## Phase 6: MCP Server

**Goal**: FastMCP server with stdio transport.

### Tests First (`tests/mcp/test_server.py`)

```python
# Test 1: Server creates correctly
def test_server_creation():
    # Given SwimCoachServer()
    # When created
    # Then server has name "swim-coach"

# Test 2: Tools registered
def test_tools_registered():
    # Given server instance
    # When checking registered tools
    # Then start_session, end_session, get_status present

# Test 3: Tool call works
def test_tool_call():
    # Given running server
    # When MCP tool call for get_status
    # Then returns valid response

# Test 4: Server lifecycle
def test_server_lifecycle():
    # Given server
    # When start() then stop() called
    # Then clean shutdown, no errors

# Test 5: WebSocket server integration
def test_websocket_integration():
    # Given server started
    # Then WebSocket server also running

# Test 6: Error handling
def test_error_handling():
    # Given invalid tool call
    # When processed
    # Then error returned, server continues
```

### Implementation

```python
# src/mcp/server.py
class SwimCoachServer:
    def __init__(
        self,
        websocket_port: int = 8765,
        push_interval: float = 0.5,
    ):
        self.mcp = FastMCP("swim-coach")
        self.state_store = StateStore()
        self.session_storage = SessionStorage()
        self.websocket_server = WebSocketServer(
            self.state_store,
            port=websocket_port,
            push_interval=push_interval,
        )
        self._register_tools()

    def _register_tools(self) -> None
    async def start(self) -> None
    async def stop(self) -> None
    def run(self) -> None  # Main entry point

# Entry point
if __name__ == "__main__":
    server = SwimCoachServer()
    server.run()
```

---

## Phase 7: Integration Tests

**Goal**: End-to-end testing with real MCP protocol.

### Tests First (`tests/mcp/test_integration.py`)

```python
# Test 1: Full session lifecycle
async def test_full_session_lifecycle():
    # Given running server
    # When start_session → simulate strokes → end_session
    # Then session saved with correct data

# Test 2: WebSocket receives session updates
async def test_websocket_session_updates():
    # Given running server and connected WebSocket client
    # When start_session called
    # Then client receives state update with active=True

# Test 3: Multiple tool calls
async def test_multiple_tool_calls():
    # Given running server
    # When multiple rapid tool calls
    # Then all handled correctly

# Test 4: Persistence across restarts
async def test_persistence():
    # Given completed session
    # When server restarts
    # Then session still in storage

# Test 5: Config changes persist
async def test_config_persistence():
    # Given config change
    # When server restarts
    # Then config loaded correctly
```

---

## Test Fixtures

```python
# tests/mcp/conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def temp_slipstream_dir(tmp_path):
    """Temporary ~/.slipstream directory."""
    slipstream_dir = tmp_path / ".slipstream"
    slipstream_dir.mkdir()
    (slipstream_dir / "sessions").mkdir()
    return slipstream_dir

@pytest.fixture
def config(temp_slipstream_dir):
    """Config with temp directory."""
    return Config(config_path=temp_slipstream_dir / "config.json")

@pytest.fixture
def session_storage(temp_slipstream_dir):
    """SessionStorage with temp directory."""
    return SessionStorage(sessions_dir=temp_slipstream_dir / "sessions")

@pytest.fixture
def state_store():
    """Fresh StateStore instance."""
    return StateStore()

@pytest.fixture
async def websocket_server(state_store):
    """Running WebSocket server for tests."""
    server = WebSocketServer(state_store, port=0)  # Random port
    await server.start()
    yield server
    await server.stop()

@pytest.fixture
def mock_fastmcp(mocker):
    """Mock FastMCP for isolated testing."""
    return mocker.patch("mcp.FastMCP")
```

---

## Implementation Order

| Order | Component | Tests | Implementation |
|-------|-----------|-------|----------------|
| 1 | Models | `test_models.py` | `models/messages.py` |
| 2 | Config | `test_config.py` | `storage/config.py` |
| 3 | Session Storage | `test_session_storage.py` | `storage/session_storage.py` |
| 4 | State Store | `test_state_store.py` | `state_store.py` |
| 5 | WebSocket Server | `test_websocket_server.py` | `websocket_server.py` |
| 6 | Session Tools | `test_session_tools.py` | `tools/session_tools.py` |
| 7 | MCP Server | `test_server.py` | `server.py` |
| 8 | Integration | `test_integration.py` | - |

---

## Dependencies to Add

```bash
uv add mcp websockets
uv add --dev pytest-asyncio
```

---

## Success Metrics

- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] >90% code coverage on `src/mcp/`
- [ ] MCP server responds to tool calls <100ms
- [ ] WebSocket pushes state at 500ms intervals
- [ ] Session files saved correctly as JSON
- [ ] Config file loads and saves preferences
