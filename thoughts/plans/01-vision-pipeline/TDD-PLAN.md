# Vision Pipeline TDD Plan

**Branch**: `feature/vision-pipeline`
**Constraint**: No CUDA available on development laptop
**Strategy**: Mock pose estimation layer, test all downstream logic

---

## Architecture: Dependency Injection with Protocol

The key insight is that **YOLO11-Pose inference is the only component requiring GPU**. Everything downstream (stroke detection, rate calculation) is pure Python logic that can be fully tested with mock keypoint data.

**Note on TrendAnalyzer**: Intentionally omitted. Claude can derive trends from rate history directly—no need to pre-compute something the model can infer from `[58, 59, 60, 61, 62]`.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TESTABLE WITHOUT CUDA                              │
│                                                                              │
│  VideoSource ──▶ PoseEstimator ──▶ KeypointBuffer ──▶ StrokeDetector        │
│      │              │                    │                   │               │
│      │              │                    │                   ▼               │
│      │              │                    │            RateCalculator         │
│      │              │                    │                   │               │
│      │              │                    │                   ▼               │
│      │              │                    │              SwimState            │
│      │              │                    │         (includes rate_history)   │
│  ────┼──────────────┼────────────────────┼───────────────────────────────   │
│      │              │                    │                                   │
│  Mock: file/       Mock: returns      Filters by           Pure Python       │
│  synthetic         synthetic          confidence           logic, fully      │
│  frames            keypoints          (occlusion)          testable          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Core Interfaces & Data Structures

### 1.1 Define the Protocol (Interface)

```python
# src/vision/protocols.py

from typing import Protocol, Iterator
from dataclasses import dataclass
import numpy as np

@dataclass
class PoseResult:
    """Single frame pose estimation result."""
    keypoints: np.ndarray      # Shape: (17, 3) - x, y, confidence per keypoint
    bbox: tuple[int, int, int, int] | None  # x1, y1, x2, y2 or None if no detection
    confidence: float          # Overall detection confidence
    timestamp: float           # Frame timestamp in seconds
    frame_index: int           # Frame number in sequence


class PoseEstimatorProtocol(Protocol):
    """Protocol for pose estimation implementations."""

    def estimate(self, frame: np.ndarray, timestamp: float, frame_index: int) -> PoseResult | None:
        """Estimate pose from a single frame. Returns None if no person detected."""
        ...

    def is_available(self) -> bool:
        """Check if the estimator is ready (model loaded, GPU available, etc.)."""
        ...


class VideoSourceProtocol(Protocol):
    """Protocol for video input sources."""

    def frames(self) -> Iterator[tuple[np.ndarray, float, int]]:
        """Yield (frame, timestamp, frame_index) tuples."""
        ...

    @property
    def fps(self) -> float:
        """Source frame rate."""
        ...

    def close(self) -> None:
        """Release resources."""
        ...
```

### 1.2 Tests for Data Structures

```python
# tests/vision/test_data_structures.py

def test_pose_result_creation():
    """PoseResult can be created with valid keypoints."""

def test_pose_result_keypoint_shape():
    """Keypoints must be (17, 3) shape."""

def test_pose_result_wrist_indices():
    """Left wrist is index 9, right wrist is index 10 (COCO format)."""

def test_keypoint_confidence_range():
    """Each keypoint confidence is in [0, 1] range."""
```

---

## Keypoint Occlusion & Confidence Handling

YOLO11-Pose **always outputs 17 keypoints** regardless of visibility. The model uses a fixed COCO topology—indices never change.

```python
# keypoints shape is ALWAYS (17, 3) - never fewer points
# Format: [x, y, confidence] per keypoint

# Example: legs underwater (occluded)
keypoints[9]   # left wrist  → [245.3, 180.2, 0.94]  ✓ high confidence (visible)
keypoints[10]  # right wrist → [312.1, 195.7, 0.91]  ✓ high confidence (visible)
keypoints[15]  # left ankle  → [180.0, 450.0, 0.12]  ✗ low confidence (underwater)
keypoints[16]  # right ankle → [195.0, 455.0, 0.08]  ✗ low confidence (underwater)
```

**Filtering strategy**: Only use keypoints above confidence threshold:

```python
CONFIDENCE_THRESHOLD = 0.5
LEFT_WRIST = 9

def get_reliable_wrist_y(pose: PoseResult) -> float | None:
    """Return wrist Y if confident, None if occluded."""
    confidence = pose.keypoints[LEFT_WRIST, 2]
    if confidence >= CONFIDENCE_THRESHOLD:
        return pose.keypoints[LEFT_WRIST, 1]  # Y position
    return None  # Occluded this frame
```

