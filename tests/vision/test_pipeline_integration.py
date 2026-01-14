"""Integration tests for the vision pipeline."""

import numpy as np
import pytest


class TestVisionPipelineIntegration:
    """
    Full pipeline integration tests using mock pose estimator.

    These tests validate the entire pipeline works end-to-end
    WITHOUT requiring CUDA or real model inference.
    """

    @pytest.fixture
    def mock_pipeline(self):
        """Pipeline with sine wave mock estimator."""
        from src.vision.backends.mock_pose import SineWavePoseEstimator
        from src.vision.pipeline import VisionPipeline
        from src.vision.state_store import StateStore

        estimator = SineWavePoseEstimator(stroke_rate=60.0, seed=42)
        state_store = StateStore()
        return VisionPipeline(pose_estimator=estimator, state_store=state_store)

    def test_pipeline_processes_frames(self, mock_pipeline):
        """Pipeline processes frames without error."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Process several frames
        for i in range(30):
            mock_pipeline.process_frame(frame, timestamp=i / 30.0, frame_index=i)

        # Should have updated state
        state = mock_pipeline.state_store.get_state()
        assert state.pose_detected is True

    def test_stroke_count_accumulates(self, mock_pipeline):
        """Stroke count increases over time."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Process 10 seconds of video at 30 fps
        for i in range(300):
            mock_pipeline.process_frame(frame, timestamp=i / 30.0, frame_index=i)

        state = mock_pipeline.state_store.get_state()

        # At 60 strokes/min, 10 seconds should give ~10 strokes
        assert state.stroke_count >= 8
        assert state.stroke_count <= 12

    def test_stroke_rate_accuracy(self, mock_pipeline):
        """
        Calculated stroke rate matches mock's configured rate.

        Mock at 60 strokes/min -> pipeline should report ~60 strokes/min
        """
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Process 15 seconds of video (enough to fill rate window)
        for i in range(450):
            mock_pipeline.process_frame(frame, timestamp=i / 30.0, frame_index=i)

        state = mock_pipeline.state_store.get_state()

        # Should be close to 60 strokes/min
        assert 55 <= state.stroke_rate <= 65

    def test_rate_history_populated(self, mock_pipeline):
        """Rate history grows over time for trend analysis."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Process enough frames for rate history to accumulate
        # Rate samples are recorded every 5 seconds
        for i in range(600):  # 20 seconds at 30fps
            mock_pipeline.process_frame(frame, timestamp=i / 30.0, frame_index=i)

        state = mock_pipeline.state_store.get_state()
        # Should have multiple rate samples (at 5s intervals: ~4 samples)
        assert len(state.rate_history) >= 3
        # Claude can derive trends from this data
        rates = [sample.rate for sample in state.rate_history]
        assert all(r >= 0 for r in rates)

    def test_state_updates_each_frame(self, mock_pipeline):
        """State store updated after each frame processed."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Initial state
        state_before = mock_pipeline.state_store.get_state()
        assert state_before.pose_detected is False

        # Process one frame
        mock_pipeline.process_frame(frame, timestamp=0.0, frame_index=0)

        state_after = mock_pipeline.state_store.get_state()
        assert state_after.pose_detected is True

    @pytest.mark.parametrize(
        "mock_rate,expected_range",
        [
            (30, (25, 35)),
            (60, (55, 65)),
            (90, (85, 95)),
        ],
    )
    def test_rate_accuracy_across_speeds(self, mock_rate: int, expected_range: tuple):
        """Pipeline accurately detects various stroke rates."""
        from src.vision.backends.mock_pose import SineWavePoseEstimator
        from src.vision.pipeline import VisionPipeline
        from src.vision.state_store import StateStore

        estimator = SineWavePoseEstimator(stroke_rate=float(mock_rate), seed=42)
        state_store = StateStore()
        pipeline = VisionPipeline(pose_estimator=estimator, state_store=state_store)

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Process 20 seconds
        for i in range(600):
            pipeline.process_frame(frame, timestamp=i / 30.0, frame_index=i)

        state = state_store.get_state()
        assert expected_range[0] <= state.stroke_rate <= expected_range[1]

    def test_run_with_video_source(self):
        """Pipeline can run on a video source."""
        from src.vision.backends.mock_pose import SineWavePoseEstimator
        from src.vision.pipeline import VisionPipeline
        from src.vision.state_store import StateStore
        from src.vision.video_capture import MockVideoSource

        estimator = SineWavePoseEstimator(stroke_rate=60.0, seed=42)
        state_store = StateStore()
        pipeline = VisionPipeline(pose_estimator=estimator, state_store=state_store)

        video = MockVideoSource(fps=30.0, duration=5.0)
        pipeline.run(video)

        state = state_store.get_state()
        assert state.stroke_count >= 3
        assert state.pose_detected is True

    def test_pipeline_handles_no_detection(self):
        """Pipeline handles frames with no pose detection."""
        from src.vision.pipeline import VisionPipeline
        from src.vision.state_store import StateStore
        from src.vision.protocols import PoseResult

        # Mock estimator that returns None (no detection)
        class NoPoseEstimator:
            def estimate(self, frame, timestamp, frame_index):
                return None

            def is_available(self):
                return True

        state_store = StateStore()
        pipeline = VisionPipeline(
            pose_estimator=NoPoseEstimator(), state_store=state_store
        )

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        for i in range(30):
            pipeline.process_frame(frame, timestamp=i / 30.0, frame_index=i)

        state = state_store.get_state()
        assert state.pose_detected is False
        assert state.stroke_count == 0


class TestPipelineWithChangingRate:
    """Tests for pipeline behavior with varying stroke rates."""

    def test_detects_rate_and_builds_history(self):
        """Pipeline correctly detects rate and builds rate history."""
        from src.vision.backends.mock_pose import SineWavePoseEstimator
        from src.vision.pipeline import VisionPipeline
        from src.vision.state_store import StateStore

        # Test with a known stroke rate
        estimator = SineWavePoseEstimator(stroke_rate=60.0, seed=42)
        state_store = StateStore()
        pipeline = VisionPipeline(pose_estimator=estimator, state_store=state_store)

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Run for 45 seconds - enough for warmup and rate history
        for i in range(1350):
            pipeline.process_frame(frame, timestamp=i / 30.0, frame_index=i)

        state = state_store.get_state()
        # Verify strokes are detected
        assert state.stroke_count >= 30  # At 60/min for 45s, expect ~45 strokes
        # Verify rate history is populated (Claude derives trends from this)
        assert len(state.rate_history) >= 5  # At 5s intervals, 45s = ~9 samples
        # All rates should be reasonable for 60 strokes/min mock
        rates = [sample.rate for sample in state.rate_history]
        assert all(40 <= r <= 80 for r in rates if r > 0)
