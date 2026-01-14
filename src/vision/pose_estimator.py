"""Pose estimator factory for creating implementations."""

from enum import Enum
from pathlib import Path
from typing import Any

from src.vision.protocols import PoseEstimatorProtocol


class EstimatorBackend(Enum):
    """Available pose estimator backends."""

    YOLO = "yolo"  # Real YOLO11-Pose (requires CUDA)
    MOCK_SINE = "mock_sine"  # Sine wave pattern (deterministic)
    MOCK_FILE = "mock_file"  # Replay from recorded keypoints
    MOCK_RANDOM = "mock_random"  # Random but valid keypoints


def create_pose_estimator(
    backend: EstimatorBackend | str = EstimatorBackend.YOLO,
    **kwargs: Any,
) -> PoseEstimatorProtocol:
    """
    Factory function to create pose estimators.

    In tests/dev without CUDA, use MOCK_* backends.
    In production on Jetson, use YOLO backend.

    Args:
        backend: Which backend to use
        **kwargs: Additional arguments passed to the estimator constructor

    Returns:
        A pose estimator implementation

    Raises:
        ValueError: If unknown backend specified
        ImportError: If YOLO backend requested but ultralytics not installed
    """
    # Convert string to enum if needed
    if isinstance(backend, str):
        try:
            backend = EstimatorBackend(backend)
        except ValueError:
            raise ValueError(f"Unknown backend: {backend}")

    if backend == EstimatorBackend.YOLO:
        from src.vision.backends.yolo_pose import YoloPoseEstimator

        return YoloPoseEstimator(**kwargs)

    elif backend == EstimatorBackend.MOCK_SINE:
        from src.vision.backends.mock_pose import SineWavePoseEstimator

        return SineWavePoseEstimator(**kwargs)

    elif backend == EstimatorBackend.MOCK_FILE:
        from src.vision.backends.mock_pose import FilePoseEstimator

        keypoints_file = kwargs.pop("keypoints_file", None)
        if keypoints_file is None:
            raise ValueError("MOCK_FILE backend requires 'keypoints_file' argument")
        return FilePoseEstimator(keypoints_file=Path(keypoints_file), **kwargs)

    elif backend == EstimatorBackend.MOCK_RANDOM:
        from src.vision.backends.mock_pose import RandomPoseEstimator

        return RandomPoseEstimator(**kwargs)

    else:
        raise ValueError(f"Unknown backend: {backend}")
