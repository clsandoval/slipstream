"""Shared fixtures for vision tests."""

import numpy as np
import pytest


@pytest.fixture
def valid_keypoints() -> np.ndarray:
    """Valid COCO-format keypoints (17, 3) with x, y, confidence."""
    keypoints = np.zeros((17, 3), dtype=np.float32)
    # Set some base positions (rough swimming pose)
    base_positions = [
        (320, 100),   # 0: nose
        (310, 90),    # 1: left_eye
        (330, 90),    # 2: right_eye
        (300, 95),    # 3: left_ear
        (340, 95),    # 4: right_ear
        (280, 150),   # 5: left_shoulder
        (360, 150),   # 6: right_shoulder
        (250, 200),   # 7: left_elbow
        (390, 200),   # 8: right_elbow
        (220, 250),   # 9: left_wrist
        (420, 250),   # 10: right_wrist
        (290, 300),   # 11: left_hip
        (350, 300),   # 12: right_hip
        (280, 400),   # 13: left_knee
        (360, 400),   # 14: right_knee
        (270, 500),   # 15: left_ankle
        (370, 500),   # 16: right_ankle
    ]
    for i, (x, y) in enumerate(base_positions):
        keypoints[i] = [x, y, 0.95]  # High confidence
    return keypoints


@pytest.fixture
def low_confidence_keypoints(valid_keypoints: np.ndarray) -> np.ndarray:
    """Keypoints with low confidence values."""
    keypoints = valid_keypoints.copy()
    keypoints[:, 2] = 0.2  # Low confidence
    return keypoints
