"""Shared inference utilities."""

from __future__ import annotations

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
