# Slipstream Implementation Plan

**Version**: 1.0.0
**Status**: Planning
**Purpose**: Define parallel implementation branches for the complete Slipstream system

---

## Overview

This document outlines how to implement Slipstream as a set of parallel development branches that can be worked on simultaneously and merged together. The plan is designed to maximize parallel development while respecting component dependencies.

### Project Summary

Slipstream is an AI-powered swim coaching system for endless pools, consisting of:
- Local ML models (pose estimation, speech-to-text)
- MCP server exposing tools to Claude
- Real-time React dashboard
- Voice interaction via Claude Code CLI

---

## Branch Structure

### Branch Dependency Graph

```
                    ┌─────────────────────────────────────────────┐
                    │              FOUNDATIONAL                    │
                    │         (can start immediately)              │
                    └─────────────────────────────────────────────┘
                                        │
            ┌───────────────────────────┼───────────────────────────┐
            │                           │                           │
            ▼                           ▼                           ▼
  ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
  │ 1. vision-      │       │ 2. mcp-server-  │       │ 3. stt-service  │
  │    pipeline     │       │    core         │       │                 │
  └────────┬────────┘       └────────┬────────┘       └────────┬────────┘
           │                         │                          │
           │            ┌────────────┴────────────┐             │
           │            │                         │             │
           ▼            ▼                         ▼             │
  ┌─────────────────────────────┐    ┌─────────────────┐       │
  │    4. swim-metrics          │    │ 7. notifications│       │
  │    (vision + mcp-core)      │    └─────────────────┘       │
  └────────────┬────────────────┘                               │
               │                                                │
               ▼                                                │
  ┌─────────────────────────────┐    ┌─────────────────────────┐
  │    5. workout-system        │    │ 6. dashboard            │
  │    (swim-metrics + core)    │    │ (parallel, uses mocks)  │
  └────────────┬────────────────┘    └──────────┬──────────────┘
               │                                 │
               └─────────────┬───────────────────┘
                             │
                             ▼
              ┌─────────────────────────────────┐
              │    8. verification              │
              │    (tests all components)       │
              └──────────────┬──────────────────┘
                             │
                             ▼
              ┌─────────────────────────────────┐
              │    9. claude-integration        │
              │    (final integration)          │
              └─────────────────────────────────┘
```

---

## Branch Specifications

### Branch 1: `feature/vision-pipeline`

**Scope**: Pose Estimation + Stroke Detection Core

**Description**: The computer vision foundation that captures video, extracts pose keypoints, detects swim strokes, and calculates stroke rate.

#### Components

| Component | Description |
|-----------|-------------|
| YOLO11-Pose setup | Model loading, TensorRT export, inference wrapper |
| Keypoint buffer | 300-frame circular buffer for wrist trajectories |
| Stroke detector | Peak detection algorithm on wrist Y-position |
| Rate calculator | Rolling 15-second window, strokes/min calculation |
| Trend analysis | "increasing", "stable", "decreasing" detection |
| SwimState dataclass | Core state store for session data |
| Mock pose stream | For testing without camera |
| Verification scripts | Accuracy evaluation against ground truth |

#### File Structure

```
src/vision/
├── __init__.py
├── pose_estimator.py      # YOLO11 wrapper, TensorRT inference
├── keypoint_buffer.py     # Circular buffer for trajectory tracking
├── stroke_detector.py     # Peak detection on wrist Y-position
├── rate_calculator.py     # Rolling window stroke rate
├── trend_analyzer.py      # Rate trend detection
├── state_store.py         # SwimState dataclass
├── video_capture.py       # RTSP/file video source abstraction
└── mock/
    └── mock_pose_stream.py  # Synthetic keypoint generator
```

#### Key Interfaces

```python
@dataclass
class PoseResult:
    keypoints: np.ndarray      # Shape: (17, 3) - x, y, confidence
    bbox: tuple[int, int, int, int]
    confidence: float
    timestamp: float

@dataclass
class SwimState:
    session_active: bool
    session_start: datetime | None
    stroke_count: int
    stroke_rate: float
    stroke_rate_trend: str  # "increasing" | "stable" | "decreasing"
    last_stroke_time: datetime | None
    pose_detected: bool
    is_swimming: bool
```

#### Success Criteria

