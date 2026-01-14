# Slipstream

Local AI swim coach for endless pools. Real-time stroke analysis using computer vision, voice interaction via Claude, and a poolside dashboard.

## Tech Stack

- **Python 3.11+** with `uv` package manager
- **Claude Agent SDK** for voice interaction and coaching
- **FastMCP** for MCP server (stdio transport)
- **YOLO11-Pose** for pose estimation (TensorRT on Jetson)
- **Whisper** (faster-whisper) for speech-to-text
- **React 18+ / TypeScript** for dashboard
- **WebSocket** for real-time dashboard updates

## Package Manager

This project uses **uv** for Python dependency management. Always use:

```bash
uv sync              # Install dependencies
uv run python ...    # Run Python scripts
uv run pytest        # Run tests
uv add <package>     # Add a dependency
uv remove <package>  # Remove a dependency
```

Never use `pip install` or `python` directly. Always prefix with `uv run`.

## Project Structure

```
src/
├── vision/          # Pose estimation, stroke detection, rate calculation
├── mcp/             # FastMCP server, tools, workout system
├── stt/             # Whisper transcription daemon (continuous)
├── agent/           # Claude Agent SDK integration
├── tts/             # Text-to-speech (ElevenLabs/OpenAI)
└── notifications/   # Telegram/SMS session summaries

dashboard/           # React frontend (separate npm workspace)
verification/        # ML benchmarks, integration tests
tests/               # Unit tests (pytest)
thoughts/            # Design docs and specs (see below)
```

## Essential Commands

```bash
# Python
uv sync                                    # Install dependencies
uv run python -m src.mcp.server            # Start MCP server
uv run pytest tests/                       # Run unit tests
uv run pytest tests/ -v                    # Verbose test output

# Dashboard (in dashboard/ directory)
npm install                                # Install dependencies
npm run dev                                # Start dev server

# Verification
uv run python verification/pose/run_pose_on_video.py <video>
uv run python verification/pose/benchmark_fps.py
```

## Code Conventions

- Type hints required for all Python functions
- Use `@dataclass` for data structures
- Async for I/O-bound operations (WebSocket, file reads)
- Sync for CPU-bound (vision pipeline, stroke detection)
- React components use TypeScript interfaces
- Format with `black` (Python) and `prettier` (TypeScript)

## Key Interfaces

```python
# Vision output
@dataclass
class PoseResult:
    keypoints: np.ndarray  # Shape: (17, 3)
    confidence: float
    timestamp: float

# Core state
@dataclass
class SwimState:
    session_active: bool
    stroke_count: int
    stroke_rate: float
    stroke_rate_trend: str  # "increasing" | "stable" | "decreasing"
```

## Runtime Data

User data stored at `~/.slipstream/` (not in repo):

```
~/.slipstream/
├── config.json       # User settings (DPS ratio, notifications)
├── sessions/         # Session JSON files
├── transcript.log    # Voice transcriptions
└── logs/
```

## Documentation

Detailed specs in `thoughts/`:

- `thoughts/specs/technical-spec.md` - Architecture and components
- `thoughts/specs/user-journey.md` - User experience flow
- `thoughts/plans/implementation-plan.md` - 9-branch development plan
- `thoughts/project-structure.md` - Full directory structure

Each branch has its own spec: `thoughts/plans/01-vision-pipeline/` through `09-claude-integration/`

## Important Notes

- ML models in `models/` are gitignored (large files, device-specific)
- WebSocket requires both MCP server AND dashboard running
- STT runs as independent systemd service, writes to transcript.log with sequence IDs
- Agent SDK monitors transcript.log and tracks processed messages
- Never commit `.env` files or API keys
- Dashboard must be readable from 10ft (pool distance)

## Testing

```bash
uv run pytest tests/                       # All tests
uv run pytest tests/vision/ -v             # Vision tests only
uv run pytest tests/ -k "stroke"           # Tests matching "stroke"
uv run pytest tests/ --cov=src             # With coverage
```

## Branch Development

Nine parallel branches (see `thoughts/plans/`):

| # | Branch | Scope |
|---|--------|-------|
| 1 | vision-pipeline | Pose estimation, stroke detection |
| 2 | mcp-server-core | FastMCP, sessions, WebSocket |
| 3 | stt-service | Whisper continuous transcription |
| 4 | swim-metrics | Stroke rate/count MCP tools |
| 5 | workout-system | Intervals, state machine |
| 6 | dashboard | React poolside display |
| 7 | notifications | SMS/Telegram summaries |
| 8 | verification | Test infrastructure |
| 9 | claude-integration | Agent SDK, TTS, agent behavior |

Foundational (1, 2, 3) can start immediately. Others have dependencies.
