"""Real inference pipeline runner — BallDetector + RallyDetector over a video file.

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
from src.inference.rally_detector import RallyDetector
from src.pipeline.frame_result import FrameResult

# Default ball model path — override with DIGDEEP_BALL_MODEL env var or
# ball_model_path key in app.yaml (set in configs/app/app.yaml).
_DEFAULT_BALL_MODEL = str(
    Path.home() / "digdeep-training" / "models" / "VballNetFastV1_seq9_grayscale_233_h288_w512.onnx"
)


def get_video_frame_count(path: str) -> int:
    """Return the total frame count of a video file.

    Args:
        path: Path to the video file.

    Returns:
        Total number of frames, or 0 if the file cannot be opened.
    """
    cap = cv2.VideoCapture(path)
    count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return count


def run_pipeline(
    video_path: str,
    progress_cb: Callable[[int], None],
    stage_cb: Callable[[str], None],
    progress_interval: int = 100,
    cfg: DictConfig | None = None,
) -> List[dict]:
    """Run ball detection + rally detection over a video file.

    Processes frames one at a time (memory-efficient) and returns the list of
    detected rally intervals.

    Args:
        video_path: Path to the input video.
        progress_cb: Called with the current frame index every
            ``progress_interval`` frames.
        stage_cb: Called with a human-readable stage label at key transitions.
        progress_interval: Number of frames between ``progress_cb`` calls.
        cfg: App config DictConfig. Used for ``ball_model_path`` override.

    Returns:
        List of rally dicts [{"start_sec": float, "end_sec": float}].
        Empty list if no rallies detected.
    """
    ball_model_path = (
        os.environ.get("DIGDEEP_BALL_MODEL")
        or (cfg.get("ball_model_path", None) if cfg is not None else None)
        or _DEFAULT_BALL_MODEL
    )

    if not Path(ball_model_path).exists():
        raise FileNotFoundError(
            f"Ball detector model not found: {ball_model_path}\n"
            "Set DIGDEEP_BALL_MODEL env var or ball_model_path in configs/app/app.yaml."
        )

    ball_cfg = OmegaConf.create(
        {
            "model_path": ball_model_path,
            "input_h": 288,
            "input_w": 512,
            "seq_len": 9,
            "conf_threshold": 0.5,
        }
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

    stage_cb("Loading models...")
    ball_detector = BallDetector(ball_cfg)
    rally_detector = RallyDetector(rally_cfg)

    cap = cv2.VideoCapture(video_path)
    fps: float = cap.get(cv2.CAP_PROP_FPS) or 30.0

    stage_cb("Detecting ball and rallies...")
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
        fr = rally_detector.process(fr)
        states.append((frame_idx, fr.rally_state or "dead_ball"))

        if frame_idx % progress_interval == 0:
            progress_cb(frame_idx)

        frame_idx += 1

    cap.release()

    stage_cb("Extracting rally segments...")
    min_frames = int(rally_cfg.min_rally_frames)
    return _extract_rally_intervals(states, fps, min_frames)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _extract_rally_intervals(
    states: List[Tuple[int, str]],
    fps: float,
    min_frames: int,
) -> List[dict]:
    """Convert (frame_idx, rally_state) pairs to rally time intervals.

    Applies a minimum-length filter: segments shorter than ``min_frames``
    are discarded.

    Args:
        states: List of (frame_idx, rally_state) tuples in order.
        fps: Video frame rate, used to convert frame indices to seconds.
        min_frames: Minimum segment length in frames.

    Returns:
        List of {"start_sec": float, "end_sec": float} dicts.
    """
    rallies: List[dict] = []
    in_seg = False
    seg_start = 0

    for frame_idx, state in states:
        if state == "in_rally" and not in_seg:
            in_seg = True
            seg_start = frame_idx
        elif state != "in_rally" and in_seg:
            in_seg = False
            length = frame_idx - seg_start
            if length >= min_frames:
                rallies.append(
                    {"start_sec": seg_start / fps, "end_sec": frame_idx / fps}
                )

    # Close any segment open at end of stream.
    if in_seg and states:
        last_idx = states[-1][0]
        length = last_idx - seg_start + 1
        if length >= min_frames:
            rallies.append(
                {"start_sec": seg_start / fps, "end_sec": last_idx / fps}
            )

    return rallies