This is actually ideal for swimming—wrists are above water during stroke (high confidence), while legs are often submerged (low confidence, ignored anyway).

---

## Phase 2: Mock Implementations

### 2.1 Mock Pose Estimator Factory

The factory pattern allows swapping implementations based on environment:

```python
# src/vision/pose_estimator.py

from enum import Enum
from typing import TYPE_CHECKING

class EstimatorBackend(Enum):
    YOLO = "yolo"           # Real YOLO11-Pose (requires CUDA)
    MOCK_SINE = "mock_sine" # Sine wave pattern (deterministic)
    MOCK_FILE = "mock_file" # Replay from recorded keypoints
    MOCK_RANDOM = "mock_random"  # Random but valid keypoints


def create_pose_estimator(
    backend: EstimatorBackend = EstimatorBackend.YOLO,
    **kwargs
) -> PoseEstimatorProtocol:
    """
    Factory function to create pose estimators.

    In tests/dev without CUDA, use MOCK_* backends.
    In production on Jetson, use YOLO backend.
    """
    if backend == EstimatorBackend.YOLO:
        from .backends.yolo_pose import YoloPoseEstimator
        return YoloPoseEstimator(**kwargs)
    elif backend == EstimatorBackend.MOCK_SINE:
        from .backends.mock_pose import SineWavePoseEstimator
        return SineWavePoseEstimator(**kwargs)
    elif backend == EstimatorBackend.MOCK_FILE:
        from .backends.mock_pose import FilePoseEstimator
        return FilePoseEstimator(**kwargs)
    elif backend == EstimatorBackend.MOCK_RANDOM:
        from .backends.mock_pose import RandomPoseEstimator
        return RandomPoseEstimator(**kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}")
```

### 2.2 Mock Implementations

```python
# src/vision/backends/mock_pose.py

class SineWavePoseEstimator:
    """
    Generates synthetic keypoints with sine wave motion for wrists.

    This simulates freestyle swimming with predictable stroke patterns:
    - Wrists move up/down in alternating sine waves
    - Configurable stroke rate (strokes per minute)
    - Deterministic output for repeatable tests
    """

    def __init__(
        self,
        stroke_rate: float = 60.0,  # strokes per minute
        frame_size: tuple[int, int] = (1920, 1080),
        seed: int | None = None,
    ):
        self.stroke_rate = stroke_rate
        self.frame_size = frame_size
        self._rng = np.random.default_rng(seed)

    def estimate(self, frame: np.ndarray, timestamp: float, frame_index: int) -> PoseResult:
        """Generate synthetic keypoints with sine wave wrist motion."""
        keypoints = self._generate_base_pose()
        keypoints = self._apply_stroke_motion(keypoints, timestamp)
        return PoseResult(
            keypoints=keypoints,
            bbox=(100, 100, 500, 400),
            confidence=0.95,
            timestamp=timestamp,
            frame_index=frame_index,
        )

    def _generate_base_pose(self) -> np.ndarray:
        """Generate a static base pose (person swimming position)."""
        # Returns (17, 3) array with base keypoint positions
        ...

    def _apply_stroke_motion(self, keypoints: np.ndarray, timestamp: float) -> np.ndarray:
        """Apply sine wave motion to wrists based on timestamp."""
        # Frequency from stroke rate: f = stroke_rate / 60 Hz
        freq = self.stroke_rate / 60.0

        # Left wrist (index 9) - sine wave
        phase_left = 2 * np.pi * freq * timestamp
        keypoints[9, 1] += 100 * np.sin(phase_left)  # Y oscillation

        # Right wrist (index 10) - opposite phase (alternating arms)
        phase_right = phase_left + np.pi
        keypoints[10, 1] += 100 * np.sin(phase_right)

        return keypoints

    def is_available(self) -> bool:
        return True  # Always available


class FilePoseEstimator:
    """
    Replays pre-recorded keypoints from a JSON file.

    Useful for:
    - Regression testing with real recorded data
    - Testing edge cases captured from real sessions
    """

    def __init__(self, keypoints_file: Path):
        self.keypoints_file = keypoints_file
        self._data = self._load_keypoints()
        self._index = 0

    def estimate(self, frame: np.ndarray, timestamp: float, frame_index: int) -> PoseResult | None:
        """Return next pre-recorded keypoints."""
        if self._index >= len(self._data):
            return None
        result = self._data[self._index]
        self._index += 1
        return result

    def is_available(self) -> bool:
        return self.keypoints_file.exists()
```

### 2.3 Tests for Mock Estimators

