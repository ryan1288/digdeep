"""Stub pipeline runner — no ONNX or model weights required.

Returns empty rally list; real detection will replace this in Phase 2.
"""

from __future__ import annotations

from typing import Callable, List

import cv2


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
) -> List[dict]:
    """Run the stub inference pipeline over a video file.

    Iterates every frame and emits progress/stage callbacks. Returns an empty
    rally list — real detection will replace this stub in Phase 2.

    Args:
        video_path: Path to the input video.
        progress_cb: Called with the current frame index every
            ``progress_interval`` frames.
        stage_cb: Called with a human-readable stage label at key transitions.
        progress_interval: Number of frames between ``progress_cb`` calls.

    Returns:
        List of rally dicts (empty stub).
    """
    stage_cb("Detecting ball...")
    cap = cv2.VideoCapture(video_path)
    frame_idx = 0

    while True:
        ret, _ = cap.read()
        if not ret:
            break
        if frame_idx % progress_interval == 0:
            progress_cb(frame_idx)
        frame_idx += 1

    cap.release()

    stage_cb("Detecting players...")
    stage_cb("Detecting rallies...")

    return []