- [ ] YOLO11-Pose processes video at >30 FPS on laptop GPU
- [ ] Wrist keypoints detected in >90% of frames
- [ ] Stroke rate within ±2 strokes/min of manual count
- [ ] Mock stream generates realistic synthetic data

#### Dependencies

None (foundational branch)

---

### Branch 2: `feature/mcp-server-core`

**Scope**: MCP Server Foundation + Session Management

**Description**: The core MCP server infrastructure using FastMCP, including WebSocket server for dashboard updates and session file management.

#### Components

| Component | Description |
|-----------|-------------|
| FastMCP server | stdio transport, tool registration, lifecycle |
| WebSocket server | Dashboard state push at 500ms intervals |
| Session tools | `start_session`, `end_session`, `get_status` |
| Session storage | JSON files in `~/.slipstream/sessions/` |
| Config management | User preferences, DPS ratio |
| State push format | WebSocket message structure |

#### File Structure

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

#### Key Interfaces

```python
# MCP Tools
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

```python
# WebSocket Message
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

#### Data Directory Structure

```
~/.slipstream/
├── config.json              # User settings
├── sessions/
│   ├── 2026-01-11_0830.json
│   └── ...
├── transcript.log           # Voice transcriptions
└── logs/                    # System logs
```

#### Success Criteria

- [ ] MCP server starts and responds to tool calls
- [ ] WebSocket pushes state at 500ms intervals
- [ ] Session files saved correctly as JSON
- [ ] Config file loads and saves preferences

#### Dependencies

None (foundational branch)

---

### Branch 3: `feature/stt-service`

**Scope**: Speech-to-Text Service + Voice Input

**Description**: Independent STT service using Whisper, transcript log management, and the MCP tool for voice input polling.

#### Components

| Component | Description |
|-----------|-------------|
| Whisper STT service | `faster-whisper` with CTranslate2, runs as daemon |
| Voice Activity Detection | Energy threshold or WebRTC VAD |
| Transcript log | Append-only log file with timestamps |
| Button handler | Bluetooth headset button → `<<<COMMIT>>>` marker |
| Systemd services | Service files for STT and button handler |
| Log rotation | Daily rotation, 7-day retention |
| MCP tool | `get_voice_input` with log-based polling |

#### File Structure

```
src/stt/
├── __init__.py
├── stt_service.py         # Whisper transcription daemon
├── vad.py                 # Voice activity detection
├── button_handler.py      # Bluetooth button monitoring (evdev)
├── log_manager.py         # Transcript log rotation/cleanup
└── voice_input_tool.py    # MCP get_voice_input implementation

services/
├── slipstream-stt.service
└── slipstream-button.service

scripts/
└── install_services.sh    # Systemd service installation
```

#### Transcript Log Format

```
~/.slipstream/transcript.log
───────────────────────────────────────
2026-01-11T08:30:15.123 what's my current
2026-01-11T08:30:16.456 stroke rate
2026-01-11T08:30:17.001 <<<COMMIT>>>
2026-01-11T08:32:45.789 start a new session
2026-01-11T08:32:46.234 <<<COMMIT>>>
```

#### Key Interfaces

```python
# MCP Tool
@mcp.tool()
def get_voice_input(timeout_seconds: int = 10) -> dict:
    """
    Poll for transcribed voice input.

    Returns when:
    - New transcription + button commit detected
    - Timeout expires (returns has_input: false)
    """
    return {"text": "...", "has_input": True}
```

```python
# STT Service
class STTService:
    def __init__(self, model: str = "small"):
        self.model = WhisperModel(model, device="cuda")

    async def run(self):
        """Main loop: capture audio, transcribe, append to log."""
        ...
```

#### Systemd Service

