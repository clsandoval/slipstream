# Local Models Specification

**Purpose**: Define all ML models running locally on Jetson Orin, with a complete laptop-first verification strategy.

---

## Overview

Only **two specialized ML models** run locally:

| Model | Purpose | Why Local |
|-------|---------|-----------|
| **Pose Estimation** | Extract body keypoints from video | Real-time (<100ms), privacy, no cloud dependency |
| **Speech-to-Text** | Transcribe voice commands | Low latency for conversation, works offline |

Everything else is either:
- **Cloud**: LLM (Claude API), TTS (ElevenLabs/OpenAI)
- **Simple Python**: Stroke detection algorithm, peak detection, rate calculation

---

## 1. Pose Estimation Model

### 1.1 Model Selection

| Model | Params | Input | Keypoints | Jetson FPS (est.) | Notes |
|-------|--------|-------|-----------|-------------------|-------|
| **YOLO11-Pose-s** | 9.9M | 640x640 | 17 (COCO) | 50-80 FPS | Recommended for Phase 1 |
| YOLO11-Pose-m | 20.9M | 640x640 | 17 (COCO) | 30-50 FPS | Fallback if accuracy insufficient |
| RTMPose-m | 13.6M | 256x192 | 17 (COCO) | 40-60 FPS | More accurate, harder to deploy |

**Phase 1 Choice: YOLO11-Pose-s**
- Ultralytics provides native Jetson/TensorRT support
- Single-stage (detection + pose in one pass)
- Good enough for wrist tracking / stroke detection

### 1.2 Keypoints We Care About

For stroke detection, we primarily need:
```
Keypoint 9:  Left wrist   ← Primary
Keypoint 10: Right wrist  ← Primary
Keypoint 5:  Left shoulder (backup)
Keypoint 6:  Right shoulder (backup)
```

Full COCO-17 keypoint map:
```
0: nose           1: left_eye       2: right_eye
3: left_ear       4: right_ear      5: left_shoulder
6: right_shoulder 7: left_elbow     8: right_elbow
9: left_wrist     10: right_wrist   11: left_hip
12: right_hip     13: left_knee     14: right_knee
15: left_ankle    16: right_ankle
```

### 1.3 Input/Output Specification

**Input**:
```python
# Video frame from camera or file
frame: np.ndarray  # Shape: (H, W, 3), BGR, uint8
# Model expects 640x640, will auto-resize
```

**Output**:
```python
@dataclass
class PoseResult:
    keypoints: np.ndarray      # Shape: (17, 3) - x, y, confidence
    bbox: tuple[int, int, int, int]  # x1, y1, x2, y2
    confidence: float          # Detection confidence
    timestamp: float           # Frame timestamp in seconds
```

### 1.4 Model Files & Deployment

**Development (Laptop)**:
```
models/
├── yolo11s-pose.pt          # PyTorch weights (Ultralytics)
└── yolo11s-pose.onnx        # ONNX export for verification
```

**Production (Jetson)**:
```
models/
└── yolo11s-pose.engine      # TensorRT optimized
```

**Export Commands**:
```bash
# Laptop: Export to ONNX
yolo export model=yolo11s-pose.pt format=onnx

# Jetson: Export to TensorRT (run ON the Jetson)
yolo export model=yolo11s-pose.pt format=engine device=0
```

---

## 2. Speech-to-Text Model

### 2.1 Model Selection

| Model | Params | Size | RTF* (GPU) | RTF* (Orin) | Notes |
|-------|--------|------|------------|-------------|-------|
| **Whisper-small** | 244M | 461MB | 0.05 | 0.2-0.3 | Recommended |
| Whisper-base | 74M | 142MB | 0.02 | 0.1 | Faster, less accurate |
| Whisper-medium | 769M | 1.5GB | 0.15 | 0.5-0.8 | More accurate, slower |
| Distil-Whisper-small | 166M | 332MB | 0.03 | 0.15 | Faster, similar accuracy |

*RTF = Real-Time Factor (1.0 = takes as long as audio duration)

