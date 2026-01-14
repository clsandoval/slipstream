"""Tests for pose estimator factory."""

import pytest
import numpy as np


class TestCreatePoseEstimator:
    """Tests for create_pose_estimator factory function."""

    def test_create_mock_sine_backend(self):
        """Can create sine wave mock estimator."""
        from src.vision.pose_estimator import create_pose_estimator, EstimatorBackend

        estimator = create_pose_estimator(backend=EstimatorBackend.MOCK_SINE)

        assert estimator.is_available()

        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = estimator.estimate(frame, 0.0, 0)

        assert result is not None
        assert result.keypoints.shape == (17, 3)

    def test_create_mock_random_backend(self):
        """Can create random mock estimator."""
        from src.vision.pose_estimator import create_pose_estimator, EstimatorBackend

        estimator = create_pose_estimator(backend=EstimatorBackend.MOCK_RANDOM)

        assert estimator.is_available()

        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = estimator.estimate(frame, 0.0, 0)

        assert result is not None

    def test_create_mock_file_backend(self, tmp_path):
        """Can create file mock estimator."""
        from src.vision.pose_estimator import create_pose_estimator, EstimatorBackend
        import json

        # Create a test keypoints file
        keypoints_file = tmp_path / "keypoints.json"
        keypoints_file.write_text(
            json.dumps(
                [
                    {
                        "keypoints": np.random.rand(17, 3).tolist(),
                        "bbox": [100, 100, 500, 400],
                        "confidence": 0.95,
                        "timestamp": 0.0,
                        "frame_index": 0,
                    }
                ]
            )
        )

        estimator = create_pose_estimator(
            backend=EstimatorBackend.MOCK_FILE, keypoints_file=keypoints_file
        )

        assert estimator.is_available()

    def test_create_with_kwargs(self):
        """Can pass kwargs to estimator constructor."""
        from src.vision.pose_estimator import create_pose_estimator, EstimatorBackend

        estimator = create_pose_estimator(
            backend=EstimatorBackend.MOCK_SINE, stroke_rate=90.0, seed=123
        )

        # Verify kwargs were applied
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Run deterministic estimator
        results = [estimator.estimate(frame, i / 30.0, i) for i in range(30)]

        # With seed=123, results should be deterministic
        estimator2 = create_pose_estimator(
            backend=EstimatorBackend.MOCK_SINE, stroke_rate=90.0, seed=123
        )
        results2 = [estimator2.estimate(frame, i / 30.0, i) for i in range(30)]

        for r1, r2 in zip(results, results2):
            np.testing.assert_array_equal(r1.keypoints, r2.keypoints)

    def test_unknown_backend_raises(self):
        """Unknown backend raises ValueError."""
        from src.vision.pose_estimator import create_pose_estimator

        with pytest.raises(ValueError, match="Unknown backend"):
            create_pose_estimator(backend="invalid")

    def test_yolo_backend_import_guarded(self):
        """YOLO backend import is guarded (may not be available)."""
        from src.vision.pose_estimator import create_pose_estimator, EstimatorBackend

        # This test verifies the import structure is correct
        # It may succeed or fail depending on whether ultralytics is installed
        try:
            estimator = create_pose_estimator(backend=EstimatorBackend.YOLO)
            # If we get here, ultralytics is available
            assert hasattr(estimator, "estimate")
            assert hasattr(estimator, "is_available")
        except ImportError:
            # ultralytics not installed, which is fine for testing
            pass


class TestEstimatorBackend:
    """Tests for EstimatorBackend enum."""

    def test_all_backends_defined(self):
        """All expected backends are defined."""
        from src.vision.pose_estimator import EstimatorBackend

        assert EstimatorBackend.YOLO.value == "yolo"
        assert EstimatorBackend.MOCK_SINE.value == "mock_sine"
        assert EstimatorBackend.MOCK_FILE.value == "mock_file"
        assert EstimatorBackend.MOCK_RANDOM.value == "mock_random"
