# STT Service - TDD Implementation Plan

## Overview

Test-Driven Development plan for Branch 3: STT Service. Each phase follows the red-green-refactor cycle.

---

## Phase 1: Log Manager

**Goal**: Transcript log file operations with rotation and cleanup.

### Tests First (`tests/stt/test_log_manager.py`)

```python
# Test 1: Write transcription to log
def test_append_transcription():
    # Given empty log file
    # When append_transcription("hello world") called
    # Then log contains timestamped entry

# Test 2: Write COMMIT marker
def test_append_commit_marker():
    # Given existing log entries
    # When append_commit_marker() called
    # Then "<<<COMMIT>>>" appended with timestamp

# Test 3: Read entries since last commit
def test_get_entries_since_last_commit():
    # Given log with: "hello", "world", "<<<COMMIT>>>", "new input"
    # When get_entries_since_last_commit() called
    # Then returns ["new input"]

# Test 4: Read entries with no prior commit
def test_get_entries_no_prior_commit():
    # Given log with: "first", "second"
    # When get_entries_since_last_commit() called
    # Then returns ["first", "second"]

# Test 5: Log rotation creates new file
def test_rotate_log():
    # Given log file older than 1 day
    # When rotate_if_needed() called
    # Then old file renamed with date suffix

# Test 6: Cleanup old logs
def test_cleanup_old_logs():
    # Given log files from 10 days ago
    # When cleanup_old_logs(retention_days=7) called
    # Then files older than 7 days deleted
```

### Implementation (`src/stt/log_manager.py`)

```python
@dataclass
class LogManager:
    log_path: Path = ~/.slipstream/transcript.log

    def append_transcription(text: str) -> None
    def append_commit_marker() -> None
    def get_entries_since_last_commit() -> list[str]
    def rotate_if_needed() -> None
    def cleanup_old_logs(retention_days: int = 7) -> None
```

---

## Phase 2: Voice Activity Detection (VAD)

**Goal**: Detect speech vs silence in audio stream.

### Tests First (`tests/stt/test_vad.py`)

```python
# Test 1: Detect speech in audio chunk
def test_detect_speech_in_audio():
    # Given audio samples with speech
    # When is_speech(audio_chunk) called
    # Then returns True

# Test 2: Detect silence
def test_detect_silence():
    # Given audio samples with silence/low energy
    # When is_speech(audio_chunk) called
    # Then returns False

# Test 3: Energy threshold calculation
def test_energy_threshold():
    # Given audio samples
    # When calculate_energy(samples) called
    # Then returns RMS energy value

# Test 4: Configurable threshold
def test_custom_threshold():
    # Given VAD with threshold=0.05
    # When audio at 0.04 energy tested
    # Then is_speech returns False

# Test 5: Speech segment boundaries
def test_speech_segment_detection():
    # Given audio: [silence, speech, silence]
    # When get_speech_segments(audio) called
    # Then returns [(start_idx, end_idx)]
```

### Implementation (`src/stt/vad.py`)

```python
@dataclass
class VAD:
    energy_threshold: float = 0.02
    min_speech_duration: float = 0.3  # seconds

    def is_speech(audio_chunk: np.ndarray) -> bool
    def calculate_energy(samples: np.ndarray) -> float
    def get_speech_segments(audio: np.ndarray) -> list[tuple[int, int]]
```

---

## Phase 3: STT Service Core

**Goal**: Whisper-based transcription with audio capture.

### Tests First (`tests/stt/test_stt_service.py`)

```python
# Test 1: Transcribe audio file
def test_transcribe_audio_file():
    # Given WAV file with "hello world"
    # When transcribe(audio_path) called
    # Then returns "hello world"

# Test 2: Transcribe numpy array
def test_transcribe_array():
    # Given np.ndarray of audio samples
    # When transcribe_array(samples) called
    # Then returns transcribed text

# Test 3: Handle empty audio
def test_transcribe_empty_audio():
    # Given silent audio
    # When transcribe(audio) called
    # Then returns empty string

# Test 4: Model loading
def test_model_loads():
    # Given valid model name "small"
    # When STTService(model="small") created
    # Then model loads without error

# Test 5: Service writes to log
def test_service_writes_transcription():
    # Given running service with mock audio input
    # When speech detected and transcribed
    # Then transcription appears in log file

# Test 6: Service integrates VAD
def test_service_uses_vad():
    # Given service with VAD
    # When audio has silence gaps
    # Then only speech portions transcribed
```

### Implementation (`src/stt/stt_service.py`)

```python
class STTService:
    def __init__(self, model: str = "small", device: str = "cuda"):
        self.model = WhisperModel(model, device=device)
        self.vad = VAD()
        self.log_manager = LogManager()

    def transcribe(audio: np.ndarray | Path) -> str
    async def capture_audio() -> np.ndarray
    async def run() -> None  # Main daemon loop
```

---

## Phase 4: Button Handler

**Goal**: Bluetooth headset button detection via evdev.

