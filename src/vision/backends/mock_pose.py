"""Mock pose estimators for testing without CUDA."""

import json
from pathlib import Path

import numpy as np

from src.vision.protocols import (
    LEFT_WRIST_IDX,
    NUM_KEYPOINTS,
    PoseResult,
    RIGHT_WRIST_IDX,
)


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
        frame_size: tuple[int, int] = (640, 480),  # width, height
        seed: int | None = None,
        amplitude: float = 100.0,  # pixels of oscillation
    ):
        self.stroke_rate = stroke_rate
        self.frame_size = frame_size
        self.amplitude = amplitude
        self._rng = np.random.default_rng(seed)
        self._base_pose = self._generate_base_pose()

    def estimate(
        self, frame: np.ndarray, timestamp: float, frame_index: int
    ) -> PoseResult:
        """Generate synthetic keypoints with sine wave wrist motion."""
        keypoints = self._base_pose.copy()
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
        keypoints = np.zeros((NUM_KEYPOINTS, 3), dtype=np.float32)

        width, height = self.frame_size
        cx, cy = width // 2, height // 2

        # Base positions for swimming pose (horizontal position)
        positions = [
            (cx, cy - 50),  # 0: nose
            (cx - 10, cy - 60),  # 1: left_eye
            (cx + 10, cy - 60),  # 2: right_eye
            (cx - 20, cy - 55),  # 3: left_ear
            (cx + 20, cy - 55),  # 4: right_ear
            (cx - 80, cy - 30),  # 5: left_shoulder
            (cx + 80, cy - 30),  # 6: right_shoulder
            (cx - 120, cy),  # 7: left_elbow
            (cx + 120, cy),  # 8: right_elbow
            (cx - 160, cy + 30),  # 9: left_wrist
            (cx + 160, cy + 30),  # 10: right_wrist
            (cx - 40, cy + 80),  # 11: left_hip
            (cx + 40, cy + 80),  # 12: right_hip
            (cx - 50, cy + 150),  # 13: left_knee
            (cx + 50, cy + 150),  # 14: right_knee
            (cx - 60, cy + 220),  # 15: left_ankle
            (cx + 60, cy + 220),  # 16: right_ankle
        ]

        for i, (x, y) in enumerate(positions):
            keypoints[i] = [x, y, 0.95]

        return keypoints

    def _apply_stroke_motion(
        self, keypoints: np.ndarray, timestamp: float
    ) -> np.ndarray:
        """Apply sine wave motion to wrists based on timestamp."""
        # Frequency from stroke rate: f = stroke_rate / 60 Hz
        freq = self.stroke_rate / 60.0

        # Left wrist (index 9) - sine wave
        phase_left = 2 * np.pi * freq * timestamp
        keypoints[LEFT_WRIST_IDX, 1] += self.amplitude * np.sin(phase_left)

        # Right wrist (index 10) - opposite phase (alternating arms)
        phase_right = phase_left + np.pi
        keypoints[RIGHT_WRIST_IDX, 1] += self.amplitude * np.sin(phase_right)

        return keypoints

    def is_available(self) -> bool:
        """Always available (no hardware requirements)."""
        return True


class FilePoseEstimator:
    """
    Replays pre-recorded keypoints from a JSON file.

    Useful for:
    - Regression testing with real recorded data
    - Testing edge cases captured from real sessions
    """

    def __init__(self, keypoints_file: Path):
        self.keypoints_file = Path(keypoints_file)
        self._data: list[PoseResult] = []
        self._index = 0
        self._loaded = False

    def _load_keypoints(self) -> None:
        """Load keypoints from JSON file."""
        if self._loaded or not self.keypoints_file.exists():
            return

        with open(self.keypoints_file) as f:
            raw_data = json.load(f)

        self._data = []
        for item in raw_data:
            keypoints = np.array(item["keypoints"], dtype=np.float32)
            bbox = tuple(item["bbox"]) if item.get("bbox") else None
            self._data.append(
                PoseResult(
                    keypoints=keypoints,
                    bbox=bbox,
                    confidence=item["confidence"],
                    timestamp=item["timestamp"],
                    frame_index=item["frame_index"],
                )
            )
        self._loaded = True

    def estimate(
        self, frame: np.ndarray, timestamp: float, frame_index: int
    ) -> PoseResult | None:
        """Return next pre-recorded keypoints."""
        self._load_keypoints()

        if self._index >= len(self._data):
            return None

        result = self._data[self._index]
        self._index += 1
        return result

    def is_available(self) -> bool:
        """Check if keypoints file exists."""
        return self.keypoints_file.exists()


class RandomPoseEstimator:
    """
    Generates random but valid keypoints.

    Useful for stress testing and edge case exploration.
    """

    def __init__(
        self,
        frame_size: tuple[int, int] = (640, 480),
        seed: int | None = None,
    ):
        self.frame_size = frame_size
        self._rng = np.random.default_rng(seed)

    def estimate(
        self, frame: np.ndarray, timestamp: float, frame_index: int
    ) -> PoseResult:
        """Generate random keypoints within frame bounds."""
        width, height = self.frame_size

        keypoints = np.zeros((NUM_KEYPOINTS, 3), dtype=np.float32)

        # Generate random positions within frame
        keypoints[:, 0] = self._rng.uniform(0, width, NUM_KEYPOINTS)
        keypoints[:, 1] = self._rng.uniform(0, height, NUM_KEYPOINTS)
        keypoints[:, 2] = self._rng.uniform(0.5, 1.0, NUM_KEYPOINTS)

        # Random bounding box
        x1 = int(self._rng.uniform(0, width // 2))
        y1 = int(self._rng.uniform(0, height // 2))
        x2 = int(self._rng.uniform(width // 2, width))
        y2 = int(self._rng.uniform(height // 2, height))

        return PoseResult(
            keypoints=keypoints,
            bbox=(x1, y1, x2, y2),
            confidence=float(self._rng.uniform(0.7, 1.0)),
            timestamp=timestamp,
            frame_index=frame_index,
        )

    def is_available(self) -> bool:
        """Always available (no hardware requirements)."""
        return True
