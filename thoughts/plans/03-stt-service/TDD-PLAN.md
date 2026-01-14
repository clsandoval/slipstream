# STT Service - TDD Implementation Plan

## Overview

Test-Driven Development plan for Branch 3: STT Service. Simple always-on transcription.

---

## Phase 1: Log Manager

**Goal**: Transcript log file operations with rotation.

### Tests First (`tests/stt/test_log_manager.py`)

```python
# Test 1: Append transcription with timestamp
def test_append_transcription():
    # Given empty log file
    # When append("hello world") called
    # Then log contains "2026-01-11T08:30:15.123 hello world"

# Test 2: Multiple appends
def test_multiple_appends():
    # Given log with one entry
    # When append("second line") called
    # Then log has both entries in order

# Test 3: Creates log file if missing
def test_creates_log_file():
    # Given no log file exists
    # When append("first") called
    # Then file created with entry

# Test 4: Creates parent directory
def test_creates_parent_dir():
    # Given ~/.slipstream/ doesn't exist
    # When append("first") called
    # Then directory and file created

# Test 5: Log rotation
def test_rotate_log():
    # Given log file older than 1 day
    # When rotate_if_needed() called
    # Then old file renamed with date suffix

# Test 6: Cleanup old logs
def test_cleanup_old_logs():
    # Given log files from 10 days ago
    # When cleanup_old_logs(retention_days=7) called
    # Then files older than 7 days deleted

# Test 7: Skip empty text
def test_skip_empty_text():
    # Given empty string
    # When append("") called
    # Then nothing written to log
```

### Implementation (`src/stt/log_manager.py`)

```python
@dataclass
class LogManager:
    log_path: Path = Path.home() / ".slipstream" / "transcript.log"

    def append(self, text: str) -> None
    def rotate_if_needed(self) -> None
    def cleanup_old_logs(self, retention_days: int = 7) -> None
```

---

## Phase 2: STT Service

**Goal**: Whisper transcription daemon with audio capture.

### Tests First (`tests/stt/test_stt_service.py`)

```python
# Test 1: Transcribe audio array
def test_transcribe_audio():
    # Given np.ndarray of speech audio
    # When transcribe(audio) called
    # Then returns transcribed text

# Test 2: Handle silence
def test_transcribe_silence():
    # Given silent audio (zeros)
    # When transcribe(audio) called
    # Then returns empty string

# Test 3: Model loading
def test_model_loads():
    # Given valid model name "small"
    # When STTService(model="small") created
    # Then model loads without error

# Test 4: Service writes to log
def test_service_writes_to_log(mock_audio_input):
    # Given service with mock audio returning "hello"
    # When one iteration of run loop executes
    # Then "hello" appears in log file

# Test 5: Skip empty transcriptions
def test_skip_empty_transcriptions(mock_audio_input):
    # Given service with mock audio returning ""
    # When one iteration executes
    # Then nothing written to log

# Test 6: Continuous operation
def test_continuous_loop(mock_audio_input):
    # Given service running for 3 iterations
    # When audio produces "one", "two", "three"
    # Then all three in log
```

### Implementation (`src/stt/stt_service.py`)

```python
class STTService:
    def __init__(
        self,
        model: str = "small",
        device: str = "auto",  # auto-detect: cuda > cpu
        chunk_duration: float = 3.0,
    ):
        self.model = WhisperModel(model, device=device)
        self.log_manager = LogManager()
        self.chunk_duration = chunk_duration

    def transcribe(self, audio: np.ndarray) -> str
    async def capture_chunk(self) -> np.ndarray
    async def run(self) -> None  # Main daemon loop
```

---

## Phase 3: Integration Tests

**Goal**: End-to-end testing.

### Tests (`tests/stt/test_integration.py`)

```python
# Test 1: Full loop with real audio file
def test_transcribe_real_audio():
    # Given WAV file with known speech
    # When service processes it
    # Then correct text in log

# Test 2: Log rotation during operation
def test_rotation_during_operation():
    # Given service running
    # When day changes (mocked)
    # Then log rotates without interruption
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
def mock_whisper_model(mocker):
    """Mock WhisperModel for fast tests."""
    mock = mocker.patch("faster_whisper.WhisperModel")
    mock.return_value.transcribe.return_value = (
        [mocker.Mock(text="hello world")],
        None,
    )
    return mock
```

---

## Implementation Order

| Order | Component | Tests | Implementation |
|-------|-----------|-------|----------------|
| 1 | Log Manager | `test_log_manager.py` | `log_manager.py` |
| 2 | STT Service | `test_stt_service.py` | `stt_service.py` |
| 3 | Integration | `test_integration.py` | - |
| 4 | Systemd | Manual testing | Service file |

---

## Dependencies to Add

```bash
uv add faster-whisper numpy sounddevice
uv add --dev pytest-asyncio pytest-mock
```

---

## Success Metrics

- [x] All unit tests pass (35 tests)
- [x] Integration tests pass (5 tests)
- [x] >90% code coverage on `src/stt/` (log_manager: 97%, stt_service: 92%)
- [ ] Service runs continuously without memory leaks (requires hardware testing)
- [x] Log rotation verified
