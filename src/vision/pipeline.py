"""Main vision processing pipeline."""

from datetime import datetime

import numpy as np

from src.vision.keypoint_buffer import KeypointBuffer
from src.vision.protocols import PoseEstimatorProtocol, VideoSourceProtocol
from src.vision.rate_calculator import RateCalculator
from src.vision.state_store import StateStore
from src.vision.stroke_detector import StrokeDetector


class VisionPipeline:
    """
    Main vision processing pipeline.

    Orchestrates: video -> pose estimation -> stroke detection -> state updates
    """

    def __init__(
        self,
        pose_estimator: PoseEstimatorProtocol,
        state_store: StateStore,
        buffer_size: int = 300,
        rate_window: float = 15.0,
        confidence_threshold: float = 0.5,
    ):
        """
        Initialize the vision pipeline.

        Args:
            pose_estimator: Pose estimation implementation
            state_store: State store for swim session data
            buffer_size: Number of frames to buffer for analysis
            rate_window: Time window for rate calculation (seconds)
            confidence_threshold: Minimum confidence for valid keypoints
        """
        self.pose_estimator = pose_estimator
        self.state_store = state_store
        self.buffer = KeypointBuffer(
            max_size=buffer_size,
            min_confidence=confidence_threshold,
        )
        self.stroke_detector = StrokeDetector()
        self.rate_calculator = RateCalculator(window_seconds=rate_window)

        # Track the timestamp of last processed stroke to avoid duplicates
        self._last_stroke_timestamp: float = -1.0

    def process_frame(
        self, frame: np.ndarray, timestamp: float, frame_index: int
    ) -> None:
        """
        Process a single video frame.

        Args:
            frame: BGR image as numpy array
            timestamp: Frame timestamp in seconds
            frame_index: Frame number in sequence
        """
        # 1. Estimate pose
        pose = self.pose_estimator.estimate(frame, timestamp, frame_index)

        # 2. Update buffer and detect strokes
        new_strokes = []
        if pose is not None:
            self.buffer.add(pose)

            # 3. Detect strokes from trajectory (pre-filtered for confident keypoints)
            if len(self.buffer) > 10:  # Need enough data
                wrist_y, wrist_timestamps = self.buffer.get_wrist_trajectory("left")
                strokes = self.stroke_detector.detect_strokes(wrist_y, wrist_timestamps)

                # Only add strokes we haven't seen yet (by timestamp)
                for stroke in strokes:
                    if stroke.timestamp > self._last_stroke_timestamp:
                        new_strokes.append(stroke)
                        self._last_stroke_timestamp = stroke.timestamp

        # 4. Update rate calculator with new strokes
        for stroke in new_strokes:
            self.rate_calculator.add_stroke(stroke.timestamp)

        # 5. Calculate rate (also updates internal rate_history)
        rate = self.rate_calculator.get_rate(timestamp)

        # 6. Update state (includes rate_history for Claude/dashboard)
        self.state_store.update(
            pose_detected=pose is not None,
            stroke_count=self.rate_calculator.get_stroke_count(),
            stroke_rate=rate,
            rate_history=self.rate_calculator.get_rate_history(),
            last_stroke_time=datetime.now() if new_strokes else None,
            is_swimming=pose is not None and rate > 0,
        )

    def run(self, video_source: VideoSourceProtocol) -> None:
        """
        Run pipeline on video source until exhausted.

        Args:
            video_source: Video source to process
        """
        try:
            for frame, timestamp, frame_index in video_source.frames():
                self.process_frame(frame, timestamp, frame_index)
        finally:
            video_source.close()

    def reset(self) -> None:
        """Reset pipeline state for a new session."""
        self.buffer.clear()
        self.rate_calculator.reset()
        self._last_stroke_timestamp = -1.0
