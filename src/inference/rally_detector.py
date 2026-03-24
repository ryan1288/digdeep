"""Tier 1 rally detector — ball-presence threshold with median filter."""

from collections import deque
from typing import List, Tuple

from omegaconf import DictConfig

from src.pipeline.base import PipelineModule
from src.pipeline.frame_result import FrameResult


class RallyDetector(PipelineModule):
    """Detects rally boundaries from the ball-presence signal in FrameResults.

    Uses a binary ball-visible signal (conf > threshold) median-filtered over
    a short window to suppress flicker, then applies hysteresis:

    - Rally **starts** after the ball has been visible for ``rally_start_frames``
      consecutive (post-filter) frames.
    - Rally **ends** after the ball has been absent for ``rally_end_frames``
      consecutive frames.
    - Segments shorter than ``min_rally_frames`` are discarded (set to dead_ball).

    Reads:  frame_result.ball_detections
    Writes: frame_result.rally_state  →  'in_rally' | 'dead_ball'

    Config keys (rally_detector.yaml):
        conf_threshold (float):    Ball confidence required to count as visible (default 0.5).
        median_window (int):       Median-filter width in frames (default 15, must be odd).
        rally_start_frames (int):  Consecutive visible frames to open a rally (default 30).
        rally_end_frames (int):    Consecutive absent frames to close a rally (default 90).
        min_rally_frames (int):    Minimum rally length; shorter segments become dead_ball (default 90).
    """

    def __init__(self, cfg: DictConfig) -> None:
        super().__init__(cfg)

        self._conf_threshold: float = float(cfg.get("conf_threshold", 0.5))
        self._median_window: int = int(cfg.get("median_window", 15))
        self._rally_start_frames: int = int(cfg.get("rally_start_frames", 30))
        self._rally_end_frames: int = int(cfg.get("rally_end_frames", 90))
        self._min_rally_frames: int = int(cfg.get("min_rally_frames", 90))

        # Rolling window of raw binary ball-present signals (1 or 0).
        self._signal_window: deque = deque(
            [0] * self._median_window, maxlen=self._median_window
        )

        # Hysteresis counters.
        self._visible_streak: int = 0
        self._absent_streak: int = 0
        self._in_rally: bool = False
        self._rally_start_frame: int = 0
        self._current_frame_idx: int = 0

    # ------------------------------------------------------------------
    # PipelineModule interface
    # ------------------------------------------------------------------

    def process(self, frame_result: FrameResult) -> FrameResult:
        """Update rally state for a single frame.

        Args:
            frame_result: Carrier with ball_detections populated.

        Returns:
            frame_result with rally_state set to 'in_rally' or 'dead_ball'.
        """
        self._current_frame_idx = frame_result.frame_idx
        raw = self._ball_visible(frame_result)
        filtered = self._median_filter(raw)
        self._update_state(filtered)
        frame_result.rally_state = "in_rally" if self._in_rally else "dead_ball"
        return frame_result

    # ------------------------------------------------------------------
    # Batch API
    # ------------------------------------------------------------------

    def detect_rallies(self, frames: List[FrameResult]) -> List[Tuple[int, int]]:
        """Process a full list of frames and return rally (start, end) pairs.

        Resets internal state before processing so this can be called on an
        already-used detector.  Short segments (< min_rally_frames) are
        automatically dropped.

        Args:
            frames: Ordered list of FrameResults with ball_detections populated.

        Returns:
            List of (start_frame_idx, end_frame_idx) tuples, one per rally.
        """
        self._reset()

        # Track per-frame states to identify segment boundaries.
        states: List[str] = []
        for fr in frames:
            self.process(fr)
            states.append(fr.rally_state)

        return self._extract_segments(frames, states)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _reset(self) -> None:
        """Reset all stateful counters (used at start of detect_rallies)."""
        self._signal_window = deque(
            [0] * self._median_window, maxlen=self._median_window
        )
        self._visible_streak = 0
        self._absent_streak = 0
        self._in_rally = False
        self._rally_start_frame = 0
        self._current_frame_idx = 0

    def _ball_visible(self, frame_result: FrameResult) -> int:
        """Return 1 if any detection exceeds the confidence threshold, else 0."""
        dets = frame_result.ball_detections or []
        return int(any(d.get("conf", 0.0) >= self._conf_threshold for d in dets))

    def _median_filter(self, raw: int) -> int:
        """Push raw signal into the window and return the median (0 or 1)."""
        self._signal_window.append(raw)
        mid = self._median_window // 2
        return int(sorted(self._signal_window)[mid] >= 0.5)

    def _update_state(self, filtered: int) -> None:
        """Apply hysteresis logic to transition in/out of rally state."""
        if filtered:
            self._visible_streak += 1
            self._absent_streak = 0
            if not self._in_rally and self._visible_streak >= self._rally_start_frames:
                self._in_rally = True
                # Back-date the rally start by the streak we needed to confirm it.
                self._rally_start_frame = (
                    self._current_frame_idx - self._rally_start_frames + 1
                )
        else:
            self._absent_streak += 1
            self._visible_streak = 0
            if self._in_rally and self._absent_streak >= self._rally_end_frames:
                self._in_rally = False

    def _extract_segments(
        self, frames: List[FrameResult], states: List[str]
    ) -> List[Tuple[int, int]]:
        """Scan rally_state labels and return (start, end) pairs, dropping short ones.

        Args:
            frames: Original frame list (used to read frame_idx values).
            states: Parallel list of rally_state strings.

        Returns:
            Filtered list of (start_frame_idx, end_frame_idx) tuples.
        """
        rallies: List[Tuple[int, int]] = []
        in_seg = False
        seg_start = 0

        for i, state in enumerate(states):
            if state == "in_rally" and not in_seg:
                in_seg = True
                seg_start = frames[i].frame_idx
            elif state != "in_rally" and in_seg:
                in_seg = False
                seg_end = frames[i - 1].frame_idx
                length = seg_end - seg_start + 1
                if length >= self._min_rally_frames:
                    rallies.append((seg_start, seg_end))

        # Close any segment still open at end of stream.
        if in_seg:
            seg_end = frames[-1].frame_idx
            length = seg_end - seg_start + 1
            if length >= self._min_rally_frames:
                rallies.append((seg_start, seg_end))

        return rallies
