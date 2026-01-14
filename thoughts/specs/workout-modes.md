# Workout Modes Specification

**Version**: 0.1.0
**Status**: Draft
**Related**: [Technical Spec](./technical-spec.md), [User Journey](./user-journey.md), [Dashboard Layouts](../design/dashboard-layouts.md)

---

## Overview

This document specifies how Claude controls structured workouts (intervals, rest periods, warmup/cooldown) through the MCP server, and how that state flows to the dashboard.

**Key Insight**: The MCP server is the single source of truth for workout state. Claude creates and controls workouts via MCP tools. The dashboard receives state via WebSocket and renders accordingly.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   User: "Let's do 4x100m intervals like Tuesday"                           │
│                              │                                              │
│                              ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                      CLAUDE CODE CLI                                 │  │
│   │                                                                      │  │
│   │  1. Reads ~/.slipstream/sessions/ to find Tuesday's workout         │  │
│   │  2. Calls create_workout() with similar structure                   │  │
│   │  3. Calls start_workout() when user is ready                        │  │
│   │  4. Monitors progress, provides coaching during rest                │  │
│   │                                                                      │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              │ MCP Tool Calls                               │
│                              ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                    SWIM COACH MCP SERVER                             │  │
│   │                                                                      │  │
│   │  Workout Tools:                 Internal State:                      │  │
│   │  - create_workout()             - current_workout: Workout | None   │  │
│   │  - start_workout()              - workout_state: WorkoutState       │  │
│   │  - get_workout_status()         - current_segment_idx: int          │  │
│   │  - skip_segment()               - segment_start_time: datetime      │  │
│   │  - end_workout()                                                     │  │
│   │                                                                      │  │
│   │  Automatic Behavior:                                                 │  │
│   │  - Detects swimming → advances to next segment if in REST           │  │
│   │  - Detects rest → transitions SWIM segment to REST                  │  │
│   │  - Pushes state to dashboard via WebSocket                          │  │
│   │                                                                      │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              │ WebSocket (state push)                       │
│                              ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                      REACT DASHBOARD                                 │  │
│   │                                                                      │  │
│   │  Receives workout state → Renders appropriate view                  │  │
│   │  - No workout: basic session view                                   │  │
│   │  - Workout active: interval progress, segment info, rest timer      │  │
│   │  - Dashboard is "dumb" - just renders what it receives              │  │
│   │                                                                      │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Workout Data Model

### Workout Structure

```python
@dataclass
class WorkoutSegment:
    """A single segment of a workout (swim or rest)."""
    type: Literal["warmup", "work", "rest", "cooldown"]
    target_duration_seconds: int | None  # None = swim until stopped
    target_distance_m: int | None        # Optional distance target
    target_stroke_rate: tuple[int, int] | None  # (min, max) range, optional
    notes: str = ""                       # e.g., "focus on long strokes"

@dataclass
class Workout:
    """A complete workout plan."""
    workout_id: str                       # e.g., "wkt_2026-01-11_0830"
    name: str                             # e.g., "4x100m Intervals"
    segments: list[WorkoutSegment]
    created_at: datetime
    created_by: str = "claude"            # or "user" if manually defined

@dataclass
class WorkoutState:
    """Current state of an active workout."""
    workout: Workout
    current_segment_idx: int
    segment_started_at: datetime
    segment_elapsed_seconds: float
    is_swimming: bool                     # From pose detection
    total_elapsed_seconds: float
    segments_completed: list[SegmentResult]
```

### Example Workout

```json
{
  "workout_id": "wkt_2026-01-11_0830",
  "name": "4x100m Intervals",
  "segments": [
    { "type": "warmup", "target_duration_seconds": 300, "notes": "easy pace" },
    { "type": "work", "target_distance_m": 100, "target_stroke_rate": [50, 55] },
    { "type": "rest", "target_duration_seconds": 30 },
    { "type": "work", "target_distance_m": 100, "target_stroke_rate": [50, 55] },
    { "type": "rest", "target_duration_seconds": 30 },
    { "type": "work", "target_distance_m": 100, "target_stroke_rate": [50, 55] },
    { "type": "rest", "target_duration_seconds": 30 },
    { "type": "work", "target_distance_m": 100, "target_stroke_rate": [50, 55] },
    { "type": "cooldown", "target_duration_seconds": 180, "notes": "easy pace" }
  ],
  "created_at": "2026-01-11T08:30:00",
  "created_by": "claude"
}
```

