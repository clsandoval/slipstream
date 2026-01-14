"""Tests for StrokeDetector."""

import numpy as np
import pytest


def generate_sine_wave(
    duration: float, fps: float, stroke_rate: float, amplitude: float = 100.0
) -> tuple[np.ndarray, np.ndarray]:
    """Generate sine wave data for testing."""
    num_frames = int(duration * fps)
    timestamps = np.linspace(0, duration, num_frames)

    # Frequency from stroke rate
    freq = stroke_rate / 60.0  # Hz

    # Sine wave with given amplitude
    wrist_y = amplitude * np.sin(2 * np.pi * freq * timestamps)

    return wrist_y.astype(np.float32), timestamps.astype(np.float32)


class TestStrokeDetector:
    """Tests for StrokeDetector."""

    def test_detects_peaks_in_sine_wave(self):
        """Detects correct number of peaks in known sine wave."""
        from src.vision.stroke_detector import StrokeDetector

        # 10 seconds at 60 strokes/min = 10 strokes
        wrist_y, timestamps = generate_sine_wave(
            duration=10.0, fps=30.0, stroke_rate=60.0
        )

        detector = StrokeDetector()
        strokes = detector.detect_strokes(wrist_y, timestamps)

        # Should detect ~10 strokes (peaks)
        assert 9 <= len(strokes) <= 11

    def test_ignores_low_prominence_peaks(self):
        """Small oscillations below threshold ignored."""
        from src.vision.stroke_detector import StrokeDetector

        # Small amplitude = low prominence
        wrist_y, timestamps = generate_sine_wave(
            duration=5.0, fps=30.0, stroke_rate=60.0, amplitude=10.0  # Small amplitude
        )

        detector = StrokeDetector(min_peak_prominence=30.0)
        strokes = detector.detect_strokes(wrist_y, timestamps)

        # Should detect no strokes (below prominence threshold)
        assert len(strokes) == 0

    def test_min_distance_filters_noise(self):
        """Peaks too close together are filtered."""
        from src.vision.stroke_detector import StrokeDetector

        # Very fast stroke rate = peaks close together
        wrist_y, timestamps = generate_sine_wave(
            duration=5.0, fps=30.0, stroke_rate=180.0  # 3 strokes per second
        )

        # Detector with large min distance should filter some peaks
        detector = StrokeDetector(min_peak_distance=0.5)  # 0.5 seconds between strokes
        strokes = detector.detect_strokes(wrist_y, timestamps)

        # With 0.5s min distance, max ~10 peaks in 5 seconds
        assert len(strokes) <= 11

    def test_stroke_timestamps_accurate(self):
        """Detected stroke times match actual peak times."""
        from src.vision.stroke_detector import StrokeDetector

        wrist_y, timestamps = generate_sine_wave(
            duration=5.0, fps=30.0, stroke_rate=60.0
        )

        detector = StrokeDetector()
        strokes = detector.detect_strokes(wrist_y, timestamps)

        # sin(2*pi*f*t) has max at t = 1/(4*f). For f=1Hz: 0.25s, 1.25s, 2.25s, etc.
        expected_times = [0.25, 1.25, 2.25, 3.25, 4.25]

        for stroke in strokes:
            # Find closest expected time
            min_diff = min(abs(stroke.timestamp - t) for t in expected_times)
            assert min_diff < 0.1, f"Stroke at {stroke.timestamp} not near expected peak"

    def test_handles_incomplete_strokes(self):
        """Partial strokes at buffer edges handled correctly."""
        from src.vision.stroke_detector import StrokeDetector

        # Start mid-stroke
        wrist_y, timestamps = generate_sine_wave(
            duration=2.0, fps=30.0, stroke_rate=60.0
        )

        detector = StrokeDetector()
        strokes = detector.detect_strokes(wrist_y, timestamps)

        # Should still detect strokes despite incomplete edges
        assert len(strokes) >= 1

    def test_no_strokes_when_stationary(self):
        """No false positives when wrist stationary."""
        from src.vision.stroke_detector import StrokeDetector

        # Constant value (no motion)
        num_frames = 150
        wrist_y = np.full(num_frames, 200.0, dtype=np.float32)
        timestamps = np.linspace(0, 5.0, num_frames, dtype=np.float32)

        detector = StrokeDetector()
        strokes = detector.detect_strokes(wrist_y, timestamps)

        assert len(strokes) == 0

    @pytest.mark.parametrize("stroke_rate", [30, 45, 60, 75, 90])
    def test_various_stroke_rates(self, stroke_rate: int):
        """Accurately detects strokes across range of rates."""
        from src.vision.stroke_detector import StrokeDetector

        duration = 10.0
        wrist_y, timestamps = generate_sine_wave(
            duration=duration, fps=30.0, stroke_rate=float(stroke_rate)
        )

        detector = StrokeDetector()
        strokes = detector.detect_strokes(wrist_y, timestamps)

        expected_strokes = int(duration * stroke_rate / 60)
        # Allow +/- 2 strokes for edge effects
        assert abs(len(strokes) - expected_strokes) <= 2

    def test_stroke_event_fields(self):
        """StrokeEvent has correct fields."""
        from src.vision.stroke_detector import StrokeDetector, StrokeEvent

        wrist_y, timestamps = generate_sine_wave(
            duration=3.0, fps=30.0, stroke_rate=60.0
        )

        detector = StrokeDetector()
        strokes = detector.detect_strokes(wrist_y, timestamps)

        assert len(strokes) > 0
        stroke = strokes[0]

        assert isinstance(stroke, StrokeEvent)
        assert hasattr(stroke, "timestamp")
        assert hasattr(stroke, "wrist")
        assert hasattr(stroke, "confidence")
        assert stroke.wrist == "left"  # Default wrist

    def test_handles_nan_values(self):
        """Handles NaN values in trajectory (missing keypoints)."""
        from src.vision.stroke_detector import StrokeDetector

        wrist_y, timestamps = generate_sine_wave(
            duration=5.0, fps=30.0, stroke_rate=60.0
        )

        # Insert some NaN values (simulating missing keypoints)
        wrist_y[10:15] = np.nan
        wrist_y[50:55] = np.nan

        detector = StrokeDetector()
        strokes = detector.detect_strokes(wrist_y, timestamps)

        # Should still detect some strokes despite gaps
        assert len(strokes) >= 2

    def test_empty_input(self):
        """Handles empty input gracefully."""
        from src.vision.stroke_detector import StrokeDetector

        detector = StrokeDetector()
        strokes = detector.detect_strokes(np.array([]), np.array([]))

        assert len(strokes) == 0

    def test_single_frame(self):
        """Handles single frame input."""
        from src.vision.stroke_detector import StrokeDetector

        detector = StrokeDetector()
        strokes = detector.detect_strokes(
            np.array([100.0], dtype=np.float32), np.array([0.0], dtype=np.float32)
        )

        assert len(strokes) == 0
