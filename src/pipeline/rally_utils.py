"""Shared rally-segment extraction primitive."""

from __future__ import annotations

from typing import List, Tuple


def extract_rally_segments(
    states: List[Tuple[int, str]],
    min_frames: int = 0,
) -> List[Tuple[int, int]]:
    """Scan (frame_idx, rally_state) pairs and return inclusive rally intervals.

    Consecutive 'in_rally' frames are collapsed into (start, end) pairs where
    both indices are inclusive.  Segments shorter than ``min_frames`` are
    discarded.

    Args:
        states: Ordered list of (frame_idx, rally_state) tuples.
        min_frames: Minimum segment length in frames (inclusive endpoints).

    Returns:
        List of (start_frame_idx, end_frame_idx) tuples, one per rally.
    """
    segments: List[Tuple[int, int]] = []
    in_seg = False
    seg_start = 0
    prev_idx = 0

    for frame_idx, state in states:
        if state == "in_rally" and not in_seg:
            in_seg = True
            seg_start = frame_idx
        elif state != "in_rally" and in_seg:
            in_seg = False
            seg_end = prev_idx
            if seg_end - seg_start + 1 >= min_frames:
                segments.append((seg_start, seg_end))
        prev_idx = frame_idx

    if in_seg and states:
        seg_end = states[-1][0]
        if seg_end - seg_start + 1 >= min_frames:
            segments.append((seg_start, seg_end))

    return segments