---

## MCP Tools for Workouts

### Phase 1 Tools (extend existing SPEC.md tools)

| Tool | Description | Parameters | Returns |
|------|-------------|------------|---------|
| `create_workout` | Create a workout plan | `name`, `segments[]` | `{ workout_id, segments_count }` |
| `start_workout` | Begin executing a workout | `workout_id` | `{ started_at, first_segment }` |
| `get_workout_status` | Current workout state | none | `WorkoutStatus` (see below) |
| `skip_segment` | Skip to next segment | none | `{ skipped, now_on }` |
| `end_workout` | End workout early | none | `{ summary }` |
| `list_workout_templates` | List saved workout templates | `limit?` | `{ templates[] }` |

### Tool Specifications

#### `create_workout`

Creates a workout plan but does NOT start it. Claude builds the plan based on user request and history.

```python
@mcp.tool()
def create_workout(
    name: str,
    segments: list[dict],  # List of WorkoutSegment as dicts
    save_as_template: bool = False
) -> dict:
    """
    Create a workout plan.

    Args:
        name: Human-readable name (e.g., "4x100m Intervals")
        segments: List of segments, each with:
            - type: "warmup" | "work" | "rest" | "cooldown"
            - target_duration_seconds: int (optional)
            - target_distance_m: int (optional)
            - target_stroke_rate: [min, max] (optional)
            - notes: str (optional)
        save_as_template: If true, save for future "do that workout again"

    Returns:
        { "workout_id": "wkt_...", "segments_count": 9 }
    """
```

**Example call from Claude:**
```
User: "Let's do 4x100m with 30 second rest"

Claude calls: create_workout(
    name="4x100m Intervals",
    segments=[
        {"type": "warmup", "target_duration_seconds": 180},
        {"type": "work", "target_distance_m": 100},
        {"type": "rest", "target_duration_seconds": 30},
        {"type": "work", "target_distance_m": 100},
        {"type": "rest", "target_duration_seconds": 30},
        {"type": "work", "target_distance_m": 100},
        {"type": "rest", "target_duration_seconds": 30},
        {"type": "work", "target_distance_m": 100},
        {"type": "cooldown", "target_duration_seconds": 120}
    ]
)
```

#### `start_workout`

Begins workout execution. Must have an active session (calls `start_session` internally if needed).

```python
@mcp.tool()
def start_workout(workout_id: str) -> dict:
    """
    Start executing a created workout.

    Automatically starts a session if one isn't active.
    Dashboard will switch to workout view.

    Returns:
        {
            "started_at": "2026-01-11T08:30:00",
            "first_segment": { "type": "warmup", "target_duration_seconds": 180 },
            "total_segments": 9
        }
    """
```

#### `get_workout_status`

Returns comprehensive current state. Dashboard can also get this via WebSocket.

```python
@mcp.tool()
def get_workout_status() -> dict:
    """
    Get current workout execution status.

    Returns:
        {
            "has_active_workout": true,
            "workout_name": "4x100m Intervals",
            "current_segment": {
                "index": 3,
                "type": "work",
                "target_distance_m": 100,
                "elapsed_seconds": 45,
                "estimated_distance_m": 67,
                "target_stroke_rate": [50, 55],
                "actual_stroke_rate": 52
            },
            "progress": {
                "segments_completed": 2,
                "total_segments": 9,
                "work_segments_completed": 1,
                "total_work_segments": 4
            },
            "is_swimming": true,
            "next_segment": { "type": "rest", "target_duration_seconds": 30 }
        }
    """
```

#### `skip_segment`

Manually advance to next segment (useful if user wants to cut a segment short).

```python
@mcp.tool()
def skip_segment() -> dict:
    """
    Skip current segment and advance to next.

    Returns:
        {
            "skipped": { "type": "warmup", "completed_seconds": 120 },
            "now_on": { "type": "work", "index": 1 }
        }
    """
```

---

## Workout State Machine