```python
# tests/vision/test_mock_pose.py

class TestSineWavePoseEstimator:
    def test_returns_valid_pose_result(self):
        """Mock returns PoseResult with correct keypoint shape."""

    def test_wrist_oscillates_over_time(self):
        """Wrist Y-position follows sine wave pattern."""

    def test_stroke_rate_affects_frequency(self):
        """Higher stroke rate = faster oscillation."""

    def test_deterministic_with_seed(self):
        """Same seed produces identical output."""

    def test_left_right_wrist_alternation(self):
        """Left and right wrists are 180° out of phase."""


class TestFilePoseEstimator:
    def test_loads_keypoints_from_file(self):
        """Can load and replay recorded keypoints."""

    def test_returns_none_when_exhausted(self):
        """Returns None after all keypoints consumed."""
```

---

## Phase 3: Keypoint Buffer

### 3.1 Implementation

```python
# src/vision/keypoint_buffer.py

# COCO keypoint indices
LEFT_WRIST = 9
RIGHT_WRIST = 10

class KeypointBuffer:
    """
    Circular buffer storing recent keypoint history.

    Stores wrist positions for stroke detection algorithm.
    Default size: 300 frames (~10 seconds at 30 FPS)

    Handles occlusion via confidence filtering—low confidence
    keypoints are skipped (None stored), and downstream
    algorithms handle gaps gracefully.
    """

    def __init__(
        self,
        max_size: int = 300,
        confidence_threshold: float = 0.5,
    ):
        self.max_size = max_size
        self.confidence_threshold = confidence_threshold
        self._left_wrist_y: deque[float | None] = deque(maxlen=max_size)
        self._right_wrist_y: deque[float | None] = deque(maxlen=max_size)
        self._timestamps: deque[float] = deque(maxlen=max_size)

    def add(self, pose: PoseResult) -> None:
        """
        Add a pose result to the buffer.

        Low-confidence wrists are stored as None.
        """
        self._timestamps.append(pose.timestamp)

        # Left wrist - check confidence before storing
        left_conf = pose.keypoints[LEFT_WRIST, 2]
        if left_conf >= self.confidence_threshold:
            self._left_wrist_y.append(pose.keypoints[LEFT_WRIST, 1])
        else:
            self._left_wrist_y.append(None)  # Occluded

        # Right wrist
        right_conf = pose.keypoints[RIGHT_WRIST, 2]
        if right_conf >= self.confidence_threshold:
            self._right_wrist_y.append(pose.keypoints[RIGHT_WRIST, 1])
        else:
            self._right_wrist_y.append(None)  # Occluded

    def get_wrist_trajectory(self, wrist: str = "left") -> tuple[np.ndarray, np.ndarray]:
        """
        Get Y-positions and timestamps for specified wrist.

        Returns only frames where wrist was confident (not occluded).
        Returns (positions, timestamps) tuple with aligned arrays.
        """
        data = self._left_wrist_y if wrist == "left" else self._right_wrist_y

        # Filter out None values (occluded frames)
        valid_indices = [i for i, v in enumerate(data) if v is not None]
        positions = np.array([data[i] for i in valid_indices])
        timestamps = np.array([self._timestamps[i] for i in valid_indices])

        return positions, timestamps

    def clear(self) -> None:
        """Clear all buffered data."""

    def __len__(self) -> int:
        """Number of frames in buffer (including occluded)."""
```

### 3.2 Tests

```python
# tests/vision/test_keypoint_buffer.py

class TestKeypointBuffer:
    def test_add_and_retrieve(self):
        """Can add poses and retrieve wrist trajectory."""

    def test_circular_buffer_overflow(self):
        """Old frames discarded when buffer full."""

    def test_wrist_trajectory_shape(self):
        """Trajectory array matches number of confident frames."""

    def test_timestamps_aligned_with_positions(self):
        """Timestamps correspond to correct positions."""

    def test_clear_empties_buffer(self):
        """Clear removes all data."""

    def test_low_confidence_keypoints_filtered(self):
        """Low confidence wrists stored as None and excluded from trajectory."""

    def test_handles_all_occluded(self):
        """Returns empty arrays when all frames are occluded."""

    def test_mixed_confidence_frames(self):
        """Correctly handles mix of confident and occluded frames."""
```

---

## Phase 4: Stroke Detector

### 4.1 Implementation

