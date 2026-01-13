# Branch 4: Swim Metrics

**Branch**: `feature/swim-metrics`
**Scope**: Real-time Swim Metric MCP Tools
**Dependencies**: Branch 1 (vision-pipeline), Branch 2 (mcp-server-core)
**Complexity**: Low

---

## Description

MCP tools that expose swim metrics to Claude, bridging the vision pipeline to the MCP server.

---

## Components

| Component | Description |
|-----------|-------------|
| `get_stroke_rate` | Current rate + trend from vision pipeline |
| `get_stroke_count` | Total strokes + estimated distance |
| `get_session_time` | Elapsed seconds + formatted string |
| Distance estimation | Stroke count × user-configured DPS ratio |
| Metric bridge | Adapter connecting vision pipeline to MCP |

---

## File Structure

```
src/mcp/tools/
├── swim_tools.py          # get_stroke_rate, get_stroke_count, get_session_time
└── metric_bridge.py       # Vision pipeline → MCP adapter
```

---

## Key Interfaces

```python
@mcp.tool()
def get_stroke_rate() -> dict:
    """Get current stroke rate and trend."""
    return {
        "rate": 54,
        "trend": "stable",
        "window_seconds": 15
    }

@mcp.tool()
def get_stroke_count() -> dict:
    """Get total strokes and estimated distance."""
    return {
        "count": 142,
        "estimated_distance_m": 213
    }

@mcp.tool()
def get_session_time() -> dict:
    """Get elapsed session time."""
    return {
        "elapsed_seconds": 1234,
        "formatted": "20:34"
    }
```

---

## Success Criteria

- [ ] `get_stroke_rate` returns data within 100ms
- [ ] Distance estimation uses config DPS ratio
- [ ] Tools return correct data from vision pipeline
- [ ] Tools handle "no session active" gracefully

---

## Upstream Dependencies

Requires:
- Branch 1: `feature/vision-pipeline` (stroke detection data)
- Branch 2: `feature/mcp-server-core` (MCP infrastructure)

---

## Downstream Dependencies

This branch is required by:
- Branch 5: `feature/workout-system`
