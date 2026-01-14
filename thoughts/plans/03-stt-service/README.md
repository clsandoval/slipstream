# Branch 3: STT Service

**Branch**: `feature/stt-service`
**Scope**: Speech-to-Text Service
**Dependencies**: None (foundational branch)
**Complexity**: Low

---

## Description

Simple always-on STT service. Continuously transcribes speech and appends to a timestamped log file. No VAD, no buttons, no complexity.

---

## Components

| Component | Description |
|-----------|-------------|
| STT service | `faster-whisper` daemon, eternally transcribes |
| Transcript log | Append-only log file with timestamps |
| Log rotation | Daily rotation, 7-day retention |
| Systemd service | Service file for STT daemon |

---

## File Structure

```
src/stt/
├── __init__.py
├── stt_service.py         # Whisper transcription daemon
└── log_manager.py         # Transcript log write/rotation

services/
└── slipstream-stt.service

scripts/
└── install_services.sh    # Systemd service installation
```

---

## How It Works

1. Service starts, opens microphone
2. Records audio in chunks (e.g., 3-5 seconds)
3. Transcribes each chunk with Whisper
4. Appends transcription to log with timestamp
5. Repeat forever

That's it.

---

## Transcript Log Format

```
~/.slipstream/transcript.log
───────────────────────────────────────
2026-01-11T08:30:15.123 what's my current stroke rate
2026-01-11T08:32:45.789 start a new session
2026-01-11T08:35:12.456 how many laps have I done
```

---

## Key Interfaces

### STT Service

```python
class STTService:
    def __init__(self, model: str = "small"):
        self.model = WhisperModel(model, device="cuda")
        self.log_manager = LogManager()

    async def run(self):
        """Main loop: capture audio chunk, transcribe, append to log."""
        while True:
            audio = await self.capture_chunk()
            text = self.transcribe(audio)
            if text.strip():
                self.log_manager.append(text)
```

### Log Manager

```python
class LogManager:
    def __init__(self, log_path: Path = ~/.slipstream/transcript.log):
        ...

    def append(self, text: str) -> None:
        """Append timestamped transcription to log."""

    def rotate_if_needed(self) -> None:
        """Rotate log daily, keep 7 days."""
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

- [ ] Whisper transcribes speech continuously
- [ ] Transcriptions appended to log with timestamps
- [ ] Log rotation works (keeps 7 days)
- [ ] Service runs reliably as daemon

---

## Downstream Dependencies

This branch is required by:
- Branch 8: `feature/verification`
- Branch 9: `feature/claude-integration`