```python
# src/vision/stroke_detector.py

@dataclass
class StrokeEvent:
    """A detected stroke."""
    timestamp: float
    wrist: str  # "left" | "right"
    confidence: float


class StrokeDetector:
    """
    Detects stroke cycles from wrist trajectory.

    Algorithm:
    1. Track wrist Y-position over time
    2. Detect peaks (local maxima) in Y-position
    3. Each peak = one stroke completed
    4. Filter by minimum peak prominence to avoid noise
    """

    def __init__(
        self,
        min_peak_prominence: float = 30.0,  # pixels
        min_peak_distance: float = 0.3,     # seconds between strokes
    ):
        self.min_peak_prominence = min_peak_prominence
        self.min_peak_distance = min_peak_distance

    def detect_strokes(
        self,
        wrist_y: np.ndarray,
        timestamps: np.ndarray,
    ) -> list[StrokeEvent]:
        """
        Detect strokes from wrist trajectory.

        Uses scipy.signal.find_peaks for peak detection.

        Note: wrist_y and timestamps are pre-filtered (no None values)
        from KeypointBuffer.get_wrist_trajectory().
        """
```

### 4.2 Tests

```python
# tests/vision/test_stroke_detector.py

class TestStrokeDetector:
    def test_detects_peaks_in_sine_wave(self):
        """Detects correct number of peaks in known sine wave."""
        # Generate 10 seconds of data at 60 strokes/min = 10 strokes
        # Detector should find ~10 peaks

    def test_ignores_low_prominence_peaks(self):
        """Small oscillations below threshold ignored."""

    def test_min_distance_filters_noise(self):
        """Peaks too close together are filtered."""

    def test_stroke_timestamps_accurate(self):
        """Detected stroke times match actual peak times."""

    def test_handles_incomplete_strokes(self):
        """Partial strokes at buffer edges handled correctly."""

    def test_no_strokes_when_stationary(self):
        """No false positives when wrist stationary."""

    @pytest.mark.parametrize("stroke_rate", [30, 45, 60, 75, 90])
    def test_various_stroke_rates(self, stroke_rate):
        """Accurately detects strokes across range of rates."""
```

---

## Phase 5: Rate Calculator

### 5.1 Implementation

```python
# src/vision/rate_calculator.py

@dataclass
class RateSample:
    """A single stroke rate measurement."""
    timestamp: float
    rate: float


class RateCalculator:
    """
    Calculates stroke rate from detected strokes.

    Uses a rolling window (default 15 seconds) to smooth rate calculation.
    Maintains rate history for Claude/dashboard to analyze trends.
    """

    def __init__(
        self,
        window_seconds: float = 15.0,
        history_max_samples: int = 60,  # ~5 min at 5s intervals
    ):
        self.window_seconds = window_seconds
        self._stroke_times: list[float] = []
        self._rate_history: deque[RateSample] = deque(maxlen=history_max_samples)
        self._last_sample_time: float = 0
        self._sample_interval: float = 5.0  # Record rate every 5 seconds

    def add_stroke(self, timestamp: float) -> None:
        """Record a stroke event."""

    def get_rate(self, current_time: float) -> float:
        """
        Calculate current stroke rate in strokes/minute.

        Only considers strokes within the rolling window.
        Also records to rate_history at sample_interval.
        """

    def get_rate_history(self, last_n: int | None = None) -> list[RateSample]:
        """
        Get recent rate samples for trend analysis.

        Claude can derive trends from this: [58, 59, 60, 61, 62] → increasing
        Dashboard can plot this as a sparkline.
        """

    def get_stroke_count(self) -> int:
        """Total strokes recorded in session."""

    def reset(self) -> None:
        """Clear all stroke history and rate samples."""
```

### 5.2 Tests

```python
# tests/vision/test_rate_calculator.py

class TestRateCalculator:
    def test_rate_calculation_accuracy(self):
        """Rate calculated correctly from known stroke times."""
        # Add strokes at exactly 1 per second = 60/min

    def test_rolling_window_excludes_old_strokes(self):
        """Strokes outside window not counted in rate."""

    def test_rate_zero_with_no_strokes(self):
        """Returns 0 when no strokes recorded."""

    def test_rate_with_single_stroke(self):
        """Handles edge case of single stroke in window."""

    def test_stroke_count_cumulative(self):
        """Count includes all strokes, not just window."""

    def test_reset_clears_history(self):
        """Reset clears all strokes and rate history."""

    def test_rate_history_recorded(self):
        """Rate samples recorded at regular intervals."""

    def test_rate_history_max_size(self):
        """Old rate samples discarded when history full."""

    @pytest.mark.parametrize("expected_rate", [30, 45, 60, 75, 90])
    def test_various_rates(self, expected_rate):
        """Accurately calculates various stroke rates."""
```

---

## Phase 6: SwimState (State Store)

### 6.1 Implementation

