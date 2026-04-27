"""Player tracker module — BoT-SORT-ReID wrapper (BoxMOT)."""

from __future__ import annotations

from pathlib import Path
from typing import List

import numpy as np
import torch
from boxmot import BotSort
from omegaconf import DictConfig

from src.pipeline.base import PipelineModule
from src.pipeline.frame_result import FrameResult


class PlayerTracker(PipelineModule):
    """Wraps BoxMOT BoT-SORT-ReID to assign persistent tracker IDs.

    Reads:  player_detections (bbox + conf, tracker_id=-1)
    Writes: player_detections (tracker_id updated for matched detections)

    Config keys:
        reid_weights_path (str): Path to the ReID OSNet .pt weights file.
        lost_buffer (int):       Frames to keep a lost track alive (default 200).
    """

    def __init__(self, cfg: DictConfig) -> None:
        super().__init__(cfg)
        weights = Path(cfg.reid_weights_path).expanduser().resolve()
        if not weights.exists():
            raise FileNotFoundError(
                f"ReID weights not found: {weights}\n"
                "Set DIGDEEP_REID_MODEL env var or reid_model_path in configs/app/app.yaml."
            )
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self._tracker = BotSort(
            reid_weights=weights,
            device=device,
            half=False,
            track_buffer=int(cfg.get("lost_buffer", 200)),
            frame_rate=30,
        )

    def process(self, frame_result: FrameResult) -> FrameResult:
        if frame_result.player_detections is None:
            return frame_result
        dets = _to_boxmot(frame_result.player_detections)
        tracks = self._tracker.update(dets, frame_result.frame)
        frame_result.player_detections = _from_boxmot(
            tracks, frame_result.player_detections
        )
        return frame_result


def _to_boxmot(player_detections: List[dict]) -> np.ndarray:
    if not player_detections:
        return np.empty((0, 6), dtype=np.float32)
    rows = [[*det["bbox"], det["conf"], 0.0] for det in player_detections]
    return np.array(rows, dtype=np.float32)


def _from_boxmot(tracks: np.ndarray, player_detections: List[dict]) -> List[dict]:
    for track in tracks:
        det_ind = int(track[7])
        player_detections[det_ind]["tracker_id"] = int(track[4])
    return player_detections