```
                                    ┌──────────────────────────────────┐
                                    │                                  │
    create_workout()                │         NO WORKOUT               │
         │                          │     (basic session mode)         │
         │                          │                                  │
         ▼                          └──────────────────────────────────┘
┌──────────────────────────────────┐              ▲
│                                  │              │
│        WORKOUT CREATED           │              │ end_workout() or
│     (plan ready, not started)    │              │ workout completes
│                                  │              │
└──────────────────────────────────┘              │
         │                                        │
         │ start_workout()                        │
         ▼                                        │
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│                        WORKOUT ACTIVE                                │
│                                                                      │
│   ┌─────────────┐      segment        ┌─────────────┐               │
│   │   SEGMENT   │      completes      │   SEGMENT   │               │
│   │   ACTIVE    │ ─────────────────▶  │  TRANSITION │               │
│   │             │                     │             │               │
│   │  (swimming  │ ◀───────────────── │ (auto-start │               │
│   │   or rest)  │    next segment     │  next)      │               │
│   └─────────────┘                     └─────────────┘               │
│         │                                   │                        │
│         │ skip_segment()                    │ last segment done      │
│         ▼                                   ▼                        │
│   ┌─────────────┐                    ┌─────────────┐                │
│   │   SEGMENT   │                    │   WORKOUT   │                │
│   │   SKIPPED   │                    │  COMPLETE   │ ───────────────┘
│   └─────────────┘                    └─────────────┘
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Automatic Segment Transitions

The MCP server handles segment transitions automatically based on:

| Current Segment | Transition Trigger | Next Action |
|-----------------|-------------------|-------------|
| **warmup** | Duration elapsed OR user stops swimming | → first work segment |
| **work** | Distance target reached OR user stops swimming | → rest segment |
| **rest** | Duration elapsed OR user starts swimming | → next work segment |
| **cooldown** | Duration elapsed OR user stops swimming | → workout complete |

**Note**: Distance-based completion requires the stroke-to-distance ratio from config.

---

## WebSocket State Push

The MCP server pushes state to the dashboard via WebSocket. The dashboard does NOT call MCP tools - it just renders what it receives.

### WebSocket Message Format

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
  "workout": {
    "active": true,
    "name": "4x100m Intervals",
    "current_segment": {
      "index": 1,
      "type": "work",
      "elapsed_seconds": 45,
      "target_distance_m": 100,
      "estimated_distance_m": 67,
      "target_stroke_rate": [50, 55]
    },
    "progress": {
      "work_completed": 0,
      "work_total": 4,
      "display": "INTERVAL 1 of 4"
    },
    "next_segment": {
      "type": "rest",
      "target_duration_seconds": 30
    }
  },
  "system": {
    "is_swimming": true,
    "pose_detected": true,
    "voice_state": "listening"
  }
}
```

### Dashboard Rendering Rules

The dashboard renders based on the state it receives:

| State | Dashboard View | Key Elements |
|-------|---------------|--------------|
| `session.active && !workout.active` | Basic session | Time, stroke rate, distance |
| `workout.active && system.is_swimming` | Workout swimming | Interval progress, stroke rate, target zone |
| `workout.active && !system.is_swimming` | Workout rest | Rest countdown, last interval summary, next up |
| `workout.complete` | Workout summary | All intervals, totals, comparison |

---

## Claude's Role

Claude (via Agent SDK) is the "coach intelligence" - it:

1. **Monitors transcripts**: Tracks processed messages via sequence IDs (see SPEC.md §4.6)
2. **Understands user intent**: "Let's do the same as Tuesday" → reads session files
3. **Builds workout plans**: Constructs appropriate segment structure
4. **Creates workouts**: Calls `create_workout()` with the plan
5. **Starts workouts**: Calls `start_workout()` when user is ready
6. **Monitors progress**: Calls `get_workout_status()` during rest periods
7. **Provides coaching**: Speaks feedback during rest periods (via TTS)
8. **Handles exceptions**: "Skip this interval" → calls `skip_segment()`

### What Claude Does NOT Do

- **Does not control the dashboard directly** - MCP server handles WebSocket push
- **Does not detect swimming/rest** - MCP server vision pipeline does this
- **Does not manage timers** - MCP server tracks elapsed time
- **Does not advance segments automatically** - MCP server handles transitions

---

## Session File Storage

When a workout completes, it's saved in the session file with workout details:

