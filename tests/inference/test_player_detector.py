"""Tests for PlayerDetector — RF-DETR ONNX wrapper."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from omegaconf import OmegaConf

from src.inference.player_detector import PlayerDetector
from src.pipeline.frame_result import FrameResult


def _make_cfg(model_path, **kw):
    base = {"model_path": model_path, "resolution": 560, "conf_threshold": 0.5}
    base.update(kw)
    return OmegaConf.create(base)


def _make_frame(h=720, w=1280):
    return FrameResult(
        frame_idx=0, frame=np.zeros((h, w, 3), dtype=np.uint8), timestamp_ms=0.0
    )


def _mock_session(num_queries=300, num_classes=2, logit_value=-10.0):
    """Return a mock ort.InferenceSession with controlled outputs."""
    sess = MagicMock()
    dets = np.zeros((1, num_queries, 4), dtype=np.float32)
    labels = np.full((1, num_queries, num_classes), logit_value, dtype=np.float32)
    sess.run.return_value = [dets, labels]
    sess.get_inputs.return_value = [MagicMock(name="input")]
    return sess


@patch("src.inference.player_detector.ort.InferenceSession")
def test_returns_frame_result(mock_ort, tmp_path):
    (tmp_path / "player.onnx").touch()
    mock_ort.return_value = _mock_session()
    det = PlayerDetector(_make_cfg(str(tmp_path / "player.onnx")))
    result = det.process(_make_frame())
    assert isinstance(result, FrameResult)


@patch("src.inference.player_detector.ort.InferenceSession")
def test_no_detections_when_all_logits_very_negative(mock_ort, tmp_path):
    (tmp_path / "player.onnx").touch()
    mock_ort.return_value = _mock_session(logit_value=-100.0)
    det = PlayerDetector(_make_cfg(str(tmp_path / "player.onnx")))
    result = det.process(_make_frame())
    assert result.player_detections == []


@patch("src.inference.player_detector.ort.InferenceSession")
def test_detections_returned_when_logit_above_threshold(mock_ort, tmp_path):
    (tmp_path / "player.onnx").touch()
    sess = _mock_session(logit_value=-100.0)
    dets = np.zeros((1, 300, 4), dtype=np.float32)
    labels = np.full((1, 300, 2), -100.0, dtype=np.float32)
    labels[0, 0, 0] = 5.0  # query 0, class 0 (player) → sigmoid ≈ 0.993
    dets[0, 0] = [0.5, 0.5, 0.1, 0.1]
    sess.run.return_value = [dets, labels]
    mock_ort.return_value = sess
    det = PlayerDetector(_make_cfg(str(tmp_path / "player.onnx")))
    result = det.process(_make_frame(h=720, w=1280))
    assert len(result.player_detections) == 1


@patch("src.inference.player_detector.ort.InferenceSession")
def test_detection_schema(mock_ort, tmp_path):
    (tmp_path / "player.onnx").touch()
    sess = _mock_session(logit_value=-100.0)
    dets = np.zeros((1, 300, 4), dtype=np.float32)
    labels = np.full((1, 300, 2), -100.0, dtype=np.float32)
    labels[0, 0, 0] = 5.0
    dets[0, 0] = [0.5, 0.5, 0.2, 0.3]
    sess.run.return_value = [dets, labels]
    mock_ort.return_value = sess
    det = PlayerDetector(_make_cfg(str(tmp_path / "player.onnx")))
    result = det.process(_make_frame())
    d = result.player_detections[0]
    assert set(d.keys()) == {"bbox", "tracker_id", "conf"}
    assert len(d["bbox"]) == 4
    assert isinstance(d["conf"], float)
    assert d["tracker_id"] == -1


@patch("src.inference.player_detector.ort.InferenceSession")
def test_bbox_scaled_to_frame_coordinates(mock_ort, tmp_path):
    (tmp_path / "player.onnx").touch()
    sess = _mock_session(logit_value=-100.0)
    dets = np.zeros((1, 300, 4), dtype=np.float32)
    labels = np.full((1, 300, 2), -100.0, dtype=np.float32)
    labels[0, 0, 0] = 5.0
    # cx=0.5, cy=0.5, w=1.0, h=1.0 → xyxy should be 0, 0, W, H
    dets[0, 0] = [0.5, 0.5, 1.0, 1.0]
    sess.run.return_value = [dets, labels]
    mock_ort.return_value = sess
    h, w = 1080, 1920
    det = PlayerDetector(_make_cfg(str(tmp_path / "player.onnx")))
    result = det.process(_make_frame(h=h, w=w))
    x1, y1, x2, y2 = result.player_detections[0]["bbox"]
    assert abs(x1) < 1.0
    assert abs(y1) < 1.0
    assert abs(x2 - w) < 1.0
    assert abs(y2 - h) < 1.0


@patch("src.inference.player_detector.ort.InferenceSession")
def test_other_fields_unchanged(mock_ort, tmp_path):
    (tmp_path / "player.onnx").touch()
    mock_ort.return_value = _mock_session()
    det = PlayerDetector(_make_cfg(str(tmp_path / "player.onnx")))
    fr = _make_frame()
    fr.ball_detections = [{"x": 1.0, "y": 2.0, "conf": 0.8}]
    fr.rally_state = "in_rally"
    result = det.process(fr)
    assert result.ball_detections == [{"x": 1.0, "y": 2.0, "conf": 0.8}]
    assert result.rally_state == "in_rally"


def test_missing_model_raises_file_not_found():
    with pytest.raises(FileNotFoundError, match="Player detector model not found"):
        PlayerDetector(_make_cfg("/nonexistent/path.onnx"))