**Phase 1 Choice: Whisper-small (or Distil-Whisper-small)**
- English-only is fine → can use `.en` variants
- ~3-5 second utterances → transcription in <1 second
- Orin has enough VRAM to run alongside pose model

### 2.2 Input/Output Specification

**Input**:
```python
# Audio from microphone
audio: np.ndarray  # Shape: (samples,), float32, 16kHz mono
# Typical: 3-5 seconds of speech = 48,000-80,000 samples
```

**Output**:
```python
@dataclass
class TranscriptionResult:
    text: str                  # Transcribed text
    language: str              # Detected language (usually "en")
    confidence: float          # Average token probability
    duration: float            # Audio duration in seconds
    processing_time: float     # Time to transcribe
```

### 2.3 Model Files & Deployment

**Using faster-whisper (recommended)**:
```
models/
└── whisper-small-ct2/       # CTranslate2 format
    ├── model.bin
    ├── config.json
    └── vocabulary.json
```

**Conversion**:
```bash
# Convert from OpenAI format to CTranslate2
pip install faster-whisper
ct2-transformers-converter --model openai/whisper-small --output_dir models/whisper-small-ct2
```

### 2.4 STT Service Architecture (Log-Based)

**Architecture Decision**: STT runs as an independent service, writing to a log file that the MCP server reads. This decouples speech capture from Claude's processing loop.

**Data Flow**:
```
┌────────────┐     ┌─────────────────┐     ┌────────────────────────┐
│  Mic       │────▶│  STT Service    │────▶│  transcript.log        │
│  (always)  │     │  (systemd)      │     │  (append-only)         │
└────────────┘     └─────────────────┘     └────────────────────────┘
                                                      │
┌────────────┐                                        ▼
│  Headset   │────"<<<COMMIT>>>" marker──────────────▶│
│  Button    │                                        │
└────────────┘                                        ▼
                                           ┌────────────────────────┐
                                           │  MCP get_voice_input() │
                                           │  - tracks read pos     │
                                           │  - returns on commit   │
                                           └────────────────────────┘
```

**STT Service Implementation**:

```python
# stt_service.py - runs as systemd service
import asyncio
from faster_whisper import WhisperModel
from pathlib import Path
import sounddevice as sd
import numpy as np

TRANSCRIPT_LOG = Path.home() / ".slipstream" / "transcript.log"
SAMPLE_RATE = 16000
CHUNK_SECONDS = 3  # Process audio in 3-second chunks

class STTService:
    def __init__(self):
        self.model = WhisperModel("small", device="cuda", compute_type="float16")
        self.audio_buffer = []

    async def run(self):
        """Main loop: capture audio, transcribe, append to log."""
        TRANSCRIPT_LOG.parent.mkdir(parents=True, exist_ok=True)

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1) as stream:
            while True:
                # Capture audio chunk
                audio, _ = stream.read(int(SAMPLE_RATE * CHUNK_SECONDS))
                audio = audio.flatten().astype(np.float32)

                # Skip if silence (VAD)
                if np.abs(audio).max() < 0.01:
                    continue

                # Transcribe
                segments, _ = self.model.transcribe(audio, language="en")
                text = " ".join(seg.text for seg in segments).strip()

                if text:
                    # Append to log with timestamp
                    timestamp = datetime.now().isoformat(timespec='milliseconds')
                    with open(TRANSCRIPT_LOG, "a") as f:
                        f.write(f"{timestamp} {text}\n")

if __name__ == "__main__":
    service = STTService()
    asyncio.run(service.run())
```

**Button Handler**:

```python
# button_handler.py - monitors Bluetooth headset button
from evdev import InputDevice, ecodes
from pathlib import Path

TRANSCRIPT_LOG = Path.home() / ".slipstream" / "transcript.log"

def monitor_button(device_path: str = "/dev/input/event0"):
    """Write COMMIT marker when headset button pressed."""
    device = InputDevice(device_path)

    for event in device.read_loop():
        if event.type == ecodes.EV_KEY and event.value == 1:  # Key press
            timestamp = datetime.now().isoformat(timespec='milliseconds')
            with open(TRANSCRIPT_LOG, "a") as f:
                f.write(f"{timestamp} <<<COMMIT>>>\n")
```