```python
# src/vision/state_store.py

@dataclass
class SwimState:
    """Core state for a swimming session."""
    session_active: bool = False
    session_start: datetime | None = None
    stroke_count: int = 0
    stroke_rate: float = 0.0
    rate_history: list[RateSample] = field(default_factory=list)  # For trend analysis
    last_stroke_time: datetime | None = None
    pose_detected: bool = False
    is_swimming: bool = False

    # Note: No trend field - Claude derives trends from rate_history


class StateStore:
    """
    Thread-safe state container for swim session data.

    Provides atomic updates and read access for:
    - Vision pipeline (writes state)
    - MCP server (reads state)
    - WebSocket publisher (reads state)
    """

    def __init__(self):
        self._state = SwimState()
        self._lock = threading.RLock()

    def get_state(self) -> SwimState:
        """Get a snapshot of current state."""

    def update(self, **kwargs) -> None:
        """Update state fields atomically."""

    def start_session(self) -> None:
        """Initialize a new session."""

    def end_session(self) -> SwimState:
        """End session and return final state."""
```

### 6.2 Tests

```python
# tests/vision/test_state_store.py

class TestSwimState:
    def test_default_values(self):
        """SwimState has sensible defaults."""

    def test_rate_history_default_empty(self):
        """Rate history starts as empty list."""


class TestStateStore:
    def test_initial_state(self):
        """Store starts with default state."""

    def test_atomic_update(self):
        """Updates are atomic and complete."""

    def test_start_session(self):
        """Start session initializes correctly."""

    def test_end_session_returns_final_state(self):
        """End session returns snapshot and resets."""

    def test_thread_safety(self):
        """Concurrent access is safe."""
```

---

## Phase 7: Integration - Vision Pipeline

### 7.1 Pipeline Implementation

```python
# src/vision/pipeline.py

class VisionPipeline:
    """
    Main vision processing pipeline.

    Orchestrates: video → pose estimation → stroke detection → state updates
    """

    def __init__(
        self,
        pose_estimator: PoseEstimatorProtocol,
        state_store: StateStore,
        buffer_size: int = 300,
        rate_window: float = 15.0,
        confidence_threshold: float = 0.5,
    ):
        self.pose_estimator = pose_estimator
        self.state_store = state_store
        self.buffer = KeypointBuffer(
            max_size=buffer_size,
            confidence_threshold=confidence_threshold,
        )
        self.stroke_detector = StrokeDetector()
        self.rate_calculator = RateCalculator(window_seconds=rate_window)

    def process_frame(self, frame: np.ndarray, timestamp: float, frame_index: int) -> None:
        """Process a single video frame."""
        # 1. Estimate pose
        pose = self.pose_estimator.estimate(frame, timestamp, frame_index)

        # 2. Update buffer (handles confidence filtering internally)
        if pose:
            self.buffer.add(pose)

        # 3. Detect strokes (trajectory is pre-filtered for confident keypoints)
        wrist_y, wrist_timestamps = self.buffer.get_wrist_trajectory()
        strokes = self.stroke_detector.detect_strokes(wrist_y, wrist_timestamps)

        # 4. Update rate calculator
        for stroke in strokes:
            self.rate_calculator.add_stroke(stroke.timestamp)

        # 5. Calculate rate (also updates internal rate_history)
        rate = self.rate_calculator.get_rate(timestamp)

        # 6. Update state (includes rate_history for Claude/dashboard)
        self.state_store.update(
            pose_detected=pose is not None,
            stroke_count=self.rate_calculator.get_stroke_count(),
            stroke_rate=rate,
            rate_history=self.rate_calculator.get_rate_history(),
        )

    def run(self, video_source: VideoSourceProtocol) -> None:
        """Run pipeline on video source until exhausted."""
        for frame, timestamp, frame_index in video_source.frames():
            self.process_frame(frame, timestamp, frame_index)
```

### 7.2 Integration Tests (All Mock)