```ini
# /etc/systemd/system/slipstream-stt.service
[Unit]
Description=Slipstream STT Service
After=network.target sound.target

[Service]
Type=simple
User=swim
ExecStart=/usr/bin/python3 /opt/slipstream/src/stt/stt_service.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### Success Criteria

- [ ] Whisper transcribes speech with >95% accuracy
- [ ] Latency <1s for 3-second utterance
- [ ] Button handler writes COMMIT markers correctly
- [ ] `get_voice_input` returns on button press or timeout
- [ ] Log rotation works (keeps 7 days)

#### Dependencies

None (parallel to vision pipeline)

---

### Branch 4: `feature/swim-metrics`

**Scope**: Real-time Swim Metric MCP Tools

**Description**: MCP tools that expose swim metrics to Claude, bridging the vision pipeline to the MCP server.

#### Components

| Component | Description |
|-----------|-------------|
| `get_stroke_rate` | Current rate + trend from vision pipeline |
| `get_stroke_count` | Total strokes + estimated distance |
| `get_session_time` | Elapsed seconds + formatted string |
| Distance estimation | Stroke count × user-configured DPS ratio |
| Metric bridge | Adapter connecting vision pipeline to MCP |

#### File Structure

```
src/mcp/tools/
├── swim_tools.py          # get_stroke_rate, get_stroke_count, get_session_time
└── metric_bridge.py       # Vision pipeline → MCP adapter
```

#### Key Interfaces

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

#### Success Criteria

- [ ] `get_stroke_rate` returns data within 100ms
- [ ] Distance estimation uses config DPS ratio
- [ ] Tools return correct data from vision pipeline
- [ ] Tools handle "no session active" gracefully

#### Dependencies

- `feature/vision-pipeline` (stroke detection data)
- `feature/mcp-server-core` (MCP infrastructure)

---

### Branch 5: `feature/workout-system`

**Scope**: Structured Workout Management

**Description**: Complete workout/interval system with MCP tools, state machine, and automatic segment transitions.

#### Components

| Component | Description |
|-----------|-------------|
| Workout data model | `WorkoutSegment`, `Workout`, `WorkoutState` |
| MCP tools | `create_workout`, `start_workout`, `get_workout_status`, `skip_segment`, `end_workout`, `list_workout_templates` |
| State machine | NO_WORKOUT → CREATED → ACTIVE → COMPLETE |
| Auto-transitions | Duration/distance triggers, swim/rest detection |
| Segment types | warmup, work, rest, cooldown |
| Template storage | Saved workout plans |
| WebSocket integration | Workout state in dashboard updates |

#### File Structure

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

#### Data Models

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

#### State Machine

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

#### Automatic Segment Transitions

| Current Segment | Transition Trigger | Next Action |
|-----------------|-------------------|-------------|
| warmup | Duration elapsed OR stop swimming | → first work |
| work | Distance target OR stop swimming | → rest |
| rest | Duration elapsed OR start swimming | → next work |
| cooldown | Duration elapsed OR stop swimming | → complete |

#### Key Interfaces

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

#### Success Criteria

- [ ] Can create workouts with all segment types
- [ ] State machine transitions correctly
- [ ] Auto-transitions work based on duration/distance
- [ ] Workout data saved in session files
- [ ] Templates can be saved and retrieved

#### Dependencies

- `feature/mcp-server-core` (MCP infrastructure)
- `feature/swim-metrics` (distance/stroke detection for transitions)

---

### Branch 6: `feature/dashboard`

**Scope**: React Dashboard Application

**Description**: The poolside display showing real-time metrics, workout progress, and voice status with adaptive layouts for different system states.

#### Components

| Component | Description |
|-----------|-------------|
| React app | Create React App with TypeScript, dark theme |
| WebSocket client | Connect to MCP server, handle reconnection |
| State displays | SLEEPING, STANDBY, SESSION, SUMMARY views |
| Adaptive layouts | Minimal when swimming, rich when resting |
| Stroke rate display | Giant numbers + trend arrow |
| Rate graph | Sparkline visualization (last 2 min) |
| Workout display | Interval progress, segment info, rest timer |
| Voice indicator | Status dot with state labels |
| Coach message | Fading message display during rest |

#### File Structure

```
dashboard/
├── package.json
├── tsconfig.json
├── public/
│   └── index.html
├── src/
│   ├── index.tsx
│   ├── App.tsx
│   ├── types/
│   │   └── state.ts           # TypeScript interfaces
│   ├── hooks/
│   │   ├── useWebSocket.ts    # WebSocket connection
│   │   └── useSystemState.ts  # State management
│   ├── components/
│   │   ├── StrokeRate.tsx     # Giant rate display
│   │   ├── SessionTimer.tsx   # Elapsed time
│   │   ├── RateGraph.tsx      # Sparkline chart
│   │   ├── IntervalProgress.tsx
│   │   ├── VoiceIndicator.tsx
│   │   ├── CoachMessage.tsx
│   │   └── DistanceEstimate.tsx
│   ├── layouts/
│   │   ├── SleepingLayout.tsx
│   │   ├── StandbyLayout.tsx
│   │   ├── SwimmingLayout.tsx   # Minimal, giant metrics
│   │   ├── RestingLayout.tsx    # Expanded, rich info
│   │   └── SummaryLayout.tsx    # Post-session stats
│   └── styles/
│       ├── theme.css          # Dark theme, large fonts
│       └── animations.css     # Transitions, fades
```

#### Layout States

| State | Layout | Primary Elements |
|-------|--------|------------------|
| SLEEPING | Off/Ambient | Clock only |
| STANDBY | Welcome | "Ready to swim", listening indicator |
| SWIMMING | Minimal | Giant stroke rate, time, interval |
| RESTING | Expanded | Last interval summary, next up, coach message |
| SUMMARY | Full | All stats, session graph |

#### SWIMMING Layout (Minimal)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                                                                             │
│                            14:32                                            │
│                                                                             │
│                                                                             │
│                           54 /min   ↔                                       │
│                                                                             │
│                                                                             │
│                        INTERVAL 2 of 4                                      │
│                                                                             │
│         ▁▂▃▄▅▆▅▄▃▄▅▆▇▆▅▄▅▆▅▄▃▄▅▆▇▆▅▄▃▂▁▂▃▄▅▆▅▄▃▂                     │
│                                                                             │
│                                                     ◉ Listening             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### RESTING Layout (Expanded)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│         14:32                                              REST 0:45        │
│      SESSION TIME                                         remaining         │
│                                                                             │
├────────────────────────────────────┬────────────────────────────────────────┤
│                                    │                                        │
│       LAST INTERVAL                │       NEXT UP                          │
│       Avg: 52 /min                 │       INTERVAL 2 of 4                  │
│       Est: ~120m                   │       4:00 duration                    │
│       Strokes: 80                  │                                        │
│                                    │                                        │
├────────────────────────────────────┴────────────────────────────────────────┤
│                                                                             │
│  ▁▂▃▄▅▆▅▄▃▄▅▆▇▆▅▄▅▆▅▄▃▄▅▆▇▆▅▄▃▂▁▂▃▄▅▆▅▄▃▂ (session so far)                │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  COACH: "Solid interval! You held 52 consistently. Ready for the next?"    │
│                                                                             │
│  ◉ Listening...                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Success Criteria

- [ ] Dashboard connects to WebSocket and displays state
- [ ] Layout transitions smoothly between states
- [ ] Text readable from 10ft distance (pool)
- [ ] Dark theme reduces glare
- [ ] Voice indicator shows correct status
- [ ] Works with mock data for early development

#### Dependencies

- `feature/mcp-server-core` (WebSocket protocol)
- Can start early with mock data

---

### Branch 7: `feature/notifications`

**Scope**: Post-Session Notifications

**Description**: Send session summaries via SMS or Telegram after workout completion.

#### Components

| Component | Description |
|-----------|-------------|
| Notification service | Abstract base + implementations |
| Telegram integration | Bot API, message formatting |
| SMS integration | Twilio or similar provider |
| Session summary format | Markdown template |
| Integration | Trigger on `end_session` |

#### File Structure

```
src/notifications/
├── __init__.py
├── base.py                # Abstract NotificationService
├── telegram.py            # Telegram bot implementation
├── sms.py                 # SMS via Twilio
├── formatter.py           # Summary message formatting
└── config.py              # API keys, preferences
```

#### Key Interfaces

```python
class NotificationService(ABC):
    @abstractmethod
    async def send(self, recipient: str, message: str) -> bool:
        """Send notification, return success status."""
        ...

