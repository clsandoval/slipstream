"""Tests for KeypointBuffer."""

import numpy as np
import pytest

from src.vision.protocols import PoseResult, LEFT_WRIST_IDX, RIGHT_WRIST_IDX


def make_pose_result(
    timestamp: float,
    frame_index: int,
    left_wrist_y: float = 200.0,
    right_wrist_y: float = 200.0,
) -> PoseResult:
    """Helper to create PoseResult with specific wrist positions."""
    keypoints = np.zeros((17, 3), dtype=np.float32)
    keypoints[:, 2] = 0.95  # Set all confidence to high

    # Set wrist positions
    keypoints[LEFT_WRIST_IDX] = [100, left_wrist_y, 0.95]
    keypoints[RIGHT_WRIST_IDX] = [300, right_wrist_y, 0.95]

    return PoseResult(
        keypoints=keypoints,
        bbox=(100, 100, 500, 400),
        confidence=0.95,
        timestamp=timestamp,
        frame_index=frame_index,
    )


class TestKeypointBuffer:
    """Tests for KeypointBuffer."""

    def test_add_and_retrieve(self):
        """Can add poses and retrieve wrist trajectory."""
        from src.vision.keypoint_buffer import KeypointBuffer

        buffer = KeypointBuffer(max_size=100)

        # Add some poses
        buffer.add(make_pose_result(0.0, 0, left_wrist_y=100.0))
        buffer.add(make_pose_result(0.033, 1, left_wrist_y=150.0))
        buffer.add(make_pose_result(0.066, 2, left_wrist_y=200.0))

        positions, timestamps = buffer.get_wrist_trajectory("left")

        assert len(positions) == 3
        np.testing.assert_array_almost_equal(positions, [100.0, 150.0, 200.0])

    def test_circular_buffer_overflow(self):
        """Old frames discarded when buffer full."""
        from src.vision.keypoint_buffer import KeypointBuffer

        buffer = KeypointBuffer(max_size=5)

        # Add more poses than buffer size
        for i in range(10):
            buffer.add(make_pose_result(i * 0.033, i, left_wrist_y=float(i * 10)))

        # Should only have last 5
        assert len(buffer) == 5
        positions, _ = buffer.get_wrist_trajectory("left")
        np.testing.assert_array_almost_equal(positions, [50.0, 60.0, 70.0, 80.0, 90.0])

    def test_wrist_trajectory_shape(self):
        """Trajectory array matches buffer length."""
        from src.vision.keypoint_buffer import KeypointBuffer

        buffer = KeypointBuffer(max_size=100)

        for i in range(25):
            buffer.add(make_pose_result(i * 0.033, i))

        left_pos, left_ts = buffer.get_wrist_trajectory("left")
        right_pos, right_ts = buffer.get_wrist_trajectory("right")

        assert len(left_pos) == 25
        assert len(right_pos) == 25
        assert isinstance(left_pos, np.ndarray)
        assert isinstance(right_pos, np.ndarray)
        assert len(left_ts) == len(left_pos)
        assert len(right_ts) == len(right_pos)

    def test_timestamps_aligned_with_positions(self):
        """Timestamps correspond to correct positions."""
        from src.vision.keypoint_buffer import KeypointBuffer

        buffer = KeypointBuffer(max_size=100)

        # Add poses with known timestamps and positions
        buffer.add(make_pose_result(0.0, 0, left_wrist_y=100.0))
        buffer.add(make_pose_result(1.0, 30, left_wrist_y=200.0))
        buffer.add(make_pose_result(2.0, 60, left_wrist_y=300.0))

        positions, timestamps = buffer.get_wrist_trajectory("left")

        assert len(timestamps) == len(positions)
        np.testing.assert_array_almost_equal(timestamps, [0.0, 1.0, 2.0])
        np.testing.assert_array_almost_equal(positions, [100.0, 200.0, 300.0])

    def test_clear_empties_buffer(self):
        """Clear removes all data."""
        from src.vision.keypoint_buffer import KeypointBuffer

        buffer = KeypointBuffer(max_size=100)

        for i in range(10):
            buffer.add(make_pose_result(i * 0.033, i))

        assert len(buffer) == 10

        buffer.clear()

        assert len(buffer) == 0
        positions, timestamps = buffer.get_wrist_trajectory("left")
        assert len(positions) == 0
        assert len(timestamps) == 0
        assert len(buffer.get_timestamps()) == 0

    def test_low_confidence_keypoints_filtered(self):
        """Low confidence wrists are filtered out from trajectory."""
        from src.vision.keypoint_buffer import KeypointBuffer

        buffer = KeypointBuffer(max_size=100, min_confidence=0.5)

        # Create pose with low confidence left wrist
        keypoints = np.zeros((17, 3), dtype=np.float32)
        keypoints[:, 2] = 0.95
        keypoints[LEFT_WRIST_IDX] = [100, 200, 0.2]  # Low confidence
        keypoints[RIGHT_WRIST_IDX] = [300, 200, 0.95]  # High confidence

        pose = PoseResult(
            keypoints=keypoints,
            bbox=None,
            confidence=0.95,
            timestamp=0.0,
            frame_index=0,
        )

        buffer.add(pose)

        # Low confidence wrist should be filtered out
        left_positions, left_timestamps = buffer.get_wrist_trajectory("left")
        assert len(left_positions) == 0  # Filtered out

        # High confidence wrist should be included
        right_positions, right_timestamps = buffer.get_wrist_trajectory("right")
        assert len(right_positions) == 1
        assert right_positions[0] == 200.0

    def test_empty_buffer_returns_empty_arrays(self):
        """Empty buffer returns empty arrays."""
        from src.vision.keypoint_buffer import KeypointBuffer

        buffer = KeypointBuffer(max_size=100)

        assert len(buffer) == 0
        left_pos, left_ts = buffer.get_wrist_trajectory("left")
        right_pos, right_ts = buffer.get_wrist_trajectory("right")
        assert len(left_pos) == 0
        assert len(left_ts) == 0
        assert len(right_pos) == 0
        assert len(right_ts) == 0
        assert len(buffer.get_timestamps()) == 0

    def test_get_wrist_trajectory_default_is_left(self):
        """Default wrist trajectory is left."""
        from src.vision.keypoint_buffer import KeypointBuffer

        buffer = KeypointBuffer(max_size=100)
        buffer.add(make_pose_result(0.0, 0, left_wrist_y=100.0, right_wrist_y=200.0))

        # Default should be left
        default_pos, default_ts = buffer.get_wrist_trajectory()
        left_pos, left_ts = buffer.get_wrist_trajectory("left")

        np.testing.assert_array_equal(default_pos, left_pos)
        np.testing.assert_array_equal(default_ts, left_ts)

    def test_right_wrist_trajectory(self):
        """Can retrieve right wrist trajectory."""
        from src.vision.keypoint_buffer import KeypointBuffer

        buffer = KeypointBuffer(max_size=100)
        buffer.add(make_pose_result(0.0, 0, left_wrist_y=100.0, right_wrist_y=300.0))
        buffer.add(make_pose_result(0.033, 1, left_wrist_y=150.0, right_wrist_y=250.0))

        right_pos, right_ts = buffer.get_wrist_trajectory("right")

        np.testing.assert_array_almost_equal(right_pos, [300.0, 250.0])

    def test_handles_all_occluded(self):
        """Returns empty arrays when all frames are occluded."""
        from src.vision.keypoint_buffer import KeypointBuffer

        buffer = KeypointBuffer(max_size=100, min_confidence=0.5)

        # Create poses with all low confidence wrists
        for i in range(5):
            keypoints = np.zeros((17, 3), dtype=np.float32)
            keypoints[:, 2] = 0.95
            keypoints[LEFT_WRIST_IDX] = [100, 200, 0.2]  # Low confidence
            keypoints[RIGHT_WRIST_IDX] = [300, 200, 0.2]  # Low confidence

            pose = PoseResult(
                keypoints=keypoints,
                bbox=None,
                confidence=0.95,
                timestamp=i * 0.033,
                frame_index=i,
            )
            buffer.add(pose)

        # Buffer has frames, but all wrists are occluded
        assert len(buffer) == 5
        left_pos, left_ts = buffer.get_wrist_trajectory("left")
        assert len(left_pos) == 0
        assert len(left_ts) == 0

    def test_mixed_confidence_frames(self):
        """Correctly handles mix of confident and occluded frames."""
        from src.vision.keypoint_buffer import KeypointBuffer

        buffer = KeypointBuffer(max_size=100, min_confidence=0.5)

        # Add mix of high and low confidence
        buffer.add(make_pose_result(0.0, 0, left_wrist_y=100.0))  # High confidence

        # Low confidence frame
        keypoints = np.zeros((17, 3), dtype=np.float32)
        keypoints[:, 2] = 0.95
        keypoints[LEFT_WRIST_IDX] = [100, 150, 0.2]  # Low confidence
        keypoints[RIGHT_WRIST_IDX] = [300, 200, 0.95]
        buffer.add(PoseResult(keypoints=keypoints, bbox=None, confidence=0.95, timestamp=0.033, frame_index=1))

        buffer.add(make_pose_result(0.066, 2, left_wrist_y=200.0))  # High confidence

        # Should only have 2 left wrist positions (frames 0 and 2)
        left_pos, left_ts = buffer.get_wrist_trajectory("left")
        assert len(left_pos) == 2
        np.testing.assert_array_almost_equal(left_pos, [100.0, 200.0])
        np.testing.assert_array_almost_equal(left_ts, [0.0, 0.066])
