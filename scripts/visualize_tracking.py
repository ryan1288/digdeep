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
from typing import List, Tuple

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
_COLORS: List[Tuple[int, int, int]] = [
    (56, 56, 255),
    (151, 157, 255),
    (31, 112, 255),
    (29, 178, 255),
    (49, 210, 207),
    (10, 249, 72),
    (23, 204, 146),
    (134, 219, 61),
    (52, 147, 26),
    (187, 212, 0),
    (168, 153, 44),
    (255, 194, 0),
    (147, 69, 52),
    (255, 115, 100),
    (236, 24, 0),
    (255, 56, 132),
    (133, 0, 82),
    (255, 56, 203),
    (200, 149, 255),
    (199, 55, 255),
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
            frame,
            label,
            (x1, max(y1 - 5, 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
            cv2.LINE_AA,
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
            frame,
            f"{det['conf']:.2f}",
            (cx + 10, cy),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            _BALL_COLOR,
            1,
            cv2.LINE_AA,
        )
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Visualise ball + player tracking on a rally clip."
    )
    parser.add_argument("video", help="Path to input video file")
    parser.add_argument(
        "--out", default=None, help="Output video path (default: <stem>_tracked.mp4)"
    )
    parser.add_argument("--show", action="store_true", help="Show live preview window")
    parser.add_argument(
        "--conf", type=float, default=0.5, help="Detection confidence threshold"
    )
    args = parser.parse_args()

    video_path = str(Path(args.video).expanduser().resolve())
    if not Path(video_path).exists():
        sys.exit(f"ERROR: video not found: {video_path}")

    out_path = args.out or str(
        Path(video_path).with_name(Path(video_path).stem + "_tracked.mp4")
    )

    # ── Build module configs ──────────────────────────────────────────────────
    ball_model_path = os.environ.get("DIGDEEP_BALL_MODEL") or str(
        Path.home()
        / "digdeep-training"
        / "models"
        / "VballNetFastV1_seq9_grayscale_233_h288_w512.onnx"
    )
    ball_cfg = OmegaConf.create(
        {
            "model_path": ball_model_path,
            "input_h": 288,
            "input_w": 512,
            "seq_len": 9,
            "conf_threshold": args.conf,
        }
    )
    player_cfg = OmegaConf.create(
        {
            "model_path": _resolve_player_model(None),
            "resolution": 560,
            "conf_threshold": args.conf,
        }
    )
    tracker_cfg = OmegaConf.create(
        {
            "reid_weights_path": _resolve_reid_model(None),
            "lost_buffer": 200,
        }
    )

    # ── Initialise modules ────────────────────────────────────────────────────
    print("Loading models...")
    ball_detector = BallDetector(ball_cfg)
    player_detector = PlayerDetector(player_cfg)
    player_tracker = PlayerTracker(tracker_cfg)

    # ── Open video ────────────────────────────────────────────────────────────
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        sys.exit(f"ERROR: cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    writer = cv2.VideoWriter(
        out_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )

    print(f"Processing {total} frames → {out_path}")
    frame_idx = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            fr = FrameResult(
                frame_idx=frame_idx,
                frame=frame,
                timestamp_ms=frame_idx * 1000.0 / fps,
            )
            fr = ball_detector.process(fr)
            fr = player_detector.process(fr)
            fr = player_tracker.process(fr)

            annotated = frame.copy()
            if fr.player_detections:
                annotated = _draw_players(annotated, fr.player_detections)
            if fr.ball_detections:
                annotated = _draw_ball(annotated, fr.ball_detections)

            writer.write(annotated)

            if args.show:
                cv2.imshow("tracking", annotated)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            if frame_idx % 100 == 0:
                print(f"  frame {frame_idx}/{total}")

            frame_idx += 1
    finally:
        cap.release()
        writer.release()
        if args.show:
            cv2.destroyAllWindows()

    print(f"Done. Wrote {frame_idx} frames to {out_path}")


if __name__ == "__main__":
    main()
