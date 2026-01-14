"""YOLO11-Pose implementation for Jetson/CUDA."""

from pathlib import Path

import numpy as np

from src.vision.protocols import NUM_KEYPOINTS, PoseResult


class YoloPoseEstimator:
    """
    Real YOLO11-Pose implementation for Jetson/CUDA.

    Implements PoseEstimatorProtocol - same interface as mocks.
    Requires ultralytics package and CUDA for optimal performance.
    """

    # Constants matching COCO format
    LEFT_WRIST_IDX = 9
    RIGHT_WRIST_IDX = 10

    def __init__(
        self,
        model_path: Path | str = "yolo11m-pose.pt",
        conf_threshold: float = 0.5,
        device: int | str = 0,  # 0 for CUDA, "cpu" for CPU
    ):
        """
        Initialize YOLO pose estimator.

        Args:
            model_path: Path to YOLO model file
            conf_threshold: Minimum confidence for detections
            device: Device to run inference on (0 for GPU, "cpu" for CPU)
        """
        self.conf_threshold = conf_threshold
        self.device = device
        self._model = None
        self._model_path = str(model_path)

    def _load_model(self) -> None:
        """Lazy load model on first use."""
        if self._model is None:
            from ultralytics import YOLO

            self._model = YOLO(self._model_path)

    def estimate(
        self,
        frame: np.ndarray,
        timestamp: float,
        frame_index: int,
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

        # Validate keypoint shape
        if keypoints.shape[0] != NUM_KEYPOINTS:
            return None

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
