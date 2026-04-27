"""Tests for real_runner.py — 5-stage pipeline."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from omegaconf import OmegaConf

from src.inference.real_runner import run_pipeline

_FAKE_FRAME = np.zeros((480, 640, 3), dtype=np.uint8)


def _make_cfg(**kw):
    base = {
        "ball_model_path": "/fake/ball.onnx",
        "player_model_path": "/fake/player.onnx",
        "reid_model_path": "/fake/osnet.pt",
    }
    base.update(kw)
    return OmegaConf.create(base)


def _pass_through():
    m = MagicMock()
    m.process.side_effect = lambda fr: fr
    return m


def _patched_pipeline(cap_side_effect=None):
    """Context managers for patching all 4 pipeline modules + VideoCapture."""
    if cap_side_effect is None:
        cap_side_effect = [(True, _FAKE_FRAME), (False, None)]

    patches = [
        patch("src.inference.real_runner.cv2.VideoCapture"),
        patch("src.inference.real_runner.BallDetector"),
        patch("src.inference.real_runner.PlayerDetector"),
        patch("src.inference.real_runner.PlayerTracker"),
        patch("src.inference.real_runner.RallyDetector"),
    ]
    return patches, cap_side_effect


@patch("src.inference.real_runner.RallyDetector")
@patch("src.inference.real_runner.PlayerTracker")
@patch("src.inference.real_runner.PlayerDetector")
@patch("src.inference.real_runner.BallDetector")
@patch("src.inference.real_runner.cv2.VideoCapture")
def test_stage_callbacks_emitted_in_order(
    mock_cap_cls, mock_bd, mock_pd, mock_pt, mock_rd
):
    cap = MagicMock()
    cap.get.return_value = 30.0
    cap.read.side_effect = [(True, _FAKE_FRAME), (False, None)]
    mock_cap_cls.return_value = cap
    for m in (mock_bd, mock_pd, mock_pt, mock_rd):
        m.return_value = _pass_through()

    stage_calls = []
    run_pipeline("/fake/video.mp4", lambda _: None, stage_calls.append, cfg=_make_cfg())

    lower = [s.lower() for s in stage_calls]
    combined = " ".join(lower)
    assert any("decod" in s for s in lower), f"Missing 'decod' in {stage_calls}"
    assert any("ball" in s for s in lower), f"Missing 'ball' in {stage_calls}"
    assert any(
        "player" in s or "finding" in s for s in lower
    ), f"Missing 'player' in {stage_calls}"
    assert any("link" in s for s in lower), f"Missing 'link' in {stage_calls}"
    assert any("rally" in s for s in lower), f"Missing 'rally' in {stage_calls}"

    # Ordering check
    ball_idx = next(i for i, s in enumerate(lower) if "ball" in s)
    player_idx = next(i for i, s in enumerate(lower) if "player" in s or "finding" in s)
    link_idx = next(i for i, s in enumerate(lower) if "link" in s)
    rally_idx = next(i for i, s in enumerate(lower) if "rally" in s)
    assert ball_idx < player_idx < link_idx < rally_idx


@patch("src.inference.real_runner.RallyDetector")
@patch("src.inference.real_runner.PlayerTracker")
@patch("src.inference.real_runner.PlayerDetector")
@patch("src.inference.real_runner.BallDetector")
@patch("src.inference.real_runner.cv2.VideoCapture")
def test_returns_list_of_rally_dicts(mock_cap_cls, mock_bd, mock_pd, mock_pt, mock_rd):
    cap = MagicMock()
    cap.get.return_value = 30.0
    cap.read.side_effect = [(True, _FAKE_FRAME), (False, None)]
    mock_cap_cls.return_value = cap
    for m in (mock_bd, mock_pd, mock_pt, mock_rd):
        m.return_value = _pass_through()

    result = run_pipeline(
        "/fake/video.mp4", lambda _: None, lambda _: None, cfg=_make_cfg()
    )
    assert isinstance(result, list)
    for r in result:
        assert "start_sec" in r and "end_sec" in r


@patch("src.inference.real_runner.RallyDetector")
@patch("src.inference.real_runner.PlayerTracker")
@patch("src.inference.real_runner.PlayerDetector")
@patch("src.inference.real_runner.BallDetector")
@patch("src.inference.real_runner.cv2.VideoCapture")
def test_player_model_path_from_env(
    mock_cap_cls, mock_bd, mock_pd, mock_pt, mock_rd, monkeypatch, tmp_path
):
    monkeypatch.setenv("DIGDEEP_PLAYER_MODEL", str(tmp_path / "player.onnx"))
    (tmp_path / "player.onnx").touch()
    cap = MagicMock()
    cap.get.return_value = 30.0
    cap.read.return_value = (False, None)
    mock_cap_cls.return_value = cap
    for m in (mock_bd, mock_pd, mock_pt, mock_rd):
        m.return_value = _pass_through()
    # Should not raise about player model path
    run_pipeline("/fake/video.mp4", lambda _: None, lambda _: None, cfg=_make_cfg())


@patch("src.inference.real_runner.RallyDetector")
@patch("src.inference.real_runner.PlayerTracker")
@patch("src.inference.real_runner.PlayerDetector")
@patch("src.inference.real_runner.BallDetector")
@patch("src.inference.real_runner.cv2.VideoCapture")
def test_all_four_modules_called_per_frame(
    mock_cap_cls, mock_bd, mock_pd, mock_pt, mock_rd
):
    cap = MagicMock()
    cap.get.return_value = 30.0
    cap.read.side_effect = [(True, _FAKE_FRAME), (True, _FAKE_FRAME), (False, None)]
    mock_cap_cls.return_value = cap
    modules = []
    for m in (mock_bd, mock_pd, mock_pt, mock_rd):
        inst = _pass_through()
        m.return_value = inst
        modules.append(inst)

    run_pipeline("/fake/video.mp4", lambda _: None, lambda _: None, cfg=_make_cfg())
    for inst in modules:
        assert inst.process.call_count == 2  # 2 frames
