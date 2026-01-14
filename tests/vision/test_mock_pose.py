"""Tests for mock pose estimators."""

import numpy as np
import pytest

from src.vision.protocols import PoseResult, NUM_KEYPOINTS


class TestSineWavePoseEstimator:
    """Tests for SineWavePoseEstimator."""

    def test_returns_valid_pose_result(self):
        """Mock returns PoseResult with correct keypoint shape."""
        from src.vision.backends.mock_pose import SineWavePoseEstimator

        estimator = SineWavePoseEstimator(stroke_rate=60.0)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        result = estimator.estimate(frame, timestamp=0.0, frame_index=0)

        assert isinstance(result, PoseResult)
        assert result.keypoints.shape == (NUM_KEYPOINTS, 3)
        assert result.confidence > 0.0
        assert result.timestamp == 0.0
        assert result.frame_index == 0

    def test_wrist_oscillates_over_time(self):
        """Wrist Y-position follows sine wave pattern."""
        from src.vision.backends.mock_pose import SineWavePoseEstimator
        from src.vision.protocols import LEFT_WRIST_IDX

        estimator = SineWavePoseEstimator(stroke_rate=60.0, seed=42)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Collect wrist Y positions over time
        wrist_y_positions = []
        for i in range(60):  # 2 seconds at 30 fps
            timestamp = i / 30.0
            result = estimator.estimate(frame, timestamp=timestamp, frame_index=i)
            wrist_y_positions.append(result.keypoints[LEFT_WRIST_IDX, 1])

        # Verify oscillation - max and min should differ significantly
        y_range = max(wrist_y_positions) - min(wrist_y_positions)
        assert y_range > 50, "Wrist should oscillate by at least 50 pixels"

    def test_stroke_rate_affects_frequency(self):
        """Higher stroke rate = faster oscillation."""
        from src.vision.backends.mock_pose import SineWavePoseEstimator
        from src.vision.protocols import LEFT_WRIST_IDX

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Slow stroke rate
        slow = SineWavePoseEstimator(stroke_rate=30.0, seed=42)
        # Fast stroke rate
        fast = SineWavePoseEstimator(stroke_rate=90.0, seed=42)

        # Count zero-crossings (relative to mean) as proxy for frequency
        def count_peaks(estimator, duration=3.0, fps=30.0):
            positions = []
            for i in range(int(duration * fps)):
                result = estimator.estimate(frame, timestamp=i / fps, frame_index=i)
                positions.append(result.keypoints[LEFT_WRIST_IDX, 1])
            # Count direction changes (peaks and troughs)
            changes = 0
            for i in range(1, len(positions) - 1):
                if (positions[i] > positions[i - 1] and positions[i] > positions[i + 1]) or (
                    positions[i] < positions[i - 1] and positions[i] < positions[i + 1]
                ):
                    changes += 1
            return changes

        slow_peaks = count_peaks(slow)
        fast_peaks = count_peaks(fast)

        # Fast should have ~3x as many peaks as slow (90/30 = 3)
        assert fast_peaks > slow_peaks, "Fast stroke rate should have more peaks"

    def test_deterministic_with_seed(self):
        """Same seed produces identical output."""
        from src.vision.backends.mock_pose import SineWavePoseEstimator

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        est1 = SineWavePoseEstimator(stroke_rate=60.0, seed=42)
        est2 = SineWavePoseEstimator(stroke_rate=60.0, seed=42)

        for i in range(10):
            result1 = est1.estimate(frame, timestamp=i / 30.0, frame_index=i)
            result2 = est2.estimate(frame, timestamp=i / 30.0, frame_index=i)

            np.testing.assert_array_equal(result1.keypoints, result2.keypoints)

    def test_left_right_wrist_alternation(self):
        """Left and right wrists are 180 degrees out of phase."""
        from src.vision.backends.mock_pose import SineWavePoseEstimator
        from src.vision.protocols import LEFT_WRIST_IDX, RIGHT_WRIST_IDX

        estimator = SineWavePoseEstimator(stroke_rate=60.0, seed=42)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # At any moment, wrists should be roughly opposite in their oscillation
        # When left is at max, right should be at min (approximately)
        left_positions = []
        right_positions = []

        for i in range(60):
            result = estimator.estimate(frame, timestamp=i / 30.0, frame_index=i)
            left_positions.append(result.keypoints[LEFT_WRIST_IDX, 1])
            right_positions.append(result.keypoints[RIGHT_WRIST_IDX, 1])

        # Normalize positions
        left_norm = np.array(left_positions) - np.mean(left_positions)
        right_norm = np.array(right_positions) - np.mean(right_positions)

        # Correlation should be negative (opposite phase)
        correlation = np.corrcoef(left_norm, right_norm)[0, 1]
        assert correlation < -0.9, f"Wrists should be anti-correlated, got {correlation}"

    def test_is_available_always_true(self):
        """Mock estimator is always available."""
        from src.vision.backends.mock_pose import SineWavePoseEstimator

        estimator = SineWavePoseEstimator()
        assert estimator.is_available() is True