### Tests First (`tests/stt/test_button_handler.py`)

```python
# Test 1: Detect button press event
def test_detect_button_press():
    # Given mock evdev device
    # When KEY_PLAYPAUSE event received
    # Then on_button_press callback called

# Test 2: Write COMMIT on press
def test_button_writes_commit():
    # Given button handler with log manager
    # When button pressed
    # Then "<<<COMMIT>>>" written to log

# Test 3: Find Bluetooth device
def test_find_bluetooth_device():
    # Given evdev devices list
    # When find_headset_device() called
    # Then returns Bluetooth audio device

# Test 4: Handle device disconnect
def test_handle_disconnect():
    # Given connected device
    # When device disconnects
    # Then handler attempts reconnect

# Test 5: Debounce rapid presses
def test_debounce():
    # Given rapid button presses (10ms apart)
    # When events processed
    # Then only one COMMIT written
```

### Implementation (`src/stt/button_handler.py`)

```python
class ButtonHandler:
    def __init__(self, log_manager: LogManager):
        self.log_manager = log_manager
        self.debounce_ms: int = 200

    def find_headset_device() -> evdev.InputDevice | None
    async def listen() -> None  # Main event loop
    def on_button_press() -> None
```

---

## Phase 5: MCP Voice Input Tool

**Goal**: Poll transcript log for voice input with timeout.

### Tests First (`tests/stt/test_voice_input_tool.py`)

```python
# Test 1: Return text after COMMIT
def test_get_voice_input_with_commit():
    # Given log: ["start session", "<<<COMMIT>>>"]
    # When get_voice_input() called
    # Then returns {"text": "start session", "has_input": True}

# Test 2: Timeout with no input
def test_get_voice_input_timeout():
    # Given empty log (no new commits)
    # When get_voice_input(timeout_seconds=1) called
    # Then returns {"text": "", "has_input": False} after 1s

# Test 3: Combine multiple fragments
def test_combine_fragments():
    # Given log: ["what's my", "stroke rate", "<<<COMMIT>>>"]
    # When get_voice_input() called
    # Then returns {"text": "what's my stroke rate", "has_input": True}

# Test 4: Wait for new COMMIT
def test_wait_for_commit():
    # Given no pending commits
    # When new COMMIT written during poll
    # Then returns immediately with text

# Test 5: Clear state after read
def test_clears_read_position():
    # Given previous input read
    # When new text and COMMIT arrive
    # Then only new text returned
```

### Implementation (`src/stt/voice_input_tool.py`)

```python
def get_voice_input(timeout_seconds: int = 10) -> dict:
    """
    Poll transcript log for voice input.

    Returns:
        {"text": str, "has_input": bool}
    """
    ...
```

---

## Phase 6: Integration Tests

**Goal**: End-to-end testing of full STT pipeline.

### Tests (`tests/stt/test_integration.py`)

```python
# Test 1: Full pipeline simulation
def test_full_pipeline():
    # Given: STT service running, audio input, button handler
    # When: Speech → transcription → button press
    # Then: get_voice_input returns correct text

# Test 2: Multiple utterances
def test_multiple_utterances():
    # Given: Three speech segments with commits
    # When: get_voice_input called three times
    # Then: Each returns correct text

# Test 3: Concurrent access
def test_concurrent_log_access():
    # Given: STT writing, button writing, tool reading
    # When: All operate simultaneously
    # Then: No file corruption or deadlocks
```

---

## Test Fixtures

```python
# conftest.py
@pytest.fixture
def temp_log_dir(tmp_path):
    """Temporary ~/.slipstream directory."""
    log_dir = tmp_path / ".slipstream"
    log_dir.mkdir()
    return log_dir

@pytest.fixture
def log_manager(temp_log_dir):
    """LogManager with temp directory."""
    return LogManager(log_path=temp_log_dir / "transcript.log")

@pytest.fixture
def sample_audio():
    """Load test audio file."""
    return np.load("tests/fixtures/sample_speech.npy")

@pytest.fixture
def mock_whisper_model():
    """Mock WhisperModel for fast tests."""
    ...
```

---

## Implementation Order

| Order | Component | Tests | Implementation |
|-------|-----------|-------|----------------|
| 1 | Log Manager | `test_log_manager.py` | `log_manager.py` |
| 2 | VAD | `test_vad.py` | `vad.py` |
| 3 | STT Service | `test_stt_service.py` | `stt_service.py` |
| 4 | Button Handler | `test_button_handler.py` | `button_handler.py` |
| 5 | Voice Input Tool | `test_voice_input_tool.py` | `voice_input_tool.py` |
| 6 | Integration | `test_integration.py` | - |
| 7 | Systemd Services | Manual testing | Service files |

---

## Dependencies to Add

```bash
uv add faster-whisper evdev numpy
uv add --dev pytest-asyncio
```

---

## Success Metrics

- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] >90% code coverage on `src/stt/`
- [ ] Transcription latency <1s (3s utterance)
- [ ] Button debounce working
- [ ] Log rotation verified
