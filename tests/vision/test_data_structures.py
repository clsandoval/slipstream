"""Tests for vision data structures."""

import numpy as np
import pytest


class TestPoseResult:
    """Tests for PoseResult dataclass."""

    def test_pose_result_creation(self, valid_keypoints: np.ndarray):
        """PoseResult can be created with valid keypoints."""
        from src.vision.protocols import PoseResult

        result = PoseResult(
            keypoints=valid_keypoints,
            bbox=(100, 100, 500, 400),
            confidence=0.95,
            timestamp=1.5,
            frame_index=45,
        )

        assert result.confidence == 0.95
        assert result.timestamp == 1.5
        assert result.frame_index == 45
        assert result.bbox == (100, 100, 500, 400)

    def test_pose_result_keypoint_shape(self, valid_keypoints: np.ndarray):
        """Keypoints must be (17, 3) shape."""
        from src.vision.protocols import PoseResult

        result = PoseResult(
            keypoints=valid_keypoints,
            bbox=None,
            confidence=0.9,
            timestamp=0.0,
            frame_index=0,
        )

        assert result.keypoints.shape == (17, 3)

    def test_pose_result_wrist_indices(self, valid_keypoints: np.ndarray):
        """Left wrist is index 9, right wrist is index 10 (COCO format)."""
        from src.vision.protocols import PoseResult, LEFT_WRIST_IDX, RIGHT_WRIST_IDX

        result = PoseResult(
            keypoints=valid_keypoints,
            bbox=None,
            confidence=0.9,
            timestamp=0.0,
            frame_index=0,
        )

        # COCO keypoint indices
        assert LEFT_WRIST_IDX == 9
        assert RIGHT_WRIST_IDX == 10

        # Verify we can access wrist positions
        left_wrist = result.keypoints[LEFT_WRIST_IDX]
        right_wrist = result.keypoints[RIGHT_WRIST_IDX]

        assert left_wrist.shape == (3,)  # x, y, confidence
        assert right_wrist.shape == (3,)

    def test_pose_result_optional_bbox(self, valid_keypoints: np.ndarray):
        """BBox can be None if no bounding box available."""
        from src.vision.protocols import PoseResult

        result = PoseResult(
            keypoints=valid_keypoints,
            bbox=None,
            confidence=0.9,
            timestamp=0.0,
            frame_index=0,
        )

        assert result.bbox is None

    def test_pose_result_keypoint_access(self, valid_keypoints: np.ndarray):
        """Can access individual keypoint coordinates and confidence."""
        from src.vision.protocols import PoseResult

        result = PoseResult(
            keypoints=valid_keypoints,
            bbox=None,
            confidence=0.9,
            timestamp=0.0,
            frame_index=0,
        )

        # Access nose keypoint
        nose = result.keypoints[0]
        assert len(nose) == 3
        x, y, conf = nose
        assert isinstance(float(x), float)
        assert isinstance(float(y), float)
        assert 0.0 <= conf <= 1.0


class TestKeypointConstants:
    """Tests for COCO keypoint index constants."""

    def test_all_keypoint_indices_defined(self):
        """All 17 COCO keypoint indices should be defined."""
        from src.vision.protocols import (
            NOSE_IDX,
            LEFT_EYE_IDX,
            RIGHT_EYE_IDX,
            LEFT_EAR_IDX,
            RIGHT_EAR_IDX,
            LEFT_SHOULDER_IDX,
            RIGHT_SHOULDER_IDX,
            LEFT_ELBOW_IDX,
            RIGHT_ELBOW_IDX,
            LEFT_WRIST_IDX,
            RIGHT_WRIST_IDX,
            LEFT_HIP_IDX,
            RIGHT_HIP_IDX,
            LEFT_KNEE_IDX,
            RIGHT_KNEE_IDX,
            LEFT_ANKLE_IDX,
            RIGHT_ANKLE_IDX,
        )

        # Verify COCO keypoint indices
        assert NOSE_IDX == 0
        assert LEFT_EYE_IDX == 1
        assert RIGHT_EYE_IDX == 2
        assert LEFT_EAR_IDX == 3
        assert RIGHT_EAR_IDX == 4
        assert LEFT_SHOULDER_IDX == 5
        assert RIGHT_SHOULDER_IDX == 6
        assert LEFT_ELBOW_IDX == 7
        assert RIGHT_ELBOW_IDX == 8
        assert LEFT_WRIST_IDX == 9
        assert RIGHT_WRIST_IDX == 10
        assert LEFT_HIP_IDX == 11
        assert RIGHT_HIP_IDX == 12
        assert LEFT_KNEE_IDX == 13
        assert RIGHT_KNEE_IDX == 14
        assert LEFT_ANKLE_IDX == 15
        assert RIGHT_ANKLE_IDX == 16

    def test_num_keypoints_constant(self):
        """NUM_KEYPOINTS should be 17 for COCO format."""
        from src.vision.protocols import NUM_KEYPOINTS

        assert NUM_KEYPOINTS == 17