```python
# tests/vision/test_pipeline_integration.py

class TestVisionPipelineIntegration:
    """
    Full pipeline integration tests using mock pose estimator.

    These tests validate the entire pipeline works end-to-end
    WITHOUT requiring CUDA or real model inference.
    """

    @pytest.fixture
    def mock_pipeline(self):
        """Pipeline with sine wave mock estimator."""
        estimator = SineWavePoseEstimator(stroke_rate=60.0, seed=42)
        state_store = StateStore()
        return VisionPipeline(pose_estimator=estimator, state_store=state_store)

    def test_pipeline_processes_frames(self, mock_pipeline):
        """Pipeline processes frames without error."""

    def test_stroke_count_accumulates(self, mock_pipeline):
        """Stroke count increases over time."""

    def test_stroke_rate_accuracy(self, mock_pipeline):
        """
        Calculated stroke rate matches mock's configured rate.

        Mock at 60 strokes/min → pipeline should report ~60 strokes/min
        """

    def test_rate_history_populated(self, mock_pipeline):
        """Rate history grows over time for trend analysis."""

    def test_state_updates_each_frame(self, mock_pipeline):
        """State store updated after each frame processed."""

    @pytest.mark.parametrize("mock_rate,expected_range", [
        (30, (28, 32)),
        (60, (58, 62)),
        (90, (88, 92)),
    ])
    def test_rate_accuracy_across_speeds(self, mock_rate, expected_range):
        """Pipeline accurately detects various stroke rates."""
        estimator = SineWavePoseEstimator(stroke_rate=mock_rate, seed=42)
        # ... run pipeline, assert rate in expected_range
```

---

## Phase 8: Video Source Mocks

### 8.1 Mock Video Sources

```python
# src/vision/video_capture.py

class MockVideoSource:
    """
    Generates blank frames at specified FPS.

    Used with mock pose estimators that don't need real frame data.
    """

    def __init__(self, fps: float = 30.0, duration: float = 10.0):
        self._fps = fps
        self.duration = duration
        self.total_frames = int(fps * duration)

    def frames(self) -> Iterator[tuple[np.ndarray, float, int]]:
        """Yield synthetic frames."""
        for i in range(self.total_frames):
            timestamp = i / self._fps
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            yield frame, timestamp, i

    @property
    def fps(self) -> float:
        return self._fps

    def close(self) -> None:
        pass


class FileVideoSource:
    """
    Reads frames from a video file.

    For testing with real recorded video (when available).
    """

    def __init__(self, path: Path):
        self.path = path
        self._cap = cv2.VideoCapture(str(path))

    # ... implementation
```

---

## Test Execution Order

Run tests in dependency order:

```bash
# Phase 1: Data structures (no dependencies)
uv run pytest tests/vision/test_data_structures.py -v

# Phase 2: Mocks (depend on data structures)
uv run pytest tests/vision/test_mock_pose.py -v

# Phase 3-5: Components (can run in parallel)
uv run pytest tests/vision/test_keypoint_buffer.py -v
uv run pytest tests/vision/test_stroke_detector.py -v
uv run pytest tests/vision/test_rate_calculator.py -v

# Phase 6: State store
uv run pytest tests/vision/test_state_store.py -v

# Phase 7: Integration (depends on all above)
uv run pytest tests/vision/test_pipeline_integration.py -v

# All tests
uv run pytest tests/vision/ -v
```

---

## What's Tested vs What's Deferred

### Fully Tested Without CUDA

| Component | Test Coverage |
|-----------|---------------|
| PoseResult dataclass | Shape validation, field access, confidence handling |
| MockPoseEstimator variants | Deterministic output, sine wave patterns |
| KeypointBuffer | Circular buffer, confidence filtering, occlusion handling |
| StrokeDetector | Peak detection accuracy |
| RateCalculator | Rate math, rolling window, rate history |
| StateStore | Thread safety, atomic updates |
| VisionPipeline | Full integration with mocks |

### Deferred Until Jetson/CUDA Available

| Component | Why Deferred |
|-----------|--------------|
| YoloPoseEstimator | Requires CUDA for TensorRT |
| RTSPVideoSource | Requires camera hardware |
| Real video accuracy | Need ground truth annotations |
| FPS benchmarks | Hardware-specific |

### Intentionally Omitted

| Component | Reason |
|-----------|--------|
| TrendAnalyzer | Claude can derive trends from rate_history directly |

---

## File Structure After TDD

```
src/vision/
├── __init__.py
├── protocols.py           # PoseEstimatorProtocol, VideoSourceProtocol, PoseResult
├── pose_estimator.py      # Factory: create_pose_estimator()
├── keypoint_buffer.py     # KeypointBuffer (with confidence filtering)
├── stroke_detector.py     # StrokeDetector, StrokeEvent
├── rate_calculator.py     # RateCalculator, RateSample
├── state_store.py         # SwimState, StateStore
├── video_capture.py       # MockVideoSource, FileVideoSource
├── pipeline.py            # VisionPipeline (orchestrator)
└── backends/
    ├── __init__.py
    ├── mock_pose.py       # SineWavePoseEstimator, FilePoseEstimator
    └── yolo_pose.py       # YoloPoseEstimator (CUDA required)

tests/vision/
├── __init__.py
├── conftest.py            # Shared fixtures
├── test_data_structures.py
├── test_mock_pose.py
├── test_keypoint_buffer.py
├── test_stroke_detector.py
├── test_rate_calculator.py
├── test_state_store.py
└── test_pipeline_integration.py
```