**Log File Management**:

```python
# Log rotation - run daily via cron
# Keeps last 7 days of transcripts

import shutil
from datetime import datetime

LOG_PATH = Path.home() / ".slipstream" / "transcript.log"
ARCHIVE_DIR = Path.home() / ".slipstream" / "transcript_archive"

def rotate_log():
    if LOG_PATH.exists() and LOG_PATH.stat().st_size > 0:
        ARCHIVE_DIR.mkdir(exist_ok=True)
        archive_name = f"transcript_{datetime.now().strftime('%Y%m%d')}.log"
        shutil.move(LOG_PATH, ARCHIVE_DIR / archive_name)

        # Clean old archives (keep 7 days)
        for old_log in sorted(ARCHIVE_DIR.glob("transcript_*.log"))[:-7]:
            old_log.unlink()
```

**Systemd Service**:

```ini
# /etc/systemd/system/slipstream-stt.service
[Unit]
Description=Slipstream STT Service
After=network.target sound.target

[Service]
Type=simple
User=swim
ExecStart=/usr/bin/python3 /opt/slipstream/stt_service.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 2.5 Whisper Alternatives for Jetson

If Whisper is too slow on Orin:

| Alternative | Notes |
|-------------|-------|
| **whisper.cpp** | C++ implementation, very fast, CUDA support |
| **faster-whisper** | CTranslate2 backend, 4x faster than original |
| **whisper-jax** | JAX implementation, but Jetson support unclear |
| **NeMo Canary** | NVIDIA's own ASR, optimized for Jetson |

---

## 3. Laptop Verification Strategy

### 3.1 Hardware Requirements

**Minimum Laptop Specs**:
- NVIDIA GPU with 4GB+ VRAM (GTX 1060 or better)
- CUDA 11.x or 12.x
- 16GB RAM
- 50GB free disk space (models, test videos, conda env)

**Your Setup**: Laptop with GPU (verify CUDA version: `nvidia-smi`)

### 3.2 Test Data Requirements

#### Pose Estimation Test Data

**Option A: Record Your Own (Recommended)**
```
test_data/
├── videos/
│   ├── freestyle_10min_side.mp4      # Your 10-min video, side angle
│   ├── freestyle_2min_side.mp4       # Shorter clip for quick tests
│   └── freestyle_2min_overhead.mp4   # If testing angles
└── annotations/
    ├── freestyle_2min_side_strokes.json   # Manual stroke timestamps
    └── freestyle_2min_side_keypoints.json # Optional: manual keypoint annotations
```

**Annotation Format (strokes)**:
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

**Option B: Public Swimming Videos**
- YouTube: Search "freestyle swimming side view"
- Academic datasets: Swim dataset (limited availability)
- Still need manual stroke annotation

#### STT Test Data

```
test_data/
├── audio/
│   ├── stroke_rate_query.wav         # "What's my stroke rate?"
│   ├── session_commands.wav          # "Start session", "Stop"
│   └── noisy_pool_queries.wav        # Test with background noise
└── transcripts/
    └── expected_transcripts.json
