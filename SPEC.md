# Endless Pool AI Swim Coach - Technical Specification

**Version**: 0.1.0 (Draft)
**Status**: Requirements Gathering
**Goal**: 100% complete, 100% automatically verifiable specification before hardware purchase

---

## Table of Contents

1. [Vision & Goals](#1-vision--goals)
2. [Phased Approach](#2-phased-approach)
3. [Architecture Overview](#3-architecture-overview)
4. [Key Assumptions](#4-key-assumptions)
5. [Open Questions](#5-open-questions)
6. [Component Specifications (Phase 1)](#6-component-specifications-phase-1)
7. [Verification Strategy (Phase 1)](#7-verification-strategy-phase-1)
8. [Research Summary](#8-research-summary)

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

## 2. Phased Approach

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

- Distance/pace (not meaningful in endless pool)
- Turn analysis (no turns)
- Start/dive analysis (no starts)
- Multi-swimmer tracking (single user)

---

## 3. Architecture Overview

### 3.1 High-Level Architecture (Phase 1)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           JETSON ORIN NANO                                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      CLAUDE CODE CLI                                 │   │
│  │                                                                      │   │
│  │   - Primary interface (terminal or custom wrapper)                  │   │
│  │   - Configured to use swim-coach MCP server                         │   │
│  │   - Handles conversation / coaching logic                           │   │
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
│  │  ├── start_session        → Begin tracking                          │   │
│  │  ├── end_session          → Stop and save                           │   │
│  │  └── update_dashboard     → Push state to TV display                │   │
│  │                                                                      │   │
│  │  Internal:                                                          │   │
│  │  ├── Vision Pipeline (RTMPose + stroke detection)                  │   │
│  │  ├── State Store (current stroke rate, session time)               │   │
│  │  └── WebSocket Server (pushes to React dashboard)                  │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                         WebSocket  │                                        │
│                                    ▼                                        │
│                         ┌──────────────────┐                               │
│                         │  React Dashboard │                               │
│                         │  (Timer + Rate)  │                               │
│                         └────────┬─────────┘                               │
│                                  │ HDMI                                    │
└──────────────────────────────────┼──────────────────────────────────────────┘
                                   ▼
                            ┌───────────┐
                            │  Pool TV  │
                            └───────────┘
```

### 3.2 How It Works

1. **Claude Code CLI** configured with MCP server in settings
2. **Swim Coach MCP Server** runs as separate process (stdio transport)
3. Vision pipeline runs in background thread, continuously updating state
4. User asks question → Claude Code calls MCP tools → gets metrics → responds
5. Dashboard auto-updates via WebSocket (not controlled by Claude)

### 3.3 MCP Server Configuration

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

### 3.4 Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **Claude Code CLI** | No SDK needed; just configure MCP server |
| **Single MCP server** | All swim logic in one place; simpler |
| **stdio transport** | Standard MCP; easy to debug and test |
| **Dashboard via WebSocket** | Auto-updates independent of Claude |
| **Python** | Same as vision pipeline; FastMCP library |

### 3.5 Phase 1 Simplifications

| Removed for Phase 1 | Reason |
|---------------------|--------|
| TTS/speak tool | Just read Claude's text response for now |
| Complex dashboard control | Dashboard auto-displays current state |
| Session history queries | Just current session |
| Interval tracking | Just continuous swim time |

---

## 4. Key Assumptions

### 4.1 Hardware Assumptions

| Assumption | Confidence | Validation Needed |
|------------|------------|-------------------|
| Jetson Orin Nano can run RTMPose-m at 30+ FPS | High | Benchmark before purchase |
| Bone conduction headset works in pool environment | Medium | User testing required |
| Single above-water camera sufficient for technique analysis | Medium | Compare to underwater options |
| IP camera RTSP latency < 100ms | High | Standard for PoE cameras |
| Pool WiFi sufficient for API calls (~100KB/request) | High | Typical home WiFi |

### 4.2 Software Assumptions

| Assumption | Confidence | Notes |
|------------|------------|-------|
| Claude Code CLI can use custom MCP servers | High | Documented feature |
| FastMCP (Python) works for stdio MCP servers | High | Standard approach |
| TensorRT conversion for RTMPose is straightforward | Medium | MMDeploy provides tooling |
| React app can receive WebSocket updates smoothly | High | Standard browser capability |

### 4.3 Algorithm Assumptions (Phase 1)

| Assumption | Confidence | Validation Plan |
|------------|------------|-----------------|
| Stroke detection via wrist trajectory works above-water | Medium | Test on recorded video |
| Stroke rate calculation stable with 15s rolling window | Medium | Validate against manual count |

### 4.4 Endless Pool Assumptions

| Assumption | Notes |
|------------|-------|
| Swimmer stays mostly stationary | Defines camera framing |
| Current creates consistent water disturbance | May affect pose estimation |
| No lap/turn events to detect | Simplifies state machine |
| Session structure: intervals + rest periods | Work/rest timing focus |
| Current speed not automatically readable | Manual input or fixed |

---

## 5. Open Questions

### 5.1 Phase 1 Questions (Must Answer)

#### Q1: Camera Placement
- **Options**:
  - A) Ceiling mount, angled down ~45°
  - B) Wall mount at pool level, side view
- **For stroke rate**: Side view likely works; need to see arm motion
- **Decision needed before**: Buying camera/mount

#### Q2: Video Source for Testing
- **Question**: Where do we get swimming videos to test stroke detection?
- **Options**:
  - A) Record ourselves (phone/webcam)
  - B) Find public swimming footage online
  - C) Use existing swimming datasets
- **Decision needed before**: Building vision pipeline

#### Q3: Ground Truth for Stroke Rate
- **Question**: How do we know our stroke rate calculation is correct?
- **Options**:
  - A) Manually count strokes in test videos, compare
  - B) Use a stopwatch + count during live test
- **Simplest**: Manual annotation of 5-10 video clips

### 5.2 Deferred Questions (Phase 2+)

- Camera angle for technique metrics (rotation, symmetry)
- Voice interaction design (PTT vs proactive)
- Offline fallback behavior
- Session history and comparison
- Multi-stroke support

---

## 6. Component Specifications (Phase 1)

### 6.1 Swim Coach MCP Server

**Single server providing all Phase 1 functionality.**

**Tools**:

| Tool | Description | Returns |
|------|-------------|---------|
| `get_stroke_rate` | Current stroke rate | `{ "rate": 54, "trend": "stable", "window_seconds": 15 }` |
| `get_session_time` | Elapsed session time | `{ "elapsed_seconds": 1234, "formatted": "20:34" }` |
| `start_session` | Begin a new session | `{ "session_id": "...", "started_at": "..." }` |
| `end_session` | End current session | `{ "summary": { ... } }` |
| `get_status` | Overall system status | `{ "is_swimming": true, "pose_detected": true, ... }` |

### 6.2 Internal Components (Not MCP-Exposed)

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

### 6.3 Dashboard (React)

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

## 7. Verification Strategy (Phase 1)

### 7.1 What We Can Test Without Hardware

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

### 7.2 Phase 1 Verification Criteria

| Test | Pass Criteria |
|------|---------------|
| Stroke rate accuracy | Within ±2 strokes/min of manual count |
| Pose detection | Wrist keypoints detected >90% of frames |
| MCP response time | <100ms for get_stroke_rate |
| Dashboard latency | Updates within 500ms of state change |
| End-to-end query | Claude returns correct rate within 3s |

### 7.3 Test Data Needed

**Minimum for Phase 1**:
- 3-5 swimming video clips (freestyle, above-water view)
- Manual annotation: stroke times for each clip
- Can use: phone recording, YouTube clips, or webcam

### 7.4 Hardware-Deferred Tests

These wait until Jetson arrives:
- Inference speed on actual hardware
- Camera latency
- Full system under load

---

## 8. Research Summary

### 8.1 Pose Estimation (Phase 1)

**Recommended: YOLO11-Pose-s**
- Simpler deployment via Ultralytics
- Native Jetson support with TensorRT
- Good enough accuracy for stroke detection
- Can upgrade to RTMPose-m later if needed

**Why not RTMPose first**: More complex deployment (MMDeploy). YOLO11 gets us to working faster.

### 8.2 Stroke Rate Detection

**Approach**: Track wrist keypoint Y-position over time, detect peaks
- Each peak = one stroke cycle
- Calculate rate from inter-peak intervals
- Use rolling 15-second window

**Expected accuracy**: r > 0.91 correlation with manual count (based on research)

### 8.3 What We're NOT Doing in Phase 1

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

---

## Next Steps (Phase 1)

1. **Answer Q1-Q3** (camera placement, test videos, ground truth method)
2. **Get test videos** - record or find 3-5 freestyle swimming clips
3. **Build stroke detection** - YOLO11-Pose + peak detection algorithm
4. **Validate accuracy** - compare to manual stroke count
5. **Build MCP server** - expose stroke rate via tools
6. **Build dashboard** - simple React app with WebSocket
7. **Integration test** - Claude Code CLI + MCP server end-to-end
