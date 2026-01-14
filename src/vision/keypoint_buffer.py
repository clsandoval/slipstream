"""Keypoint buffer for storing recent pose history."""

from collections import deque

import numpy as np

from src.vision.protocols import LEFT_WRIST_IDX, PoseResult, RIGHT_WRIST_IDX


class KeypointBuffer:
    """
    Circular buffer storing recent keypoint history.

    Stores wrist positions for stroke detection algorithm.
    Default size: 300 frames (~10 seconds at 30 FPS)

    Handles occlusion via confidence filtering—low confidence
    keypoints are skipped (None stored), and downstream
    algorithms handle gaps gracefully.
    """

    def __init__(self, max_size: int = 300, min_confidence: float = 0.5):
        """
        Initialize the keypoint buffer.

        Args:
            max_size: Maximum number of frames to store
            min_confidence: Minimum confidence for valid keypoints
        """
        self.max_size = max_size
        self.min_confidence = min_confidence
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
        left_kp = pose.keypoints[LEFT_WRIST_IDX]
        if left_kp[2] >= self.min_confidence:
            self._left_wrist_y.append(float(left_kp[1]))
        else:
            self._left_wrist_y.append(None)  # Occluded

        # Right wrist - check confidence before storing
        right_kp = pose.keypoints[RIGHT_WRIST_IDX]
        if right_kp[2] >= self.min_confidence:
            self._right_wrist_y.append(float(right_kp[1]))
        else:
            self._right_wrist_y.append(None)  # Occluded

    def get_wrist_trajectory(
        self, wrist: str = "left"
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Get Y-positions and timestamps for specified wrist.

        Returns only frames where wrist was confident (not occluded).
        Returns (positions, timestamps) tuple with aligned arrays.

        Args:
            wrist: "left" or "right"

        Returns:
            Tuple of (positions, timestamps) arrays
        """
        data = self._left_wrist_y if wrist == "left" else self._right_wrist_y

        # Filter out None values (occluded frames)
        valid_indices = [i for i, v in enumerate(data) if v is not None]
        positions = np.array([data[i] for i in valid_indices], dtype=np.float32)
        timestamps = np.array(
            [self._timestamps[i] for i in valid_indices], dtype=np.float32
        )

        return positions, timestamps

    def get_timestamps(self) -> np.ndarray:
        """Get all timestamps (including occluded frames)."""
        return np.array(self._timestamps, dtype=np.float32)

    def clear(self) -> None:
        """Clear all buffered data."""
        self._left_wrist_y.clear()
        self._right_wrist_y.clear()
        self._timestamps.clear()

    def __len__(self) -> int:
        """Number of frames in buffer (including occluded)."""
        return len(self._timestamps)