```

### 3.3 Verification Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAPTOP VERIFICATION PIPELINE                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │  Test Video  │───▶│  Pose Model  │───▶│  Keypoint JSON   │   │
│  │  (10 min)    │    │  (YOLO11)    │    │  (every frame)   │   │
│  └──────────────┘    └──────────────┘    └──────────────────┘   │
│                                                   │              │
│                                                   ▼              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │  Ground      │───▶│   Compare    │◀───│  Stroke Detect   │   │
│  │  Truth       │    │   Results    │    │  Algorithm       │   │
│  └──────────────┘    └──────────────┘    └──────────────────┘   │
│                             │                                    │
│                             ▼                                    │
│                    ┌──────────────────┐                         │
│                    │  Accuracy Report │                         │
│                    │  - Stroke rate ±X │                        │
│                    │  - Detection %    │                        │
│                    │  - FPS achieved   │                        │
│                    └──────────────────┘                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.4 Verification Scripts

**Directory Structure**:
```
verification/
├── pose/
│   ├── run_pose_on_video.py      # Extract keypoints from video
│   ├── stroke_detector.py         # Peak detection algorithm
│   ├── evaluate_accuracy.py       # Compare to ground truth
│   └── benchmark_fps.py           # Measure inference speed
├── stt/
│   ├── run_whisper_on_audio.py   # Transcribe test audio
│   ├── evaluate_wer.py           # Word Error Rate calculation
│   └── benchmark_latency.py      # Measure transcription speed
├── mock/
│   ├── mock_pose_stream.py       # Simulate real-time pose data
│   └── mock_audio_stream.py      # Simulate microphone input
└── config.yaml                    # Model paths, thresholds
```

---

## 4. Post-Estimation Algorithms

These are **not ML models** - just Python signal processing.

### 4.1 Stroke Detection Algorithm

**Input**: Stream of wrist keypoints over time
**Output**: Stroke events (timestamps)

```python
class StrokeDetector:
    """Detect swim strokes from wrist keypoint trajectory."""

    def __init__(
        self,
        min_stroke_interval: float = 0.5,  # seconds
        smoothing_window: int = 5,          # frames
        peak_prominence: float = 0.1,       # relative to frame height
    ):
        self.buffer: deque[KeypointFrame] = deque(maxlen=300)  # 10s at 30fps

    def add_frame(self, keypoints: PoseResult) -> list[StrokeEvent]:
        """Process one frame, return any detected strokes."""
        # 1. Extract wrist Y positions
        left_wrist_y = keypoints.keypoints[9, 1]
        right_wrist_y = keypoints.keypoints[10, 1]

        # 2. Smooth signal
        # 3. Detect peaks (scipy.signal.find_peaks)
        # 4. Filter by minimum interval
        # 5. Return new stroke events
```

**Validation**: Run on test video, compare detected strokes to manual annotation.

### 4.2 Stroke Rate Calculation

**Input**: Stream of stroke events
**Output**: Strokes per minute (rolling average)

```python
class StrokeRateCalculator:
    """Calculate stroke rate from stroke events."""

    def __init__(self, window_seconds: float = 15.0):
        self.strokes: deque[float] = deque()  # timestamps
        self.window = window_seconds

    def add_stroke(self, timestamp: float) -> None:
        self.strokes.append(timestamp)
        self._prune_old()

    def get_rate(self) -> float:
        """Return strokes per minute."""
        if len(self.strokes) < 2:
            return 0.0
        duration = self.strokes[-1] - self.strokes[0]
        if duration < 1.0:
            return 0.0
        return (len(self.strokes) - 1) / duration * 60

    def get_trend(self) -> str:
        """Compare recent rate to earlier rate."""
        # Split window in half, compare rates
        # Return "increasing" | "stable" | "decreasing"
```

---

## 5. Mock Data Pipeline

For testing MCP server and dashboard **before** pose estimation is working.

### 5.1 Mock Pose Data

```python
# mock/mock_pose_stream.py
class MockPoseStream:
    """Generate fake pose keypoints for testing downstream components."""

    def __init__(self, stroke_rate: float = 55.0, noise: float = 0.05):
        self.stroke_rate = stroke_rate
        self.noise = noise

    def generate_frame(self, timestamp: float) -> PoseResult:
        """Generate one frame of keypoint data."""
        # Simulate sinusoidal arm motion
        phase = timestamp * (self.stroke_rate / 60) * 2 * np.pi
        wrist_y = 0.5 + 0.3 * np.sin(phase) + np.random.normal(0, self.noise)

        keypoints = np.zeros((17, 3))
        keypoints[9] = [0.3, wrist_y, 0.9]   # left wrist
        keypoints[10] = [0.7, wrist_y + 0.1, 0.9]  # right wrist
        # ... other keypoints

        return PoseResult(keypoints=keypoints, ...)
