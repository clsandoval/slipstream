"""Video capture sources for the vision pipeline."""

from pathlib import Path
from typing import Iterator

import numpy as np


class MockVideoSource:
    """
    Generates blank frames at specified FPS.

    Used with mock pose estimators that don't need real frame data.
    """

    def __init__(
        self,
        fps: float = 30.0,
        duration: float = 10.0,
        frame_size: tuple[int, int] = (640, 480),  # width, height
        frame_color: tuple[int, int, int] = (0, 0, 0),  # BGR
    ):
        """
        Initialize mock video source.

        Args:
            fps: Frames per second
            duration: Total duration in seconds
            frame_size: Frame dimensions (width, height)
            frame_color: Default frame color in BGR
        """
        self._fps = fps
        self.duration = duration
        self.frame_size = frame_size
        self.frame_color = frame_color
        self.total_frames = int(fps * duration)

    def frames(self) -> Iterator[tuple[np.ndarray, float, int]]:
        """
        Yield synthetic frames.

        Yields:
            Tuple of (frame, timestamp, frame_index)
        """
        width, height = self.frame_size
        for i in range(self.total_frames):
            timestamp = i / self._fps
            frame = np.full((height, width, 3), self.frame_color, dtype=np.uint8)
            yield frame, timestamp, i

    @property
    def fps(self) -> float:
        """Source frame rate."""
        return self._fps

    def close(self) -> None:
        """Release resources (no-op for mock)."""
        pass


class FileVideoSource:
    """
    Reads frames from a video file.

    For testing with real recorded video (when available).
    Requires OpenCV (cv2) to be installed.
    """

    def __init__(self, path: Path):
        """
        Initialize file video source.

        Args:
            path: Path to video file

        Raises:
            FileNotFoundError: If video file doesn't exist
        """
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"Video file not found: {path}")

        # Lazy import cv2 to avoid dependency if not needed
        import cv2

        self._cap = cv2.VideoCapture(str(self.path))
        if not self._cap.isOpened():
            raise IOError(f"Could not open video file: {path}")

        self._fps = self._cap.get(cv2.CAP_PROP_FPS)

    def frames(self) -> Iterator[tuple[np.ndarray, float, int]]:
        """
        Yield frames from video file.

        Yields:
            Tuple of (frame, timestamp, frame_index)
        """
        frame_index = 0
        while True:
            ret, frame = self._cap.read()
            if not ret:
                break

            timestamp = frame_index / self._fps
            yield frame, timestamp, frame_index
            frame_index += 1

    @property
    def fps(self) -> float:
        """Source frame rate."""
        return self._fps

    def close(self) -> None:
        """Release video capture resources."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