class TelegramNotifier(NotificationService):
    def __init__(self, bot_token: str):
        ...

class SMSNotifier(NotificationService):
    def __init__(self, twilio_sid: str, twilio_token: str, from_number: str):
        ...
```

#### Message Format

```
🏊 Swim Session Complete

Duration: 32:14
Est. Distance: ~1,200m
Avg Stroke Rate: 53/min

Intervals: 4 × 4min (all completed)
Notes: Stroke rate improved vs yesterday (+2/min)
```

#### Success Criteria

- [ ] Telegram messages send successfully
- [ ] SMS messages send successfully
- [ ] Summary format is clear and readable
- [ ] Notifications triggered on session end
- [ ] Handles API failures gracefully

#### Dependencies

- `feature/mcp-server-core` (session data for summary)

---

### Branch 8: `feature/verification`

**Scope**: Testing Infrastructure & Validation

**Description**: Mock data generators, ground truth comparison, and integration tests for validating the complete system.

#### Components

| Component | Description |
|-----------|-------------|
| Mock streams | `MockPoseStream`, `MockAudioStream` |
| Ground truth format | JSON annotation schema |
| Accuracy evaluation | Stroke rate comparison scripts |
| Benchmark scripts | FPS, latency measurements |
| Integration tests | End-to-end pipeline tests |
| Test data | Sample videos, audio, annotations |

#### File Structure

```
verification/
├── pose/
│   ├── run_pose_on_video.py      # Extract keypoints from video
│   ├── stroke_detector_test.py   # Test stroke detection
│   ├── evaluate_accuracy.py      # Compare to ground truth
│   └── benchmark_fps.py          # Measure inference speed
├── stt/
│   ├── run_whisper_on_audio.py   # Transcribe test audio
│   ├── evaluate_wer.py           # Word Error Rate
│   └── benchmark_latency.py      # Transcription speed
├── mock/
│   ├── mock_pose_stream.py       # Synthetic keypoint data
│   └── mock_audio_stream.py      # Pre-recorded queries
├── integration/
│   ├── test_mcp_tools.py         # Test all MCP tools
│   ├── test_websocket.py         # Test dashboard updates
│   └── test_full_pipeline.py     # End-to-end test
├── test_data/
│   ├── videos/
│   │   ├── freestyle_2min_side.mp4
│   │   └── ...
│   ├── annotations/
│   │   └── freestyle_2min_side_strokes.json
│   └── audio/
│       ├── stroke_rate_query.wav
│       └── ...
└── config.yaml                   # Model paths, thresholds
```

#### Ground Truth Format

```json
{
  "video": "freestyle_2min_side.mp4",
  "fps": 30,
  "strokes": [
    {"frame": 45, "time": 1.5, "arm": "left"},
    {"frame": 78, "time": 2.6, "arm": "right"},
    {"frame": 112, "time": 3.73, "arm": "left"}
  ],
  "notes": "Freestyle, moderate pace"
}
```

#### Verification Checklist

**Pose Estimation**:
- [ ] Model loads without error
- [ ] Process test video end-to-end
- [ ] Wrist keypoints detected >90% of frames
- [ ] Keypoint confidence >0.5 average
- [ ] Stroke rate ±2 strokes/min vs ground truth
- [ ] Inference >30 FPS on laptop

**Speech-to-Text**:
- [ ] Model loads without error
- [ ] >95% accuracy on clean audio
- [ ] >85% accuracy with pool noise
- [ ] Latency <1s for 3s utterance

**Integration**:
- [ ] Mock pipeline end-to-end works
- [ ] Real video + algorithm matches ground truth
- [ ] 10-minute continuous test stable

#### Success Criteria

- [ ] All verification checklists pass
- [ ] Mock streams work for development
- [ ] Integration tests cover critical paths
- [ ] Benchmarks documented

#### Dependencies

- `feature/vision-pipeline` (for pose testing)
- `feature/stt-service` (for STT testing)

---

### Branch 9: `feature/claude-integration`

**Scope**: Claude Code CLI Configuration

**Description**: Final integration connecting Claude Code CLI to the MCP server, including TTS output and agent behavior configuration.

#### Components

| Component | Description |
|-----------|-------------|
| MCP configuration | `.mcp.json` with swim-coach server |
| Environment setup | VIDEO_SOURCE, paths |
| TTS integration | ElevenLabs/OpenAI for voice output |
| Agent behavior | Polling loop, coaching patterns |
| System prompt | Claude's swim coach persona |

#### File Structure

```
.mcp.json                      # MCP server configuration
src/tts/
├── __init__.py
├── tts_service.py             # Text-to-speech wrapper
├── elevenlabs.py              # ElevenLabs implementation
├── openai_tts.py              # OpenAI TTS implementation
└── speaker.py                 # Audio playback control
docs/
├── agent_behavior.md          # How Claude uses the tools
├── coaching_patterns.md       # Example coaching dialogues
└── system_prompt.md           # Claude's persona
```

#### MCP Configuration

```json
{
  "mcpServers": {
    "swim-coach": {
      "command": "python",
      "args": ["-m", "swim_coach_mcp"],
      "env": {
        "VIDEO_SOURCE": "rtsp://192.168.1.100/stream",
        "SLIPSTREAM_HOME": "/home/swim/.slipstream"
      }
    }
  }
}
```

#### Agent Behavior

Claude operates in a polling loop:

```
1. Call get_voice_input(timeout=10)
2. If has_input:
   - Process user message
   - Call relevant swim tools
   - Respond via TTS (during rest only)