class TestFilePoseEstimator:
    """Tests for FilePoseEstimator."""

    def test_loads_keypoints_from_file(self, tmp_path):
        """Can load and replay recorded keypoints."""
        from src.vision.backends.mock_pose import FilePoseEstimator
        import json

        # Create a test keypoints file
        keypoints_data = [
            {
                "keypoints": np.random.rand(17, 3).tolist(),
                "bbox": [100, 100, 500, 400],
                "confidence": 0.95,
                "timestamp": 0.0,
                "frame_index": 0,
            },
            {
                "keypoints": np.random.rand(17, 3).tolist(),
                "bbox": [100, 100, 500, 400],
                "confidence": 0.92,
                "timestamp": 0.033,
                "frame_index": 1,
            },
        ]

        keypoints_file = tmp_path / "keypoints.json"
        keypoints_file.write_text(json.dumps(keypoints_data))

        estimator = FilePoseEstimator(keypoints_file)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        result = estimator.estimate(frame, timestamp=0.0, frame_index=0)

        assert isinstance(result, PoseResult)
        assert result.keypoints.shape == (NUM_KEYPOINTS, 3)

    def test_returns_none_when_exhausted(self, tmp_path):
        """Returns None after all keypoints consumed."""
        from src.vision.backends.mock_pose import FilePoseEstimator
        import json

        # Create a test keypoints file with one entry
        keypoints_data = [
            {
                "keypoints": np.random.rand(17, 3).tolist(),
                "bbox": [100, 100, 500, 400],
                "confidence": 0.95,
                "timestamp": 0.0,
                "frame_index": 0,
            },
        ]

        keypoints_file = tmp_path / "keypoints.json"
        keypoints_file.write_text(json.dumps(keypoints_data))

        estimator = FilePoseEstimator(keypoints_file)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # First call returns data
        result1 = estimator.estimate(frame, timestamp=0.0, frame_index=0)
        assert result1 is not None

        # Second call returns None (exhausted)
        result2 = estimator.estimate(frame, timestamp=0.033, frame_index=1)
        assert result2 is None

    def test_is_available_checks_file_exists(self, tmp_path):
        """is_available returns True only if file exists."""
        from src.vision.backends.mock_pose import FilePoseEstimator
        import json

        keypoints_file = tmp_path / "keypoints.json"

        # File doesn't exist yet
        estimator = FilePoseEstimator(keypoints_file)
        assert estimator.is_available() is False

        # Create the file
        keypoints_file.write_text(json.dumps([]))
        assert estimator.is_available() is True


class TestRandomPoseEstimator:
    """Tests for RandomPoseEstimator."""

    def test_returns_valid_pose_result(self):
        """Returns PoseResult with correct shape."""
        from src.vision.backends.mock_pose import RandomPoseEstimator

        estimator = RandomPoseEstimator(seed=42)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        result = estimator.estimate(frame, timestamp=0.0, frame_index=0)

        assert isinstance(result, PoseResult)
        assert result.keypoints.shape == (NUM_KEYPOINTS, 3)

    def test_keypoints_in_valid_range(self):
        """Keypoints are within frame bounds."""
        from src.vision.backends.mock_pose import RandomPoseEstimator

        frame_size = (640, 480)  # width, height
        estimator = RandomPoseEstimator(frame_size=frame_size, seed=42)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        result = estimator.estimate(frame, timestamp=0.0, frame_index=0)

        # X coordinates should be in [0, width]
        assert np.all(result.keypoints[:, 0] >= 0)
        assert np.all(result.keypoints[:, 0] <= frame_size[0])

        # Y coordinates should be in [0, height]
        assert np.all(result.keypoints[:, 1] >= 0)
        assert np.all(result.keypoints[:, 1] <= frame_size[1])

        # Confidence should be in [0, 1]
        assert np.all(result.keypoints[:, 2] >= 0)
        assert np.all(result.keypoints[:, 2] <= 1)

    def test_deterministic_with_seed(self):
        """Same seed produces identical results."""
        from src.vision.backends.mock_pose import RandomPoseEstimator

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        est1 = RandomPoseEstimator(seed=42)
        est2 = RandomPoseEstimator(seed=42)

        result1 = est1.estimate(frame, timestamp=0.0, frame_index=0)
        result2 = est2.estimate(frame, timestamp=0.0, frame_index=0)

        np.testing.assert_array_equal(result1.keypoints, result2.keypoints)

    def test_is_available_always_true(self):
        """Mock estimator is always available."""
        from src.vision.backends.mock_pose import RandomPoseEstimator

        estimator = RandomPoseEstimator()
        assert estimator.is_available() is True
