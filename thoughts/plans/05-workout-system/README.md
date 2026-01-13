# Branch 5: Workout System

**Branch**: `feature/workout-system`
**Scope**: Structured Workout Management
**Dependencies**: Branch 2 (mcp-server-core), Branch 4 (swim-metrics)
**Complexity**: High

---

## Description

Complete workout/interval system with MCP tools, state machine, and automatic segment transitions.

---

## Components

| Component | Description |
|-----------|-------------|
| Workout data model | `WorkoutSegment`, `Workout`, `WorkoutState` |
| MCP tools | `create_workout`, `start_workout`, `get_workout_status`, `skip_segment`, `end_workout`, `list_workout_templates` |
| State machine | NO_WORKOUT → CREATED → ACTIVE → COMPLETE |
| Auto-transitions | Duration/distance triggers, swim/rest detection |
| Segment types | warmup, work, rest, cooldown |
| Template storage | Saved workout plans |
| WebSocket integration | Workout state in dashboard updates |

---

## File Structure

```
src/mcp/
├── workout/
│   ├── __init__.py
│   ├── models.py          # WorkoutSegment, Workout, WorkoutState
│   ├── state_machine.py   # Workout state transitions
│   ├── tools.py           # MCP workout tools
│   ├── transitions.py     # Auto-transition logic
│   └── templates.py       # Template storage
```

---

## Data Models

```python
@dataclass
class WorkoutSegment:
    type: Literal["warmup", "work", "rest", "cooldown"]
    target_duration_seconds: int | None
    target_distance_m: int | None
    target_stroke_rate: tuple[int, int] | None
    notes: str = ""

@dataclass
class Workout:
    workout_id: str
    name: str
    segments: list[WorkoutSegment]
    created_at: datetime
    created_by: str = "claude"

@dataclass
class WorkoutState:
    workout: Workout
    current_segment_idx: int
    segment_started_at: datetime
    segment_elapsed_seconds: float
    is_swimming: bool
    total_elapsed_seconds: float
    segments_completed: list[SegmentResult]
```

---

## State Machine

```
    create_workout()              start_workout()
          │                            │
          ▼                            ▼
┌──────────────────┐        ┌──────────────────┐
│   NO_WORKOUT     │───────▶│     CREATED      │
└──────────────────┘        └──────────────────┘
          ▲                            │
          │                            ▼
          │                 ┌──────────────────┐
          │                 │      ACTIVE      │◀─────┐
          │                 └──────────────────┘      │
          │                            │              │
          │          segment completes │              │ next segment
          │                            ▼              │
          │                 ┌──────────────────┐      │
          └─────────────────│     COMPLETE     │──────┘
                            └──────────────────┘
```

---

## Automatic Segment Transitions

| Current Segment | Transition Trigger | Next Action |
|-----------------|-------------------|-------------|
| warmup | Duration elapsed OR stop swimming | → first work |
| work | Distance target OR stop swimming | → rest |
| rest | Duration elapsed OR start swimming | → next work |
| cooldown | Duration elapsed OR stop swimming | → complete |

---

## Key Interfaces

```python
@mcp.tool()
def create_workout(name: str, segments: list[dict], save_as_template: bool = False) -> dict:
    """Create a workout plan (does not start it)."""
    return {"workout_id": "wkt_...", "segments_count": 9}

@mcp.tool()
def start_workout(workout_id: str) -> dict:
    """Begin executing a created workout."""
    return {"started_at": "...", "first_segment": {...}, "total_segments": 9}

@mcp.tool()
def get_workout_status() -> dict:
    """Get current workout execution status."""
    return {
        "has_active_workout": True,
        "workout_name": "4x100m Intervals",
        "current_segment": {...},
        "progress": {...},
        "is_swimming": True,
        "next_segment": {...}
    }

@mcp.tool()
def skip_segment() -> dict:
    """Skip current segment and advance to next."""
    return {"skipped": {...}, "now_on": {...}}

@mcp.tool()
def end_workout() -> dict:
    """End workout early."""
    return {"summary": {...}}
```

---

## Success Criteria

- [ ] Can create workouts with all segment types
- [ ] State machine transitions correctly
- [ ] Auto-transitions work based on duration/distance
- [ ] Workout data saved in session files
- [ ] Templates can be saved and retrieved

---

## Upstream Dependencies

Requires:
- Branch 2: `feature/mcp-server-core` (MCP infrastructure)
- Branch 4: `feature/swim-metrics` (distance/stroke detection for transitions)
