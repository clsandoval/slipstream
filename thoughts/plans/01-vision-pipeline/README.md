# Branch 1: Vision Pipeline

**Branch**: `feature/vision-pipeline`
**Scope**: Pose Estimation + Stroke Detection Core
**Dependencies**: None (foundational branch)
**Complexity**: High

---

## Description

The computer vision foundation that captures video, extracts pose keypoints, detects swim strokes, and calculates stroke rate.

---

## Components

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

---

## File Structure

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

---

## Key Interfaces

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

---

## Success Criteria

- [ ] YOLO11-Pose processes video at >30 FPS on laptop GPU
- [ ] Wrist keypoints detected in >90% of frames
- [ ] Stroke rate within ±2 strokes/min of manual count
- [ ] Mock stream generates realistic synthetic data

---

## Downstream Dependencies

This branch is required by:
- Branch 4: `feature/swim-metrics`
- Branch 8: `feature/verification`