---

## Implementation Order (TDD Red-Green-Refactor)

For each component:

1. **RED**: Write failing test first
2. **GREEN**: Write minimal code to pass
3. **REFACTOR**: Clean up while tests pass

Suggested order:

1. `protocols.py` + `test_data_structures.py`
2. `backends/mock_pose.py` + `test_mock_pose.py`
3. `keypoint_buffer.py` + `test_keypoint_buffer.py`
4. `stroke_detector.py` + `test_stroke_detector.py`
5. `rate_calculator.py` + `test_rate_calculator.py`
6. `state_store.py` + `test_state_store.py`
7. `video_capture.py` (mocks only)
8. `pipeline.py` + `test_pipeline_integration.py`
9. `pose_estimator.py` (factory, connects everything)

---

## Appendix A: YOLO11-Pose Integration Guide

**Reference**: This section documents the actual Ultralytics YOLO11-Pose API to ensure mocks align with production implementation.

### A.1 YOLO11-Pose API Overview

```python
from ultralytics import YOLO

# Load model (various sizes: n, s, m, l, x)
model = YOLO("yolo11n-pose.pt")  # nano - fastest
model = YOLO("yolo11s-pose.pt")  # small
model = YOLO("yolo11m-pose.pt")  # medium - recommended for Jetson

# Inference returns list of Results objects
results = model(frame)  # frame is np.ndarray BGR (H, W, 3)

# Or with explicit parameters
results = model.predict(
    source=frame,
    conf=0.5,        # confidence threshold
    iou=0.7,         # NMS IoU threshold
    device=0,        # GPU device (0 for first CUDA device)
    verbose=False,   # suppress logging
)
```

### A.2 Results Object Structure

```python
# results is a list (one Result per input image)
result = results[0]

# Keypoints object
result.keypoints.xy      # Shape: (N, 17, 2) - absolute pixel coords
result.keypoints.xyn     # Shape: (N, 17, 2) - normalized [0,1]
result.keypoints.conf    # Shape: (N, 17) - per-keypoint confidence
result.keypoints.data    # Shape: (N, 17, 3) - [x, y, conf] combined

# Bounding boxes
result.boxes.xyxy        # Shape: (N, 4) - [x1, y1, x2, y2]
result.boxes.conf        # Shape: (N,) - detection confidence

# Convert all tensors to numpy
result = result.numpy()  # IMPORTANT: call before accessing .xy etc.
```

**Note**: `N` = number of detected people. For swimming (single person), select the detection with highest confidence.

### A.3 COCO Keypoint Indices (17 points)

```
Index | Body Part        | Used for Stroke Detection
------|------------------|---------------------------
  0   | nose             |
  1   | left_eye         |
  2   | right_eye        |
  3   | left_ear         |
  4   | right_ear        |
  5   | left_shoulder    | ✓ (stroke phase detection)
  6   | right_shoulder   | ✓ (stroke phase detection)
  7   | left_elbow       |
  8   | right_elbow      |
  9   | left_wrist       | ✓ PRIMARY - stroke detection
 10   | right_wrist      | ✓ PRIMARY - stroke detection
 11   | left_hip         |
 12   | right_hip        |
 13   | left_knee        |
 14   | right_knee       |
 15   | left_ankle       |
 16   | right_ankle      |
```

### A.4 Real YoloPoseEstimator Implementation

