# Slipstream Project Structure

**Version**: 1.0.0
**Status**: Planning
**Purpose**: Define the complete directory structure for the Slipstream codebase

---

## Overview

This document defines the recommended directory structure for Slipstream, organized to support parallel development across 9 implementation branches while maintaining clean separation between components.

---

## Repository Structure

```
slipstream/
├── src/                           # All Python source code
│   ├── __init__.py
│   │
│   ├── vision/                    # Branch 1: vision-pipeline
│   │   ├── __init__.py
│   │   ├── pose_estimator.py      # YOLO11 wrapper, TensorRT inference
│   │   ├── keypoint_buffer.py     # Circular buffer for trajectory tracking
│   │   ├── stroke_detector.py     # Peak detection on wrist Y-position
│   │   ├── rate_calculator.py     # Rolling window stroke rate
│   │   ├── trend_analyzer.py      # Rate trend detection
│   │   ├── state_store.py         # SwimState dataclass
│   │   ├── video_capture.py       # RTSP/file video source abstraction
│   │   └── mock/
│   │       └── mock_pose_stream.py
│   │
│   ├── mcp/                       # Branch 2: mcp-server-core
│   │   ├── __init__.py
│   │   ├── server.py              # FastMCP server main entry
│   │   ├── websocket_server.py    # Dashboard WebSocket publisher
│   │   ├── tools/                 # MCP tools
│   │   │   ├── __init__.py
│   │   │   ├── session_tools.py   # start_session, end_session, get_status
│   │   │   ├── swim_tools.py      # Branch 4: swim-metrics
│   │   │   ├── voice_tools.py     # get_voice_input
│   │   │   └── metric_bridge.py   # Vision pipeline → MCP adapter
│   │   ├── workout/               # Branch 5: workout-system
│   │   │   ├── __init__.py
│   │   │   ├── models.py          # WorkoutSegment, Workout, WorkoutState
│   │   │   ├── state_machine.py   # Workout state transitions
│   │   │   ├── tools.py           # MCP workout tools
│   │   │   ├── transitions.py     # Auto-transition logic
│   │   │   └── templates.py       # Template storage
│   │   ├── storage/
│   │   │   ├── __init__.py
│   │   │   ├── session_storage.py # Session file I/O
│   │   │   └── config.py          # User configuration
│   │   └── models/
│   │       ├── __init__.py
│   │       └── messages.py        # WebSocket message schemas
│   │
│   ├── stt/                       # Branch 3: stt-service
│   │   ├── __init__.py
│   │   ├── stt_service.py         # Whisper transcription daemon
│   │   ├── vad.py                 # Voice activity detection
│   │   ├── button_handler.py      # Bluetooth button monitoring (evdev)
│   │   └── log_manager.py         # Transcript log rotation/cleanup
│   │
│   ├── tts/                       # Branch 9: claude-integration
│   │   ├── __init__.py
│   │   ├── tts_service.py         # Text-to-speech wrapper
│   │   ├── elevenlabs.py          # ElevenLabs implementation
│   │   ├── openai_tts.py          # OpenAI TTS implementation
│   │   └── speaker.py             # Audio playback control
│   │
│   └── notifications/             # Branch 7: notifications
│       ├── __init__.py
│       ├── base.py                # Abstract NotificationService
│       ├── telegram.py            # Telegram bot implementation
│       ├── sms.py                 # SMS via Twilio
│       ├── formatter.py           # Summary message formatting
│       └── config.py              # API keys, preferences
│
├── dashboard/                     # Branch 6: dashboard (React)
│   ├── package.json
│   ├── tsconfig.json
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── index.tsx
│       ├── App.tsx
│       ├── types/
│       │   └── state.ts           # TypeScript interfaces
│       ├── hooks/
│       │   ├── useWebSocket.ts    # WebSocket connection
│       │   └── useSystemState.ts  # State management
│       ├── components/
│       │   ├── StrokeRate.tsx     # Giant rate display
│       │   ├── SessionTimer.tsx   # Elapsed time
│       │   ├── RateGraph.tsx      # Sparkline chart
│       │   ├── IntervalProgress.tsx
│       │   ├── VoiceIndicator.tsx
│       │   ├── CoachMessage.tsx
│       │   └── DistanceEstimate.tsx
│       ├── layouts/
│       │   ├── SleepingLayout.tsx
│       │   ├── StandbyLayout.tsx
│       │   ├── SwimmingLayout.tsx  # Minimal, giant metrics
│       │   ├── RestingLayout.tsx   # Expanded, rich info
│       │   └── SummaryLayout.tsx   # Post-session stats
│       └── styles/
│           ├── theme.css          # Dark theme, large fonts
│           └── animations.css     # Transitions, fades
│
├── verification/                  # Branch 8: verification
│   ├── pose/
│   │   ├── run_pose_on_video.py   # Extract keypoints from video
│   │   ├── stroke_detector_test.py
│   │   ├── evaluate_accuracy.py   # Compare to ground truth
│   │   └── benchmark_fps.py       # Measure inference speed
│   ├── stt/
│   │   ├── run_whisper_on_audio.py
│   │   ├── evaluate_wer.py        # Word Error Rate
│   │   └── benchmark_latency.py
│   ├── mock/
│   │   ├── mock_pose_stream.py    # Synthetic keypoint data
│   │   └── mock_audio_stream.py   # Pre-recorded queries
│   ├── integration/
│   │   ├── test_mcp_tools.py      # Test all MCP tools
│   │   ├── test_websocket.py      # Test dashboard updates
│   │   └── test_full_pipeline.py  # End-to-end test
│   ├── test_data/
│   │   ├── videos/
│   │   ├── annotations/
│   │   └── audio/
│   └── config.yaml                # Model paths, thresholds
│
├── services/                      # Systemd service files
│   ├── slipstream-stt.service
│   └── slipstream-button.service
│
├── scripts/
│   ├── install_services.sh        # Systemd installation
│   └── setup.sh                   # Development setup
│
├── models/                        # ML model files (gitignored)
│   ├── yolo11s-pose.pt            # PyTorch weights
│   ├── yolo11s-pose.engine        # TensorRT (generated on device)
│   └── whisper-small-ct2/         # CTranslate2 format
│
├── tests/                         # Unit tests (pytest)
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   ├── vision/
│   │   ├── test_stroke_detector.py
│   │   └── test_rate_calculator.py
│   ├── mcp/
│   │   ├── test_session_tools.py
│   │   └── test_workout_tools.py
│   ├── stt/
│   └── notifications/
│
├── thoughts/                      # Design documents & specs
│   ├── index.md                   # Documentation overview
│   ├── project-structure.md       # This file
│   ├── specs/
│   │   ├── technical-spec.md      # Main technical specification
│   │   ├── user-journey.md        # User experience flow
│   │   ├── local-models.md        # ML model details
│   │   └── workout-modes.md       # Workout system spec
│   ├── plans/
│   │   └── implementation-plan.md # 9-branch implementation plan
│   ├── design/
│   │   ├── dashboard-layouts.md   # Dashboard layout options
│   │   └── data-flow-diagrams.md  # Visual data flow
│   └── hardware/
│       ├── purchase-list.md       # Hardware shopping list
│       └── connection-diagram.md  # Physical setup
│
├── .mcp.json                      # MCP server configuration
├── pyproject.toml                 # Python project config
├── requirements.txt               # Python dependencies
├── .gitignore
└── README.md                      # Project overview
```

