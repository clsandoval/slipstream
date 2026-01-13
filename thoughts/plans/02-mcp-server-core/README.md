# Branch 2: MCP Server Core

**Branch**: `feature/mcp-server-core`
**Scope**: MCP Server Foundation + Session Management
**Dependencies**: None (foundational branch)
**Complexity**: Medium

---

## Description

The core MCP server infrastructure using FastMCP, including WebSocket server for dashboard updates and session file management.

---

## Components

| Component | Description |
|-----------|-------------|
| FastMCP server | stdio transport, tool registration, lifecycle |
| WebSocket server | Dashboard state push at 500ms intervals |
| Session tools | `start_session`, `end_session`, `get_status` |
| Session storage | JSON files in `~/.slipstream/sessions/` |
| Config management | User preferences, DPS ratio |
| State push format | WebSocket message structure |

---

## File Structure

```
src/mcp/
├── __init__.py
├── server.py              # FastMCP server main entry
├── websocket_server.py    # Dashboard WebSocket publisher
├── tools/
│   ├── __init__.py
│   └── session_tools.py   # start_session, end_session, get_status
├── storage/
│   ├── __init__.py
│   ├── session_storage.py # Session file I/O
│   └── config.py          # User configuration
└── models/
    ├── __init__.py
    └── messages.py        # WebSocket message schemas
```

---

## Key Interfaces

### MCP Tools

```python
@mcp.tool()
def start_session() -> dict:
    """Begin a new swim session."""
    return {"session_id": "...", "started_at": "..."}

@mcp.tool()
def end_session() -> dict:
    """End current session and save data."""
    return {"summary": {...}}

@mcp.tool()
def get_status() -> dict:
    """Get current system status."""
    return {"is_swimming": bool, "pose_detected": bool, ...}
```

### WebSocket Message

```json
{
    "type": "state_update",
    "timestamp": "2026-01-11T08:32:45.123Z",
    "session": {
        "active": true,
        "elapsed_seconds": 165,
        "stroke_count": 142,
        "stroke_rate": 52,
        "stroke_rate_trend": "stable",
        "estimated_distance_m": 213
    },
    "system": {
        "is_swimming": true,
        "pose_detected": true,
        "voice_state": "listening"
    }
}
```

---

## Data Directory Structure

```
~/.slipstream/
├── config.json              # User settings
├── sessions/
│   ├── 2026-01-11_0830.json
│   └── ...
├── transcript.log           # Voice transcriptions
└── logs/                    # System logs
```

---

## Success Criteria

- [ ] MCP server starts and responds to tool calls
- [ ] WebSocket pushes state at 500ms intervals
- [ ] Session files saved correctly as JSON
- [ ] Config file loads and saves preferences

---

## Downstream Dependencies

This branch is required by:
- Branch 4: `feature/swim-metrics`
- Branch 5: `feature/workout-system`
- Branch 6: `feature/dashboard`
- Branch 7: `feature/notifications`
