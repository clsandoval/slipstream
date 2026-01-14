"""Stroke rate calculation from detected strokes."""

from collections import deque
from dataclasses import dataclass


@dataclass
class RateSample:
    """A single stroke rate measurement."""

    timestamp: float
    rate: float


class RateCalculator:
    """
    Calculates stroke rate from detected strokes.

    Uses a rolling window (default 15 seconds) to smooth rate calculation.
    Maintains rate history for Claude/dashboard to analyze trends.
    """

    def __init__(
        self,
        window_seconds: float = 15.0,
        history_max_samples: int = 60,  # ~5 min at 5s intervals
        sample_interval: float = 5.0,  # Record rate every 5 seconds
    ):
        """
        Initialize rate calculator.

        Args:
            window_seconds: Time window for rate calculation
            history_max_samples: Maximum rate samples to keep
            sample_interval: How often to record rate samples
        """
        self.window_seconds = window_seconds
        self._stroke_times: list[float] = []
        self._rate_history: deque[RateSample] = deque(maxlen=history_max_samples)
        self._last_sample_time: float = -sample_interval  # Allow immediate first sample
        self._sample_interval = sample_interval

    def add_stroke(self, timestamp: float) -> None:
        """Record a stroke event."""
        self._stroke_times.append(timestamp)

    def get_rate(self, current_time: float) -> float:
        """
        Calculate current stroke rate in strokes/minute.

        Only considers strokes within the rolling window.
        Also records to rate_history at sample_interval.

        Args:
            current_time: Current timestamp for window calculation

        Returns:
            Stroke rate in strokes per minute
        """
        # Get strokes within window
        window_start = current_time - self.window_seconds
        strokes_in_window = [t for t in self._stroke_times if t >= window_start]

        # Need at least 2 strokes to calculate rate
        if len(strokes_in_window) < 2:
            rate = 0.0
        else:
            # Calculate rate from strokes in window
            # Rate = (num_strokes - 1) / time_span * 60
            time_span = strokes_in_window[-1] - strokes_in_window[0]

            if time_span <= 0:
                rate = 0.0
            else:
                rate = (len(strokes_in_window) - 1) / time_span * 60.0

        # Record rate sample at intervals
        if current_time - self._last_sample_time >= self._sample_interval:
            self._rate_history.append(RateSample(timestamp=current_time, rate=rate))
            self._last_sample_time = current_time

        return rate

    def get_rate_history(self, last_n: int | None = None) -> list[RateSample]:
        """
        Get recent rate samples for trend analysis.

        Claude can derive trends from this: [58, 59, 60, 61, 62] -> increasing
        Dashboard can plot this as a sparkline.

        Args:
            last_n: Return only the last N samples (None for all)

        Returns:
            List of RateSample objects
        """
        history = list(self._rate_history)
        if last_n is not None:
            return history[-last_n:]
        return history

    def get_stroke_count(self) -> int:
        """Total strokes recorded in session."""
        return len(self._stroke_times)

    def reset(self) -> None:
        """Clear all stroke history and rate samples."""
        self._stroke_times.clear()
        self._rate_history.clear()
        self._last_sample_time = -self._sample_interval