---

## Runtime Data Directory

User data is stored separately from the repository at `~/.slipstream/`:

```
~/.slipstream/
├── config.json              # User settings
│   {
│     "distance_per_stroke_m": 1.5,
│     "notification_method": "telegram",
│     "telegram_chat_id": "...",
│     "voice_output": true
│   }
│
├── sessions/                # Session data files
│   ├── 2026-01-11_0830.json
│   ├── 2026-01-10_1900.json
│   └── ...
│
├── transcript.log           # Voice transcriptions (append-only)
│
├── transcript_archive/      # Rotated transcript logs
│   └── transcript_20260110.log
│
└── logs/                    # System logs
    └── slipstream.log
```

---

## Directory Design Rationale

| Directory | Purpose | Notes |
|-----------|---------|-------|
| `src/` | All Python code | Single package for easy imports |
| `dashboard/` | React frontend | Separate tooling (npm/vite) |
| `verification/` | Test infrastructure | Not production code |
| `tests/` | Unit tests | Mirrors `src/` structure |
| `thoughts/` | Design docs | All specs and planning |
| `models/` | ML weights | Gitignored, large files |
| `~/.slipstream/` | Runtime data | User data, survives reinstalls |

---

## Package Imports

With this structure, imports are clean and intuitive:

```python
# Vision pipeline
from slipstream.vision import PoseEstimator, StrokeDetector
from slipstream.vision.state_store import SwimState

# MCP server
from slipstream.mcp.server import create_server
from slipstream.mcp.tools import session_tools, swim_tools
from slipstream.mcp.workout import WorkoutState, create_workout

# STT service
from slipstream.stt import STTService, VAD

# Notifications
from slipstream.notifications import TelegramNotifier, SMSNotifier
```

---

## Branch-to-Directory Mapping

| Branch | Primary Directories |
|--------|---------------------|
| `feature/vision-pipeline` | `src/vision/` |
| `feature/mcp-server-core` | `src/mcp/` (except tools/swim_tools, workout/) |
| `feature/stt-service` | `src/stt/`, `services/` |
| `feature/swim-metrics` | `src/mcp/tools/swim_tools.py`, `metric_bridge.py` |
| `feature/workout-system` | `src/mcp/workout/` |
| `feature/dashboard` | `dashboard/` |
| `feature/notifications` | `src/notifications/` |
| `feature/verification` | `verification/`, `tests/` |
| `feature/claude-integration` | `src/tts/`, `.mcp.json`, `thoughts/` |

---

## Gitignore Recommendations

```gitignore
# Python
__pycache__/
*.py[cod]
.venv/
venv/
*.egg-info/

# Models (large files)
models/*.pt
models/*.engine
models/whisper-*/

# Node
dashboard/node_modules/
dashboard/dist/
dashboard/build/

# IDE
.vscode/
.idea/

# Test data (optional - may want to track annotations)
verification/test_data/videos/
verification/test_data/audio/

# Environment
.env
.env.local

# OS
.DS_Store
Thumbs.db
```

---

## Related Documents

- [Technical Specification](./specs/technical-spec.md) - System architecture
- [Implementation Plan](./plans/implementation-plan.md) - Branch structure and scope
- [Local Models](./specs/local-models.md) - ML model details

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-13 | Initial directory structure |
