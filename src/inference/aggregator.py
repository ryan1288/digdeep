"""AnalyticsAggregator — PipelineModule stub that outputs the target JSON schema."""

from __future__ import annotations

from typing import Any, Dict, List

from omegaconf import DictConfig

from src.pipeline.base import PipelineModule
from src.pipeline.frame_result import FrameResult

ACTION_LABELS = ("serve", "receive", "set", "attack", "block")


class AnalyticsAggregator(PipelineModule):
    """Final pipeline stage: passes frames through unchanged and produces analytics JSON.

    ``process()`` is a no-op — it returns the FrameResult untouched so the module
    can sit at the end of the pipeline without affecting upstream outputs.

    ``finalize()`` consumes the processed frame list and returns the analytics output
    schema defined in CLAUDE.md, with all counters at zero and lists empty (stub).
    Post-MVP implementations will fill the accumulators from frame_result fields.

    Reads:  nothing (pass-through)
    Writes: nothing (pass-through)

    Config keys (aggregator.yaml):
        fps (float): Frames-per-second of the source video, used to compute
                     rally duration_sec from frame indices (default 30.0).
    """

    def __init__(self, cfg: DictConfig) -> None:
        super().__init__(cfg)
        self._fps: float = float(cfg.get("fps", 30.0))

    # ------------------------------------------------------------------
    # PipelineModule interface
    # ------------------------------------------------------------------

    def process(self, frame_result: FrameResult) -> FrameResult:
        """Pass the frame through unchanged.

        Args:
            frame_result: Any FrameResult from upstream modules.

        Returns:
            The same frame_result, unmodified.
        """
        return frame_result

    # ------------------------------------------------------------------
    # Batch finalization
    # ------------------------------------------------------------------

    def finalize(self, frames: List[FrameResult]) -> Dict[str, Any]:
        """Produce the analytics output schema from a completed frame list.

        Returns the correct schema structure with zero counts and empty lists.
        Future implementations will accumulate real values from frame fields.

        Args:
            frames: All FrameResults produced by the pipeline for one video.

        Returns:
            Dict with keys:
              "players": {track_id -> per-player analytics dict}
              "rallies": [{"start_frame", "end_frame", "duration_sec"}, ...]
        """
        players = self._aggregate_players(frames)
        rallies = self._aggregate_rallies(frames)
        return {"players": players, "rallies": rallies}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _aggregate_players(
        self, frames: List[FrameResult]
    ) -> Dict[int, Dict[str, Any]]:
        """Build per-player schema entries (stub: zero counts, empty lists).

        Collects all track IDs observed in player_actions across the frame list.

        Args:
            frames: Processed FrameResult list.

        Returns:
            Dict mapping track_id → analytics dict.
        """
        track_ids: set[int] = set()
        for fr in frames:
            if fr.player_actions:
                track_ids.update(fr.player_actions.keys())

        return {
            tid: {
                "track_id": tid,
                "action_counts": {label: 0 for label in ACTION_LABELS},
                "ball_contacts": [],
                "court_positions": [],
                "ball_contacts_3d": [],
            }
            for tid in track_ids
        }

    def _aggregate_rallies(self, frames: List[FrameResult]) -> List[Dict[str, Any]]:
        """Extract rally segments from rally_state labels.

        Scans rally_state across frames and emits one dict per contiguous
        'in_rally' segment.  duration_sec is computed from frame indices and
        the configured fps.

        Args:
            frames: Processed FrameResult list (rally_state populated by RallyDetector).

        Returns:
            List of rally dicts: [{"start_frame", "end_frame", "duration_sec"}, ...]
        """
        rallies: List[Dict[str, Any]] = []
        in_seg = False
        seg_start_idx = 0

        for i, fr in enumerate(frames):
            if fr.rally_state == "in_rally" and not in_seg:
                in_seg = True
                seg_start_idx = fr.frame_idx
            elif fr.rally_state != "in_rally" and in_seg:
                in_seg = False
                seg_end_idx = frames[i - 1].frame_idx
                rallies.append(_rally_entry(seg_start_idx, seg_end_idx, self._fps))

        if in_seg:
            rallies.append(_rally_entry(seg_start_idx, frames[-1].frame_idx, self._fps))

        return rallies


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _rally_entry(start_frame: int, end_frame: int, fps: float) -> Dict[str, Any]:
    return {
        "start_frame": start_frame,
        "end_frame": end_frame,
        "duration_sec": round((end_frame - start_frame + 1) / fps, 3),
    }
