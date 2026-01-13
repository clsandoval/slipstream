# Branch 3: STT Service

**Branch**: `feature/stt-service`
**Scope**: Speech-to-Text Service + Voice Input
**Dependencies**: None (foundational branch)
**Complexity**: Medium

---

## Description

Independent STT service using Whisper, transcript log management, and the MCP tool for voice input polling.

---

## Components

| Component | Description |
|-----------|-------------|
| Whisper STT service | `faster-whisper` with CTranslate2, runs as daemon |
| Voice Activity Detection | Energy threshold or WebRTC VAD |
| Transcript log | Append-only log file with timestamps |
| Button handler | Bluetooth headset button → `<<<COMMIT>>>` marker |
| Systemd services | Service files for STT and button handler |
| Log rotation | Daily rotation, 7-day retention |
| MCP tool | `get_voice_input` with log-based polling |

---

## File Structure

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

---

## Transcript Log Format

```
~/.slipstream/transcript.log
───────────────────────────────────────
2026-01-11T08:30:15.123 what's my current
2026-01-11T08:30:16.456 stroke rate
2026-01-11T08:30:17.001 <<<COMMIT>>>
2026-01-11T08:32:45.789 start a new session
2026-01-11T08:32:46.234 <<<COMMIT>>>
```

---

## Key Interfaces

### MCP Tool

```python
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

### STT Service

```python
class STTService:
    def __init__(self, model: str = "small"):
        self.model = WhisperModel(model, device="cuda")

    async def run(self):
        """Main loop: capture audio, transcribe, append to log."""
        ...
```

---

## Systemd Service

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

---

## Success Criteria

- [ ] Whisper transcribes speech with >95% accuracy
- [ ] Latency <1s for 3-second utterance
- [ ] Button handler writes COMMIT markers correctly
- [ ] `get_voice_input` returns on button press or timeout
- [ ] Log rotation works (keeps 7 days)

---

## Downstream Dependencies

This branch is required by:
- Branch 8: `feature/verification`
- Branch 9: `feature/claude-integration`
