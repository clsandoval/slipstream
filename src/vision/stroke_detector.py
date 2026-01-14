"""Stroke detection from wrist trajectory."""

from dataclasses import dataclass

import numpy as np
from scipy.signal import find_peaks


@dataclass
class StrokeEvent:
    """A detected stroke."""

    timestamp: float
    wrist: str  # "left" | "right"
    confidence: float


class StrokeDetector:
    """
    Detects stroke cycles from wrist trajectory.

    Algorithm:
    1. Track wrist Y-position over time
    2. Detect peaks (local maxima) in Y-position
    3. Each peak = one stroke completed
    4. Filter by minimum peak prominence to avoid noise
    """

    def __init__(
        self,
        min_peak_prominence: float = 30.0,  # pixels
        min_peak_distance: float = 0.3,  # seconds between strokes
    ):
        """
        Initialize stroke detector.

        Args:
            min_peak_prominence: Minimum height difference to count as peak (pixels)
            min_peak_distance: Minimum time between strokes (seconds)
        """
        self.min_peak_prominence = min_peak_prominence
        self.min_peak_distance = min_peak_distance

    def detect_strokes(
        self,
        wrist_y: np.ndarray,
        timestamps: np.ndarray,
        wrist: str = "left",
    ) -> list[StrokeEvent]:
        """
        Detect strokes from wrist trajectory.

        Uses scipy.signal.find_peaks for peak detection.

        Args:
            wrist_y: Array of wrist Y positions
            timestamps: Array of timestamps corresponding to positions
            wrist: Which wrist this trajectory is from ("left" or "right")

        Returns:
            List of detected StrokeEvent objects
        """
        if len(wrist_y) < 3 or len(timestamps) < 3:
            return []

        # Handle NaN values by interpolating
        wrist_y_clean = self._interpolate_nans(wrist_y)

        if len(wrist_y_clean) < 3:
            return []

        # Calculate sample rate from timestamps
        if len(timestamps) >= 2:
            dt = np.median(np.diff(timestamps))
            if dt <= 0:
                dt = 1 / 30.0  # Default to 30 fps
        else:
            dt = 1 / 30.0

        # Convert min_peak_distance from seconds to samples
        min_distance_samples = max(1, int(self.min_peak_distance / dt))

        # Find peaks
        peaks, properties = find_peaks(
            wrist_y_clean,
            prominence=self.min_peak_prominence,
            distance=min_distance_samples,
        )

        # Convert peaks to StrokeEvents
        strokes = []
        for i, peak_idx in enumerate(peaks):
            if peak_idx < len(timestamps):
                # Get prominence as confidence measure (normalized)
                prominence = properties["prominences"][i]
                confidence = min(1.0, prominence / (2 * self.min_peak_prominence))

                strokes.append(
                    StrokeEvent(
                        timestamp=float(timestamps[peak_idx]),
                        wrist=wrist,
                        confidence=confidence,
                    )
                )

        return strokes

    def _interpolate_nans(self, arr: np.ndarray) -> np.ndarray:
        """Interpolate NaN values in array."""
        if len(arr) == 0:
            return arr

        # Find NaN indices
        nan_mask = np.isnan(arr)

        if not np.any(nan_mask):
            return arr

        if np.all(nan_mask):
            return np.array([])

        # Create copy for interpolation
        result = arr.copy()

        # Get valid indices
        valid_indices = np.where(~nan_mask)[0]
        nan_indices = np.where(nan_mask)[0]

        # Interpolate NaN values
        result[nan_indices] = np.interp(nan_indices, valid_indices, arr[valid_indices])

        return result