3. If !has_input and session active:
   - Check get_status() for state changes
   - Proactive coaching during rest
4. Loop
```

#### Coaching Patterns

```markdown
## During Rest (Proactive)
- Summarize last interval
- Provide encouragement
- Preview next segment
- Keep responses brief (<15 seconds)

## User Queries
- "What's my stroke rate?" → get_stroke_rate, brief response
- "How am I doing?" → comparison to previous sessions
- "Skip this interval" → skip_segment, confirm

## Don't Interrupt Swimming
- Only speak during rest periods
- Dashboard is primary feedback during active swimming
```

#### Success Criteria

- [ ] Claude Code CLI connects to MCP server
- [ ] Voice input loop works correctly
- [ ] TTS plays through poolside speaker
- [ ] Agent provides helpful coaching
- [ ] Respects "don't interrupt swimming" rule

#### Dependencies

- All other branches (final integration)

---

## Parallel Workstreams

The branches can be organized into parallel workstreams for team development:

### Workstream A: Vision
```
1. vision-pipeline → 4. swim-metrics → 5. workout-system
```

### Workstream B: Infrastructure
```
2. mcp-server-core → 7. notifications
                  ↘ 6. dashboard (parallel)
```

### Workstream C: Voice
```
3. stt-service → 9. claude-integration
```

### Workstream D: Quality
```
8. verification (parallel throughout)
```

---

## Merge Strategy

### Phase 1: Foundation
**Branches**: `vision-pipeline` + `mcp-server-core` + `stt-service`
**Result**: Core infrastructure ready, all foundational components working

### Phase 2: Metrics
**Branches**: + `swim-metrics` + `notifications`
**Result**: Basic swim tracking functional, notifications working

### Phase 3: Features
**Branches**: + `workout-system` + `dashboard`
**Result**: Full feature set, complete UI

### Phase 4: Testing
**Branches**: + `verification`
**Result**: All components tested and validated

### Phase 5: Integration
**Branches**: + `claude-integration`
**Result**: Production-ready system

---

## Summary Table

| # | Branch | Scope | Start | Depends On | Complexity |
|---|--------|-------|-------|------------|------------|
| 1 | `vision-pipeline` | Pose + stroke detection | Immediately | None | High |
| 2 | `mcp-server-core` | MCP + sessions | Immediately | None | Medium |
| 3 | `stt-service` | Whisper + voice input | Immediately | None | Medium |
| 4 | `swim-metrics` | Stroke rate tools | After 1+2 | 1, 2 | Low |
| 5 | `workout-system` | Interval workouts | After 4 | 2, 4 | High |
| 6 | `dashboard` | React UI | Early (mocks) | 2 | Medium |
| 7 | `notifications` | SMS/Telegram | After 2 | 2 | Low |
| 8 | `verification` | Testing suite | Throughout | 1, 3 | Medium |
| 9 | `claude-integration` | CLI + TTS | Last | All | Low |

---

## Team Allocation

For a team of 3-4 developers:

| Developer | Primary | Secondary |
|-----------|---------|-----------|
| Dev 1 | vision-pipeline, swim-metrics | verification (pose) |
| Dev 2 | mcp-server-core, workout-system | notifications |
| Dev 3 | stt-service, claude-integration | verification (stt) |
| Dev 4 | dashboard | verification (integration) |

---

## Related Documents

- [SPEC.md](./SPEC.md) - Technical specification
- [LOCAL_MODELS_SPEC.md](./LOCAL_MODELS_SPEC.md) - ML model details
- [USER_JOURNEY.md](./USER_JOURNEY.md) - User experience flow
- [WORKOUT_MODES_SPEC.md](./WORKOUT_MODES_SPEC.md) - Workout system spec
- [diagrams/local_models_flow.md](./diagrams/local_models_flow.md) - Data flow diagrams
- [diagrams/dashboard_options.md](./diagrams/dashboard_options.md) - Dashboard layouts

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-11 | Initial implementation plan |
