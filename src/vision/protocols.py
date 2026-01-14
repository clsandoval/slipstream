"""Core protocols and data structures for vision pipeline."""

from dataclasses import dataclass
from typing import Iterator, Protocol

import numpy as np

# COCO Keypoint Indices (17 points)
NOSE_IDX = 0
LEFT_EYE_IDX = 1
RIGHT_EYE_IDX = 2
LEFT_EAR_IDX = 3
RIGHT_EAR_IDX = 4
LEFT_SHOULDER_IDX = 5
RIGHT_SHOULDER_IDX = 6
LEFT_ELBOW_IDX = 7
RIGHT_ELBOW_IDX = 8
LEFT_WRIST_IDX = 9
RIGHT_WRIST_IDX = 10
LEFT_HIP_IDX = 11
RIGHT_HIP_IDX = 12
LEFT_KNEE_IDX = 13
RIGHT_KNEE_IDX = 14
LEFT_ANKLE_IDX = 15
RIGHT_ANKLE_IDX = 16

NUM_KEYPOINTS = 17


@dataclass
class PoseResult:
    """Single frame pose estimation result."""

    keypoints: np.ndarray  # Shape: (17, 3) - x, y, confidence per keypoint
    bbox: tuple[int, int, int, int] | None  # x1, y1, x2, y2 or None if no detection
    confidence: float  # Overall detection confidence
    timestamp: float  # Frame timestamp in seconds
    frame_index: int  # Frame number in sequence


class PoseEstimatorProtocol(Protocol):
    """Protocol for pose estimation implementations."""

    def estimate(
        self, frame: np.ndarray, timestamp: float, frame_index: int
    ) -> PoseResult | None:
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