```python
# src/vision/backends/yolo_pose.py

from pathlib import Path
import numpy as np

class YoloPoseEstimator:
    """
    Real YOLO11-Pose implementation for Jetson/CUDA.

    Implements PoseEstimatorProtocol - same interface as mocks.
    """

    # Constants matching COCO format
    LEFT_WRIST_IDX = 9
    RIGHT_WRIST_IDX = 10
    NUM_KEYPOINTS = 17

    def __init__(
        self,
        model_path: Path | str = "yolo11m-pose.pt",
        conf_threshold: float = 0.5,
        device: int | str = 0,  # 0 for CUDA, "cpu" for CPU
    ):
        self.conf_threshold = conf_threshold
        self.device = device
        self._model = None
        self._model_path = model_path

    def _load_model(self):
        """Lazy load model on first use."""
        if self._model is None:
            from ultralytics import YOLO
            self._model = YOLO(str(self._model_path))

    def estimate(
        self,
        frame: np.ndarray,
        timestamp: float,
        frame_index: int
    ) -> PoseResult | None:
        """
        Run pose estimation on a single frame.

        Args:
            frame: BGR image as numpy array (H, W, 3)
            timestamp: Frame timestamp in seconds
            frame_index: Frame number in sequence

        Returns:
            PoseResult if person detected, None otherwise
        """
        self._load_model()

        # Run inference
        results = self._model.predict(
            source=frame,
            conf=self.conf_threshold,
            device=self.device,
            verbose=False,
        )
        result = results[0].numpy()  # Convert tensors to numpy

        # No detection
        if result.keypoints is None or len(result.keypoints.xy) == 0:
            return None

        # Multi-person: select highest confidence detection
        if len(result.boxes.conf) > 1:
            best_idx = int(np.argmax(result.boxes.conf))
        else:
            best_idx = 0

        # Extract keypoints: shape (17, 3) with [x, y, conf]
        keypoints = result.keypoints.data[best_idx]  # (17, 3)

        # Extract bounding box
        bbox_xyxy = result.boxes.xyxy[best_idx]  # (4,)
        bbox = tuple(int(v) for v in bbox_xyxy)  # (x1, y1, x2, y2)

        # Overall detection confidence
        confidence = float(result.boxes.conf[best_idx])

        return PoseResult(
            keypoints=keypoints,  # np.ndarray shape (17, 3)
            bbox=bbox,
            confidence=confidence,
            timestamp=timestamp,
            frame_index=frame_index,
        )

    def is_available(self) -> bool:
        """Check if CUDA is available for inference."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
```

### A.5 Key Differences: Mock vs Real

| Aspect | Mock (SineWavePoseEstimator) | Real (YoloPoseEstimator) |
|--------|------------------------------|--------------------------|
| Input frame | Ignored (uses timestamp only) | Processed by model |
| Output keypoints | Synthetic sine wave | From YOLO inference |
| `is_available()` | Always `True` | Checks `torch.cuda.is_available()` |
| Determinism | Deterministic with seed | Non-deterministic |
| Performance | Instant | ~10-30ms per frame |

### A.6 TensorRT Optimization (Jetson)

For production on Jetson, export to TensorRT:

```python
from ultralytics import YOLO

model = YOLO("yolo11m-pose.pt")
model.export(format="engine", device=0)  # Creates yolo11m-pose.engine

# Use the .engine file for faster inference
model = YOLO("yolo11m-pose.engine")
```

### A.7 Validation Test (Run on CUDA Device)

```python
# tests/vision/test_yolo_pose_integration.py

import pytest
import numpy as np

# Skip if no CUDA
cuda_available = pytest.mark.skipif(
    not torch.cuda.is_available(),
    reason="CUDA not available"
)

@cuda_available
class TestYoloPoseEstimator:
    def test_returns_valid_pose_result(self):
        """Real model returns PoseResult with correct shape."""
        from src.vision.backends.yolo_pose import YoloPoseEstimator

        estimator = YoloPoseEstimator()
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

        result = estimator.estimate(frame, timestamp=0.0, frame_index=0)

        # May be None if no person in random noise
        if result is not None:
            assert result.keypoints.shape == (17, 3)
            assert 0.0 <= result.confidence <= 1.0

    def test_keypoint_indices_match_coco(self):
        """Verify wrist indices are correct."""
        assert YoloPoseEstimator.LEFT_WRIST_IDX == 9
        assert YoloPoseEstimator.RIGHT_WRIST_IDX == 10

    def test_interface_matches_mock(self):
        """Same interface as mock implementations."""
        from src.vision.backends.yolo_pose import YoloPoseEstimator
        from src.vision.backends.mock_pose import SineWavePoseEstimator
        from src.vision.protocols import PoseEstimatorProtocol

        # Both should satisfy the protocol
        yolo = YoloPoseEstimator()
        mock = SineWavePoseEstimator()

        # Duck typing check - both have same methods
        assert hasattr(yolo, 'estimate')
        assert hasattr(yolo, 'is_available')
        assert hasattr(mock, 'estimate')
        assert hasattr(mock, 'is_available')
```

---

## Notes

- **Deterministic mocks are key**: SineWavePoseEstimator with fixed seed allows exact assertions
- **Parameterized tests**: Use `@pytest.mark.parametrize` to test range of stroke rates
- **Integration tests validate wiring**: Ensure components work together correctly
- **Real model testing on Jetson**: Once hardware available, add `YoloPoseEstimator` and run same integration tests with real inference
- **Confidence filtering**: KeypointBuffer handles occlusion by storing None for low-confidence keypoints
- **Rate history for trends**: Claude derives trends from `rate_history` array—no pre-computation needed