```json
{
  "session_id": "2026-01-11_0830",
  "started_at": "2026-01-11T08:30:00",
  "ended_at": "2026-01-11T09:02:14",
  "duration_seconds": 1934,
  "stroke_count": 1847,
  "estimated_distance_m": 2770,
  "avg_stroke_rate": 57.3,
  "stroke_rate_samples": [...],

  "workout": {
    "name": "4x100m Intervals",
    "planned_segments": [...],
    "completed_segments": [
      {
        "type": "warmup",
        "planned_duration_seconds": 180,
        "actual_duration_seconds": 195,
        "stroke_count": 156,
        "avg_stroke_rate": 48
      },
      {
        "type": "work",
        "interval_number": 1,
        "planned_distance_m": 100,
        "estimated_distance_m": 105,
        "duration_seconds": 72,
        "stroke_count": 70,
        "avg_stroke_rate": 58
      },
      ...
    ]
  }
}
```

This allows Claude to read past sessions and recreate similar workouts.

---

## Phase 1 vs Phase 2 Scope

### Phase 1 (MVP)

- [x] Basic workout structure (segments with time/distance targets)
- [x] Manual segment transitions via `skip_segment()`
- [x] Auto-transition on duration targets
- [x] Stroke rate targets (display only, no enforcement)
- [x] Session file includes workout details

### Phase 2 (Future)

- [ ] Auto-transition based on distance targets (requires calibrated DPS)
- [ ] Workout templates saved and retrievable
- [ ] Pace alerts (voice notification if outside target rate)
- [ ] Progressive workouts (increase target over intervals)
- [ ] Rest auto-shortening/extension based on heart rate (if available)

---

## Example User Flow

```
User: "Hey, I want to do some interval training today. Maybe 4 sets of 100 meters with 30 seconds rest between each."

Claude: [reads ~/.slipstream/config.json for DPS ratio]
        [calls create_workout with segments]

"I've set up a workout for you:
- 3 minute warmup
- 4 × 100m intervals with 30 second rest
- 2 minute cooldown

Ready when you are. Just say 'start' or jump in and I'll begin tracking."

User: "Start"

Claude: [calls start_workout()]

"Starting your warmup. Take it easy for 3 minutes."

[Dashboard shows: WARMUP | 3:00 remaining | stroke rate]

[After warmup, user starts swimming harder]

[MCP server detects swimming, transitions to work segment]
[Dashboard shows: INTERVAL 1 of 4 | 52/min | target: 50-55]

[User stops at wall]

[MCP server detects rest, transitions to rest segment]
[Dashboard shows: REST | 0:28 remaining | Last: 58/min avg]

Claude: "Nice interval! 58 strokes per minute, right in your target zone. 25 seconds rest remaining."

[Rest timer expires, user starts swimming]

[MCP server transitions to work segment 2]
...

[After last interval]

Claude: "Excellent session! You completed all 4 intervals. Average rate was 56 per minute, very consistent. Take a couple minutes to cool down."

[User finishes cooldown]

Claude: [calls end_workout() or auto-completes]

"Workout complete! Total distance about 800 meters. I've saved the session. Want me to send you a summary?"
```

---

## Open Questions

| Question | Notes |
|----------|-------|
| Should Claude call `get_workout_status()` periodically, or rely on WebSocket? | Recommend: Claude queries on-demand (during rest), doesn't poll continuously |
| How to handle "pause" vs "end" workout? | Recommend: No explicit pause - rest segments handle this naturally |
| Should there be a `modify_workout()` tool? | Recommend: No - end current and create new if major changes needed |
| Voice feedback during work segments? | Recommend: Only if explicitly asked - default is silent during swimming |

---

## Integration with Existing Specs

### SPEC.md Changes Needed

Add to MCP Tools section (8.1):

```markdown
**Workout Tools** (in addition to session tools):
| Tool | Description | Returns |
|------|-------------|---------|
| `create_workout` | Create workout plan | `{ workout_id, segments_count }` |
| `start_workout` | Begin workout | `{ started_at, first_segment }` |
| `get_workout_status` | Current workout state | `WorkoutStatus` |
| `skip_segment` | Skip to next segment | `{ skipped, now_on }` |
| `end_workout` | End workout early | `{ summary }` |
```

### dashboard_options.md Alignment

The dashboard options doc already shows interval displays. This spec defines:
- How those states are **triggered** (MCP tools + auto-detection)
- What **data** the dashboard receives (WebSocket format)
- The **state machine** governing transitions

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.2.0 | 2026-01-14 | Updated for Claude Agent SDK (removed polling, added transcript monitoring) |
| 0.1.0 | 2026-01-11 | Initial draft |
