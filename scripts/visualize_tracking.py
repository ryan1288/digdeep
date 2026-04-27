"""Visualize ball + player tracking on a rally clip.

Usage:
    conda run -n digdeep python scripts/visualize_tracking.py \\
        data/rallies/match_001_r001.mp4 \\
        [--out /tmp/out.mp4]  [--show]  [--conf 0.3]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List

import cv2
import numpy as np
from omegaconf import OmegaConf

# Ensure repo root on path when run as a plain script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.inference.ball_detector import BallDetector
from src.inference.player_detector import PlayerDetector
from src.inference.player_tracker import PlayerTracker
from src.inference.real_runner import _resolve_player_model, _resolve_reid_model
from src.pipeline.frame_result import FrameResult

# 20-colour palette — index by tracker_id % 20 (BGR order)
_COLORS: List[tuple] = [
    (56, 56, 255),   (151, 157, 255), (31, 112, 255),  (29, 178, 255),
    (49, 210, 207),  (10, 249, 72),   (23, 204, 146),  (134, 219, 61),
    (52, 147, 26),   (187, 212, 0),   (168, 153, 44),  (255, 194, 0),
    (147, 69, 52),   (255, 115, 100), (236, 24, 0),    (255, 56, 132),
    (133, 0, 82),    (255, 56, 203),  (200, 149, 255), (199, 55, 255),
]
_BALL_COLOR = (0, 255, 255)  # yellow in BGR
_UNTRACKED_COLOR = (128, 128, 128)


def _draw_players(frame: np.ndarray, detections: List[dict]) -> np.ndarray:
    """Draw player bboxes colour-coded by tracker_id.

    Args:
        frame: BGR image, modified in place.
        detections: List of dicts with keys bbox, tracker_id, conf.

    Returns:
        The same frame with rectangles and labels drawn.
    """
    for det in detections:
        tid = det["tracker_id"]
        color = _COLORS[tid % len(_COLORS)] if tid >= 0 else _UNTRACKED_COLOR
        x1, y1, x2, y2 = (int(v) for v in det["bbox"])
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = f"#{tid}" if tid >= 0 else "?"
        cv2.putText(
            frame, label, (x1, max(y1 - 5, 10)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA,
        )
    return frame


def _draw_ball(frame: np.ndarray, detections: List[dict]) -> np.ndarray:
    """Draw ball detections as yellow circles.

    Args:
        frame: BGR image, modified in place.
        detections: List of dicts with keys x, y, conf.

    Returns:
        The same frame with circles and confidence labels drawn.
    """
    for det in detections:
        cx, cy = int(det["x"]), int(det["y"])
        cv2.circle(frame, (cx, cy), 8, _BALL_COLOR, 2, cv2.LINE_AA)
        cv2.putText(
            frame, f"{det['conf']:.2f}", (cx + 10, cy),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, _BALL_COLOR, 1, cv2.LINE_AA,
        )
    return frame


def main() -> None:
    pass  # implemented in Task 3


if __name__ == "__main__":
    main()
