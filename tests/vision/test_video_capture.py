"""Tests for video capture sources."""

import numpy as np
import pytest


class TestMockVideoSource:
    """Tests for MockVideoSource."""

    def test_yields_correct_number_of_frames(self):
        """Generates correct number of frames for duration."""
        from src.vision.video_capture import MockVideoSource

        source = MockVideoSource(fps=30.0, duration=2.0)

        frames = list(source.frames())

        assert len(frames) == 60  # 30 fps * 2 seconds

    def test_frames_have_correct_shape(self):
        """Generated frames have correct dimensions."""
        from src.vision.video_capture import MockVideoSource

        source = MockVideoSource(fps=30.0, duration=1.0, frame_size=(640, 480))

        frame, timestamp, frame_index = next(source.frames())

        assert frame.shape == (480, 640, 3)  # H, W, C
        assert frame.dtype == np.uint8

    def test_timestamps_are_correct(self):
        """Timestamps match expected values for fps."""
        from src.vision.video_capture import MockVideoSource

        source = MockVideoSource(fps=30.0, duration=1.0)

        frames = list(source.frames())

        # Check first few timestamps
        assert frames[0][1] == pytest.approx(0.0, abs=0.001)
        assert frames[1][1] == pytest.approx(1 / 30.0, abs=0.001)
        assert frames[2][1] == pytest.approx(2 / 30.0, abs=0.001)

    def test_frame_indices_sequential(self):
        """Frame indices are sequential starting from 0."""
        from src.vision.video_capture import MockVideoSource

        source = MockVideoSource(fps=30.0, duration=1.0)

        frames = list(source.frames())

        for i, (_, _, frame_idx) in enumerate(frames):
            assert frame_idx == i

    def test_fps_property(self):
        """FPS property returns correct value."""
        from src.vision.video_capture import MockVideoSource

        source = MockVideoSource(fps=60.0, duration=1.0)

        assert source.fps == 60.0

    def test_close_is_noop(self):
        """Close method exists and doesn't raise."""
        from src.vision.video_capture import MockVideoSource

        source = MockVideoSource()
        source.close()  # Should not raise

    def test_custom_frame_color(self):
        """Can specify custom frame color."""
        from src.vision.video_capture import MockVideoSource

        source = MockVideoSource(
            fps=30.0, duration=0.1, frame_color=(255, 0, 0)  # Blue in BGR
        )

        frame, _, _ = next(source.frames())

        # All pixels should be blue
        assert np.all(frame[:, :, 0] == 255)  # B
        assert np.all(frame[:, :, 1] == 0)  # G
        assert np.all(frame[:, :, 2] == 0)  # R


class TestFileVideoSource:
    """Tests for FileVideoSource."""

    def test_raises_if_file_not_found(self, tmp_path):
        """Raises error if video file doesn't exist."""
        from src.vision.video_capture import FileVideoSource

        nonexistent = tmp_path / "does_not_exist.mp4"

        with pytest.raises(FileNotFoundError):
            FileVideoSource(nonexistent)

    def test_close_releases_resources(self, tmp_path):
        """Close releases video capture resources."""
        from src.vision.video_capture import FileVideoSource

        # Create a simple test file (this won't be a valid video, but we can test close)
        video_file = tmp_path / "test.mp4"
        video_file.touch()

        # This will fail to open as a video, but we can still test the close logic
        # by mocking or by checking the file existence check
        source = FileVideoSource.__new__(FileVideoSource)
        source.path = video_file
        source._cap = None

        source.close()  # Should not raise
