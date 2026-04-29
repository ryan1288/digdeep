"""Real inference pipeline runner — 5-stage: decode, ball, player, track, rally.

Replaces stub_runner.py for production use.  Worker.py imports from here once
model weights are available.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, List, Tuple

import cv2
from omegaconf import DictConfig, OmegaConf

from src.inference.ball_detector import BallDetector
from src.inference.player_detector import PlayerDetector
from src.inference.player_tracker import PlayerTracker
from src.inference.rally_detector import RallyDetector
from src.inference.utils import get_video_frame_count
from src.pipeline.frame_result import FrameResult
from src.pipeline.rally_utils import extract_rally_segments

_DEFAULT_BALL_MODEL_CACHE = str(
    Path.home()
    / ".cache"
    / "digdeep"
    / "models"
    / "VballNetFastV1_seq9_grayscale_233_h288_w512.onnx"
)
_DEFAULT_BALL_MODEL_DEV = str(
    Path.home()
    / "digdeep-training"
    / "models"
    / "VballNetFastV1_seq9_grayscale_233_h288_w512.onnx"
)
_DEFAULT_PLAYER_MODEL_CACHE = str(
    Path.home() / ".cache" / "digdeep" / "models" / "rf_detr_base.onnx"
)
_DEFAULT_PLAYER_MODEL_DEV = str(
    Path.home() / "digdeep-training" / "models" / "checkpoints" / "rf_detr_base.onnx"
)
_DEFAULT_REID_CACHE = str(
    Path.home() / ".cache" / "digdeep" / "models" / "osnet_x0_25_msmt17.pt"
)
_DEFAULT_REID_DEV = str(
    Path.home() / "digdeep-training" / "models" / "reid" / "osnet_x0_25_msmt17.pt"
)


def _resolve_ball_model(cfg: DictConfig | None) -> str:
    return (
        os.environ.get("DIGDEEP_BALL_MODEL")
        or (cfg.get("ball_model_path", None) if cfg is not None else None)
        or (
            _DEFAULT_BALL_MODEL_CACHE
            if Path(_DEFAULT_BALL_MODEL_CACHE).exists()
            else _DEFAULT_BALL_MODEL_DEV
        )
    )


def _resolve_player_model(cfg: DictConfig | None) -> str:
    return (
        os.environ.get("DIGDEEP_PLAYER_MODEL")
        or (cfg.get("player_model_path", None) if cfg is not None else None)
        or (
            _DEFAULT_PLAYER_MODEL_CACHE
            if Path(_DEFAULT_PLAYER_MODEL_CACHE).exists()
            else _DEFAULT_PLAYER_MODEL_DEV
        )
    )


def _resolve_reid_model(cfg: DictConfig | None) -> str:
    return (
        os.environ.get("DIGDEEP_REID_MODEL")
        or (cfg.get("reid_model_path", None) if cfg is not None else None)
        or (
            _DEFAULT_REID_CACHE
            if Path(_DEFAULT_REID_CACHE).exists()
            else _DEFAULT_REID_DEV
        )
    )


def run_pipeline(
    video_path: str,
    progress_cb: Callable[[int], None],
    stage_cb: Callable[[str], None],
    progress_interval: int = 100,
    cfg: DictConfig | None = None,
) -> List[dict]:
    """Run the full 5-stage inference pipeline over a video file.

    Stage callbacks emitted (matched by processing_view._STAGE_KEYWORDS):
        "Decoding video..."    → "decoding" → stage 0
        "Detecting ball..."    → "ball"      → stage 1
        "Finding players..."   → "player"    → stage 2
        "Linking players..."   → "linking"   → stage 3
        "Detecting rallies..." → "rally"     → stage 4

    Args:
        video_path: Path to the input video.
        progress_cb: Called with the current frame index every
            ``progress_interval`` frames.
        stage_cb: Called with a human-readable stage label at key transitions.
        progress_interval: Number of frames between ``progress_cb`` calls.
        cfg: App config DictConfig.

    Returns:
        List of rally dicts [{"start_sec": float, "end_sec": float}].
        Empty list if no rallies detected.
    """
    ball_model_path = _resolve_ball_model(cfg)
    player_model_path = _resolve_player_model(cfg)
    reid_model_path = _resolve_reid_model(cfg)

    ball_cfg = OmegaConf.create(
        {
            "model_path": ball_model_path,
            "input_h": 288,
            "input_w": 512,
            "seq_len": 9,
            "conf_threshold": 0.5,
        }
    )
    player_cfg = OmegaConf.create(
        {"model_path": player_model_path, "resolution": 560, "conf_threshold": 0.5}
    )
    tracker_cfg = OmegaConf.create(
        {"reid_weights_path": reid_model_path, "lost_buffer": 200}
    )
    rally_cfg = OmegaConf.create(
        {
            "conf_threshold": 0.5,
            "median_window": 15,
            "rally_start_frames": 30,
            "rally_end_frames": 90,
            "min_rally_frames": 90,
        }
    )

    stage_cb("Decoding video...")
    cap = cv2.VideoCapture(video_path)
    fps: float = cap.get(cv2.CAP_PROP_FPS) or 30.0

    stage_cb("Detecting ball...")
    ball_detector = BallDetector(ball_cfg)
    stage_cb("Finding players...")
    player_detector = PlayerDetector(player_cfg)
    stage_cb("Linking players...")
    player_tracker = PlayerTracker(tracker_cfg)
    stage_cb("Detecting rally state...")
    rally_detector = RallyDetector(rally_cfg)

    states: List[Tuple[int, str]] = []
    frame_idx = 0

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
        fr = rally_detector.process(fr)
        states.append((frame_idx, fr.rally_state or "dead_ball"))

        if frame_idx % progress_interval == 0:
            progress_cb(frame_idx)

        frame_idx += 1

    cap.release()
    min_frames = int(rally_cfg.min_rally_frames)
    segments = extract_rally_segments(states, min_frames)
    return [{"start_sec": s / fps, "end_sec": (e + 1) / fps} for s, e in segments]
