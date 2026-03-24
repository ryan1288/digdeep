"""FrameResult dataclass — central data carrier for the inference pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class FrameResult:
    """Carries all per-frame data through the pipeline.

    Attributes:
        frame_idx: Zero-based frame index from the source video.
        frame: BGR image array with shape (H, W, 3).
        timestamp_ms: Frame timestamp in milliseconds.
        ball_detections: List of ball detection dicts [{x, y, conf}], or None.
        player_detections: List of player detection dicts [{bbox, tracker_id, conf}], or None.
        player_actions: Map from tracker_id to action label string, or None.
        rally_state: One of 'serving' | 'in_rally' | 'dead_ball', or None.
        court_homography: 3×3 homography matrix for court-to-pixel mapping (post-MVP), or None.
    """

    frame_idx: int
    frame: np.ndarray  # H×W×3, BGR
    timestamp_ms: float
    ball_detections: Optional[List[Dict]] = None
    player_detections: Optional[List[Dict]] = None
    player_actions: Optional[Dict[int, str]] = None
    rally_state: Optional[str] = None
    court_homography: Optional[Any] = None
