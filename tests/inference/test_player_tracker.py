"""Tests for PlayerTracker — BoT-SORT-ReID wrapper."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import torch
from omegaconf import OmegaConf

from src.inference.player_tracker import PlayerTracker
from src.pipeline.frame_result import FrameResult


def _cfg(reid_weights_path, **kw):
    base = {"reid_weights_path": reid_weights_path, "lost_buffer": 200}
    base.update(kw)
    return OmegaConf.create(base)


def _make_frame(dets=None):
    return FrameResult(
        frame_idx=0,
        frame=np.zeros((720, 1280, 3), dtype=np.uint8),
        timestamp_ms=0.0,
        player_detections=dets,
    )


def test_missing_weights_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="ReID weights not found"):
        PlayerTracker(_cfg(str(tmp_path / "nonexistent.pt")))


@patch("src.inference.player_tracker.BotSort")
def test_none_detections_skips_tracker(mock_cls, tmp_path):
    weights = tmp_path / "osnet.pt"
    weights.touch()
    mock_cls.return_value = MagicMock()
    tracker = PlayerTracker(_cfg(str(weights)))
    result = tracker.process(_make_frame(dets=None))
    assert result.player_detections is None
    tracker._tracker.update.assert_not_called()


@patch("src.inference.player_tracker.BotSort")
def test_tracker_ids_stamped_on_detections(mock_cls, tmp_path):
    weights = tmp_path / "osnet.pt"
    weights.touch()
    mock_tracker = MagicMock()
    mock_cls.return_value = mock_tracker
    mock_tracker.update.return_value = np.array(
        [[10, 20, 100, 200, 7, 0.9, 0, 0]], dtype=np.float32
    )
    tracker = PlayerTracker(_cfg(str(weights)))
    dets = [{"bbox": [10.0, 20.0, 100.0, 200.0], "tracker_id": -1, "conf": 0.9}]
    result = tracker.process(_make_frame(dets=dets))
    assert result.player_detections[0]["tracker_id"] == 7


@patch("src.inference.player_tracker.BotSort")
def test_empty_tracks_leaves_tracker_id_minus_one(mock_cls, tmp_path):
    weights = tmp_path / "osnet.pt"
    weights.touch()
    mock_tracker = MagicMock()
    mock_cls.return_value = mock_tracker
    mock_tracker.update.return_value = np.empty((0, 8), dtype=np.float32)
    tracker = PlayerTracker(_cfg(str(weights)))
    dets = [{"bbox": [0.0, 0.0, 50.0, 50.0], "tracker_id": -1, "conf": 0.7}]
    result = tracker.process(_make_frame(dets=dets))
    assert result.player_detections[0]["tracker_id"] == -1


@patch("src.inference.player_tracker.BotSort")
def test_boxmot_input_shape(mock_cls, tmp_path):
    weights = tmp_path / "osnet.pt"
    weights.touch()
    mock_tracker = MagicMock()
    mock_cls.return_value = mock_tracker
    mock_tracker.update.return_value = np.empty((0, 8), dtype=np.float32)
    tracker = PlayerTracker(_cfg(str(weights)))
    dets = [{"bbox": [0.0, 0.0, 50.0, 50.0], "tracker_id": -1, "conf": 0.7}]
    tracker.process(_make_frame(dets=dets))
    arr = mock_tracker.update.call_args.args[0]
    assert arr.shape == (1, 6)
    assert arr.dtype == np.float32


@patch("src.inference.player_tracker.BotSort")
def test_two_detections_get_both_ids_stamped(mock_cls, tmp_path):
    weights = tmp_path / "osnet.pt"
    weights.touch()
    mock_tracker = MagicMock()
    mock_cls.return_value = mock_tracker
    mock_tracker.update.return_value = np.array(
        [
            [10, 20, 100, 200, 3, 0.9, 0, 0],
            [200, 300, 400, 500, 5, 0.8, 0, 1],
        ],
        dtype=np.float32,
    )
    tracker = PlayerTracker(_cfg(str(weights)))
    dets = [
        {"bbox": [10.0, 20.0, 100.0, 200.0], "tracker_id": -1, "conf": 0.9},
        {"bbox": [200.0, 300.0, 400.0, 500.0], "tracker_id": -1, "conf": 0.8},
    ]
    result = tracker.process(_make_frame(dets=dets))
    assert result.player_detections[0]["tracker_id"] == 3
    assert result.player_detections[1]["tracker_id"] == 5
