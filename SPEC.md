# Endless Pool AI Swim Coach - Technical Specification

**Version**: 0.2.0
**Status**: User Journey Complete, Technical Spec Aligned
**Goal**: 100% complete, 100% automatically verifiable specification before hardware purchase
**Related**: See [USER_JOURNEY.md](./USER_JOURNEY.md) for complete user experience flow

---

## Table of Contents

1. [Vision & Goals](#1-vision--goals)
2. [System States](#2-system-states)
3. [Phased Approach](#3-phased-approach)
4. [Architecture Overview](#4-architecture-overview)
5. [Data & Storage Philosophy](#5-data--storage-philosophy)
6. [Key Assumptions](#6-key-assumptions)
7. [Open Questions](#7-open-questions)
8. [Component Specifications (Phase 1)](#8-component-specifications-phase-1)
9. [Verification Strategy (Phase 1)](#9-verification-strategy-phase-1)
10. [Research Summary](#10-research-summary)

---

## 1. Vision & Goals

### 1.1 Product Vision

A local AI-powered swim coaching system for endless pools that provides:
- Real-time voice interaction during swimming
- Visual feedback on a poolside TV dashboard
- Comprehensive swim analytics and technique scoring
- Fully offline-capable operation (except for cloud LLM/TTS APIs)

### 1.2 Key Design Principles

| Principle | Description |
|-----------|-------------|
| **Progressive Disclosure** | Spec organized hierarchically - high-level first, details on demand |
| **100% Verifiable** | Every component testable without hardware via mocks/simulation |
| **Local-First** | All vision/audio processing on-device; cloud only for LLM/TTS |
| **MCP-Controlled Dashboard** | Agent has full programmatic control over dashboard state |

### 1.3 Success Criteria

1. Complete system can be simulated and tested using only:
   - Pre-recorded video files (instead of live camera)
   - Pre-recorded audio files (instead of live microphone)
   - Mock TTS output (text logs instead of audio playback)

2. All metrics calculations verified against ground truth annotations

3. Dashboard fully functional in browser before any hardware arrives

---

## 2. System States

The system operates in three distinct power/processing states:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           SYSTEM STATES                                  │
│                                                                          │
│   ┌──────────┐         ┌──────────┐         ┌──────────┐               │
│   │ SLEEPING │ ──────► │ STANDBY  │ ──────► │ SESSION  │               │
│   │          │ motion  │          │ "start" │          │               │
│   │ 1 FPM    │ detect  │ active   │ or auto │ swimming │               │
│   └──────────┘         └──────────┘         └──────────┘               │
│        ▲                    │                    │                       │
│        │                    │ timeout            │ "end" or             │
│        │                    │ (no activity)      │ timeout              │
│        │                    ▼                    │                       │
│        └────────────────────┴────────────────────┘                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

| State | Description | Processing | Transitions To |
|-------|-------------|------------|----------------|
| **Sleeping** | Low-power polling. 1 frame/minute, checks for presence. Dashboard off. Not listening. | Minimal | Standby (motion detected) |
| **Standby** | Person detected. Full vision active. Always listening. Ready for workout planning. | Medium | Session (voice/auto), Sleeping (timeout) |
| **Session** | Active swim session. Full tracking, proactive coaching during rest, dashboard live. | Full | Standby (session ends) |

### State Detection Methods

| Detection | Method |
|-----------|--------|
| **Presence** | Person detected in camera frame (wake from sleep) |
| **Swimming** | Active arm motion via pose estimation |
| **Resting** | Person in frame but no swimming motion |
| **Gone** | No person detected for extended period (~5 min) |

---

## 3. Phased Approach

### Phase 1: Stroke Rate MVP (Current Focus)

**Goal**: Validate entire pipeline with simplest possible metric

| Component | Phase 1 Scope |
|-----------|---------------|
| **Metric** | Stroke rate only (strokes/minute) |
| **Detection** | Wrist keypoint trajectory, peak detection |
| **Dashboard** | Timer + stroke rate + simple graph |
| **Voice** | Answer "what's my stroke rate?" |
| **Session** | Start/stop, log stroke rate over time |

**Why stroke rate first**:
- Highest confidence from video (r > 0.91 vs ground truth)
- Simple algorithm (no complex biomechanics)
- Single metric validates: camera, pose model, metric calc, dashboard, voice, agent
- Useful training feedback on its own

**Phase 1 Success Criteria**:
1. Stroke rate within ±2 strokes/min of manual count
2. Dashboard updates in real-time (<500ms latency)
3. Voice query returns correct current rate
4. Full session logged and retrievable

### Phase 2: Timing & Intervals

| Addition | Description |
|----------|-------------|
| Interval tracking | Work/rest periods, set structure |
| Stroke count | Total strokes per interval/session |
| Tempo consistency | Variance in stroke-to-stroke timing |
| Historical comparison | "vs last session" queries |

### Phase 3: Technique Metrics (Requires Validation)

| Metric | Feasibility | Notes |
|--------|-------------|-------|
| Body rotation | Low (video) | May need IMU sensor |
| Symmetry | Medium | Left/right cycle time comparison |
| Head position | Medium | Depends on camera angle |
| Stroke type | High | But freestyle-only for now |

**Phase 3 Decision Point**: After Phase 1, evaluate whether video-only technique metrics are accurate enough, or if IMU/underwater camera needed.

### Out of Scope (All Phases)

- Turn analysis (no turns in endless pool)
- Start/dive analysis (no starts)
- Multi-swimmer tracking (single user)
- GPS/actual distance (stationary swimming)

### Distance Estimation

Distance IS tracked, but estimated via user-configured ratio:

```
Estimated Distance = Stroke Count × Distance-Per-Stroke Ratio
```

- User sets their personal ratio (e.g., 1 stroke = 1.5m)
- Calibrated once, adjusted as technique changes
- Provides meaningful progress tracking despite stationary swimming

---

## 4. Architecture Overview

### 4.1 High-Level Architecture (Phase 1)

```
                    ┌─────────────┐
                    │  IP Camera  │
                    │   (RTSP)    │
                    └──────┬──────┘
                           │ Video Stream
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           JETSON ORIN NANO                                  │
│                                                                             │
│  ┌────────────────┐                                                        │
│  │  Poolside Mic  │─────► STT ─────┐                                       │
│  │ (always listen)│                │                                        │
│  └────────────────┘                │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      CLAUDE CODE CLI                                 │   │
│  │                                                                      │   │
│  │   - Primary interface (voice wrapper)                               │   │
│  │   - Configured to use swim-coach MCP server                         │   │
│  │   - Handles conversation / coaching logic                           │   │
│  │   - Always listening (single user, private space)                   │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                    MCP Tool Calls  │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                   SWIM COACH MCP SERVER                              │   │
│  │                   (Python - single server)                           │   │
│  │                                                                      │   │
│  │  Phase 1 Tools:                                                     │   │
│  │  ├── get_stroke_rate      → Current strokes/min + trend             │   │
│  │  ├── get_session_time     → Elapsed time                            │   │
│  │  ├── get_stroke_count     → Total strokes + est. distance           │   │
│  │  ├── start_session        → Begin tracking                          │   │
│  │  ├── end_session          → Stop, save, send notification           │   │
│  │  └── get_status           → System/swimming state                   │   │
│  │                                                                      │   │
│  │  Internal:                                                          │   │
│  │  ├── Vision Pipeline (YOLO11-Pose + stroke detection)              │   │
│  │  ├── State Store (stroke rate, count, session time)                │   │
│  │  ├── WebSocket Server (pushes to React dashboard)                  │   │
│  │  └── Notification Service (SMS/Telegram)                           │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│          ┌─────────────────────────┼─────────────────────────┐             │
│          │ WebSocket              │ TTS                      │             │
│          ▼                         ▼                          │             │
│  ┌──────────────────┐     ┌────────────────┐                 │             │
│  │  React Dashboard │     │ Poolside       │                 │             │
│  │  (Timer + Rate)  │     │ Speaker        │                 │             │
│  └────────┬─────────┘     └────────────────┘                 │             │
│           │ HDMI                                              │             │
└───────────┼──────────────────────────────────────────────────┘             │
            ▼                                                                 │
     ┌───────────┐                                                           │
     │  Pool TV  │                                                           │
     └───────────┘                                                           │
```

### 4.2 How It Works

1. **System wakes** when camera detects person (sleeping → standby)
2. **User speaks** → poolside mic → STT → Claude Code CLI
3. **Claude Code CLI** calls MCP tools to get metrics / control session
4. **MCP Server** runs vision pipeline, tracks strokes, manages state
5. **Claude responds** → TTS → poolside speaker (during rest periods only)
6. **Dashboard auto-updates** via WebSocket (always current)
7. **Session ends** → data saved → notification sent (SMS/Telegram)
8. **User leaves** → timeout → system returns to sleeping

### 4.3 MCP Server Configuration

```json
// ~/.claude.json or project .mcp.json
{
  "mcpServers": {
    "swim-coach": {
      "command": "python",
      "args": ["-m", "swim_coach_mcp"],
      "env": {
        "VIDEO_SOURCE": "rtsp://192.168.1.100/stream"
      }
    }
  }
}
```

### 4.4 Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **Claude Code CLI** | No SDK needed; just configure MCP server |
| **Single MCP server** | All swim logic in one place; simpler |
| **stdio transport** | Standard MCP; easy to debug and test |
| **Dashboard via WebSocket** | Auto-updates independent of Claude |
| **Python** | Same as vision pipeline; FastMCP library |
| **Always listening** | Single user, private space; no wake word needed |
| **Poolside speaker** | Voice output; headset is input-only |
| **Local file storage** | Agentic approach; Claude queries filesystem directly |

### 4.5 Voice Interaction Design

| Principle | Description |
|-----------|-------------|
| **Don't interrupt swimming** | Coach only speaks during rest or when asked |
| **Brief responses** | Keep voice output short; user is exercising |
| **Dashboard is primary** | Voice confirms, dashboard shows detail |
| **Proactive during rest** | Coach can initiate conversation during rest periods |

### 4.6 Phase 1 Simplifications

| Simplified for Phase 1 | Full Version (Later) |
|------------------------|----------------------|
| Voice command to start | Auto-detect swimming |
| Manual rest indication | Auto-detect rest via pose |
| Dashboard summary only | + SMS/Telegram notification |
| Always on (standby) | Sleeping → Standby → Session states |

---

## 5. Data & Storage Philosophy

**Principle: Agentic, not structured.**

| Aspect | Approach |
|--------|----------|
| **Session data** | Saved as local JSON files |
| **Workout plans** | No formal feature. Claude reads past sessions and recreates on request. |
| **Historical queries** | Claude queries local filesystem directly. No database. |
| **Configuration** | Simple local config file (distance-per-stroke ratio, notification prefs) |

### Why This Approach

- Claude Code CLI is inherently good at reading files and understanding context
- No need to build rigid data schemas when the AI can interpret freeform data
- Simplifies implementation; data format can evolve naturally
- User can say "do what I did last Tuesday" and Claude figures it out

### Data Directory Structure

```
~/.slipstream/
├── config.json              # User settings (distance ratio, notifications)
├── sessions/
│   ├── 2026-01-11_0830.json # Session data files
│   ├── 2026-01-10_1900.json
│   └── ...
└── logs/                    # System logs if needed
```

### Example Session File

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
  "intervals": [...]
}
```

Claude can query these files naturally: "How does today compare to last week?" → reads relevant files → computes comparison.

---

## 6. Key Assumptions

### 6.1 Hardware Assumptions

| Assumption | Confidence | Validation Needed |
|------------|------------|-------------------|
| Jetson Orin Nano can run YOLO11-Pose at 30+ FPS | High | Benchmark before purchase |
| Poolside microphone picks up voice clearly | Medium | Test in pool acoustics |
| Poolside speaker audible over pool noise | Medium | Volume/placement testing |
| Single above-water camera sufficient for stroke detection | High | Side view sees arm motion |
| IP camera RTSP latency < 100ms | High | Standard for PoE cameras |
| Pool WiFi sufficient for API calls (~100KB/request) | High | Typical home WiFi |

### 6.2 Software Assumptions

| Assumption | Confidence | Notes |
|------------|------------|-------|
| Claude Code CLI can use custom MCP servers | High | Documented feature |
| FastMCP (Python) works for stdio MCP servers | High | Standard approach |
| TensorRT conversion for RTMPose is straightforward | Medium | MMDeploy provides tooling |
| React app can receive WebSocket updates smoothly | High | Standard browser capability |

### 6.3 Algorithm Assumptions (Phase 1)

| Assumption | Confidence | Validation Plan |
|------------|------------|-----------------|
| Stroke detection via wrist trajectory works above-water | Medium | Test on recorded video |
| Stroke rate calculation stable with 15s rolling window | Medium | Validate against manual count |

### 6.4 Endless Pool Assumptions

| Assumption | Notes |
|------------|-------|
| Swimmer stays mostly stationary | Defines camera framing |
| Current creates consistent water disturbance | May affect pose estimation |
| No lap/turn events to detect | Simplifies state machine |
| Session structure: intervals + rest periods | Work/rest timing focus |
| Current speed not automatically readable | Manual input or fixed |

---

## 7. Open Questions

### 7.1 Phase 1 Questions (Resolved)

#### Q1: Camera Placement ✓
- **Decision**: Side view (wall mount at pool level)
- **Rationale**: Sees arm motion clearly for stroke detection

#### Q2: Video Source for Testing ✓
- **Decision**: Record ourselves + public footage
- **Plan**: Phone recording for initial testing, YouTube clips for variety

#### Q3: Ground Truth for Stroke Rate ✓
- **Decision**: Manual annotation
- **Plan**: Count strokes in 5-10 test clips, compare to algorithm output

#### Q4: Voice Interaction Design ✓
- **Decision**: Always listening (no wake word), proactive during rest only
- **Rationale**: Single user, private space; don't interrupt swimming

#### Q5: Data Storage ✓
- **Decision**: Local files (JSON), no database
- **Rationale**: Agentic approach; Claude queries filesystem directly

#### Q6: Distance Tracking ✓
- **Decision**: Stroke count × user-configured distance-per-stroke ratio
- **Rationale**: Provides meaningful progress tracking in stationary pool

### 7.2 Remaining Open Questions

| Question | Context |
|----------|---------|
| Auto-rest detection accuracy | Can pose reliably distinguish swimming vs standing? |
| Speaker placement | Where exactly? Volume for pool acoustics? |
| Notification service | Telegram vs SMS? API setup? |
| Camera angle for technique (Phase 3) | May need different angle for rotation/symmetry |

---

## 8. Component Specifications (Phase 1)

### 8.1 Swim Coach MCP Server

**Single server providing all Phase 1 functionality.**

**Tools**:

| Tool | Description | Returns |
|------|-------------|---------|
| `get_stroke_rate` | Current stroke rate | `{ "rate": 54, "trend": "stable", "window_seconds": 15 }` |
| `get_session_time` | Elapsed session time | `{ "elapsed_seconds": 1234, "formatted": "20:34" }` |
| `start_session` | Begin a new session | `{ "session_id": "...", "started_at": "..." }` |
| `end_session` | End current session | `{ "summary": { ... } }` |
| `get_status` | Overall system status | `{ "is_swimming": true, "pose_detected": true, ... }` |

### 8.2 Internal Components (Not MCP-Exposed)

**Vision Pipeline**:
- Captures RTSP stream or local video file
- Runs RTMPose (or YOLO11-Pose) for keypoint detection
- Tracks wrist trajectory, detects stroke cycles
- Updates state store every frame

**State Store**:
```python
@dataclass
class SwimState:
    session_active: bool
    session_start: datetime | None
    stroke_count: int
    stroke_rate: float  # strokes per minute
    stroke_rate_trend: str  # "increasing" | "stable" | "decreasing"
    last_stroke_time: datetime | None
    pose_detected: bool
```

**WebSocket Server**:
- Pushes state to dashboard every 500ms
- Dashboard displays current stroke rate + session time
- No MCP control needed; auto-updates

### 8.3 Dashboard (React)

**Phase 1 Display**:
```
┌─────────────────────────────────────┐
│                                     │
│         SESSION TIME                │
│           20:34                     │
│                                     │
│         STROKE RATE                 │
│         54 /min  ↔                  │
│                                     │
│    ▁▂▃▄▅▄▄▅▆▅▄▃▄▅▄▃▄▅▆▅▄          │
│    (last 2 minutes)                 │
│                                     │
└─────────────────────────────────────┘
```

- Large, readable from pool
- Dark theme for glare reduction
- Auto-updates via WebSocket

---

## 9. Verification Strategy (Phase 1)

### 9.1 What We Can Test Without Hardware

```
Level 0: Unit Tests
├── Stroke detection algorithm (given keypoints → stroke events)
├── Stroke rate calculation (given stroke times → rate)
└── State store logic

Level 1: Component Tests (Laptop)
├── Pose estimation on recorded video (any GPU)
├── Full vision pipeline end-to-end
├── MCP server responds correctly to tool calls
└── Dashboard renders and updates via WebSocket

Level 2: Integration Tests (Laptop)
├── Claude Code CLI + MCP server together
├── Ask "what's my stroke rate?" → correct answer
└── Dashboard shows same data as MCP returns
```

### 9.2 Phase 1 Verification Criteria

| Test | Pass Criteria |
|------|---------------|
| Stroke rate accuracy | Within ±2 strokes/min of manual count |
| Pose detection | Wrist keypoints detected >90% of frames |
| MCP response time | <100ms for get_stroke_rate |
| Dashboard latency | Updates within 500ms of state change |
| End-to-end query | Claude returns correct rate within 3s |

### 9.3 Test Data Needed

**Minimum for Phase 1**:
- 3-5 swimming video clips (freestyle, above-water view)
- Manual annotation: stroke times for each clip
- Can use: phone recording, YouTube clips, or webcam

### 9.4 Hardware-Deferred Tests

These wait until Jetson arrives:
- Inference speed on actual hardware
- Camera latency
- Full system under load

---

## 10. Research Summary

### 10.1 Pose Estimation (Phase 1)

**Recommended: YOLO11-Pose-s**
- Simpler deployment via Ultralytics
- Native Jetson support with TensorRT
- Good enough accuracy for stroke detection
- Can upgrade to RTMPose-m later if needed

**Why not RTMPose first**: More complex deployment (MMDeploy). YOLO11 gets us to working faster.

### 10.2 Stroke Rate Detection

**Approach**: Track wrist keypoint Y-position over time, detect peaks
- Each peak = one stroke cycle
- Calculate rate from inter-peak intervals
- Use rolling 15-second window

**Expected accuracy**: r > 0.91 correlation with manual count (based on research)

### 10.3 What We're NOT Doing in Phase 1

| Metric | Why Deferred |
|--------|--------------|
| Body rotation | Requires IMU or underwater camera for accuracy |
| Symmetry | Needs left/right comparison; more complex |
| Head position | Depends heavily on camera angle |
| Stroke classification | Freestyle only for now |

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **Endless Pool** | Swim-in-place pool with adjustable current |
| **MCP** | Model Context Protocol - standard for LLM tool integration |
| **PTT** | Push-to-talk - button-activated voice input |
| **Stroke Rate** | Arm strokes per minute |
| **DPS** | Distance Per Stroke (not applicable to endless pool) |
| **SWOLF** | Swim golf score (time + strokes; not applicable) |
| **TTS** | Text-to-speech |
| **STT** | Speech-to-text |

---

## Appendix B: Related Documents

| Document | Description |
|----------|-------------|
| [LOCAL_MODELS_SPEC.md](./LOCAL_MODELS_SPEC.md) | Detailed spec for pose estimation and STT models |
| [diagrams/local_models_flow.md](./diagrams/local_models_flow.md) | Visual data flow diagrams |

---

## Appendix C: Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.1 | 2026-01-11 | Added local models spec reference |
| 0.1.0 | 2026-01-10 | Initial draft with architecture and questions |
| 0.2.0 | 2026-01-11 | Aligned with USER_JOURNEY.md: added system states, data philosophy, resolved open questions, updated architecture with audio I/O |

---

## Next Steps (Phase 1)

**Design Complete** ✓
1. ~~Answer Q1-Q3~~ (camera placement, test videos, ground truth method) ✓
2. ~~Define user journey~~ (see USER_JOURNEY.md) ✓
3. ~~Define data storage approach~~ (agentic, local files) ✓

**Implementation (Next)**
4. **Get test videos** - record or find 3-5 freestyle swimming clips
5. **Build stroke detection** - YOLO11-Pose + peak detection algorithm
6. **Validate accuracy** - compare to manual stroke count
7. **Build MCP server** - expose stroke rate via tools
8. **Build dashboard** - simple React app with WebSocket
9. **Integration test** - Claude Code CLI + MCP server end-to-end
10. **Add voice I/O** - STT input, TTS to speaker