```

### 5.2 Mock Audio Data

```python
# mock/mock_audio_stream.py
class MockAudioStream:
    """Simulate microphone input with pre-recorded queries."""

    def __init__(self, queries: list[str]):
        self.queries = queries

    def get_next_utterance(self) -> TranscriptionResult:
        """Return next query (simulates STT output)."""
        text = self.queries.pop(0)
        return TranscriptionResult(text=text, confidence=0.95, ...)
```

---

## 6. Verification Checklist

### 6.1 Pose Estimation Verification

| Test | Pass Criteria | Status |
|------|---------------|--------|
| Model loads on laptop | No errors | ☐ |
| Process test video end-to-end | All frames processed | ☐ |
| Wrist keypoints detected | >90% of frames | ☐ |
| Keypoint confidence | >0.5 average for wrists | ☐ |
| Stroke detection accuracy | ±2 strokes/min vs ground truth | ☐ |
| Inference FPS (laptop) | >30 FPS | ☐ |
| ONNX export works | Model exports without error | ☐ |

### 6.2 STT Verification

| Test | Pass Criteria | Status |
|------|---------------|--------|
| Model loads on laptop | No errors | ☐ |
| Transcribe test queries | >95% accuracy on clean audio | ☐ |
| Transcribe noisy audio | >85% accuracy with pool noise | ☐ |
| Latency | <1s for 3s utterance | ☐ |
| CTranslate2 conversion | Model converts without error | ☐ |

### 6.3 Integration Verification

| Test | Pass Criteria | Status |
|------|---------------|--------|
| Mock pipeline end-to-end | Stroke rate returned correctly | ☐ |
| Real video + real algorithm | Matches ground truth | ☐ |
| Continuous 10-min test | No crashes, memory stable | ☐ |

---

## 7. Jetson Orin Deployment (After Laptop Verification)

### 7.1 Orin-Specific Steps

1. **TensorRT Export** (run on Orin):
   ```bash
   yolo export model=yolo11s-pose.pt format=engine device=0
   ```

2. **Whisper Deployment**:
   - Use `faster-whisper` with CUDA backend
   - Or compile `whisper.cpp` with CUDA support

3. **Memory Budget**:
   ```
   Total VRAM: 8GB (Orin Nano) or 16GB (Orin NX)

   YOLO11-Pose-s: ~500MB
   Whisper-small: ~500MB
   CUDA overhead: ~1GB
   Available for buffers: 6GB+
   ```

### 7.2 Performance Targets

| Component | Target | Notes |
|-----------|--------|-------|
| Pose estimation | >30 FPS | With TensorRT |
| STT latency | <500ms | For 3s utterance |
| Total pipeline | <100ms | Pose to stroke rate |
| Memory usage | <4GB | Leave room for OS/dashboard |

---

## 8. Development Order

```
Week 1: Environment Setup
├── Install CUDA, PyTorch on laptop
├── Download YOLO11-Pose-s, verify it loads
├── Download Whisper-small, verify transcription
└── Set up project structure

Week 2: Test Data
├── Record 10-min swimming video (your pool)
├── Manually annotate stroke timestamps (2-min clip)
├── Record voice command audio samples
└── Create ground truth files

Week 3: Pose Pipeline
├── Run pose model on test video
├── Implement stroke detection algorithm
├── Compare to ground truth, tune parameters
└── Document accuracy metrics

Week 4: STT Pipeline
├── Run Whisper on test audio
├── Measure latency, accuracy
├── Test with simulated pool noise
└── Document performance

Week 5: Integration
├── Build mock data generators
├── Connect pose → stroke detector → rate calculator
├── End-to-end test with real video
└── Create verification report
```

---

## Appendix: Model Download Links

**YOLO11-Pose**:
```bash
# Via Ultralytics (auto-downloads)
pip install ultralytics
python -c "from ultralytics import YOLO; YOLO('yolo11s-pose.pt')"
```

**Whisper**:
```bash
# Via faster-whisper
pip install faster-whisper
python -c "from faster_whisper import WhisperModel; WhisperModel('small')"
```
