"""Unit tests for visualize_tracking drawing helpers."""

import numpy as np
import pytest


def _blank(h=100, w=200):
    return np.zeros((h, w, 3), dtype=np.uint8)


# ── _draw_players ──────────────────────────────────────────────────────────────

def test_draw_players_returns_same_shape():
    from scripts.visualize_tracking import _draw_players
    frame = _blank()
    result = _draw_players(frame, [{"bbox": [10, 10, 50, 80], "tracker_id": 1, "conf": 0.9}])
    assert result.shape == frame.shape


def test_draw_players_modifies_pixels():
    from scripts.visualize_tracking import _draw_players
    frame = _blank()
    result = _draw_players(frame, [{"bbox": [10, 10, 50, 80], "tracker_id": 2, "conf": 0.9}])
    assert result.sum() > 0


def test_draw_players_empty_detections_unchanged():
    from scripts.visualize_tracking import _draw_players
    frame = _blank()
    result = _draw_players(frame, [])
    assert result.sum() == 0


def test_draw_players_untracked_id():
    """tracker_id=-1 (not yet assigned) should draw grey, not crash."""
    from scripts.visualize_tracking import _draw_players
    frame = _blank()
    result = _draw_players(frame, [{"bbox": [5, 5, 40, 60], "tracker_id": -1, "conf": 0.5}])
    assert result.shape == frame.shape


def test_draw_players_does_not_crash_on_multiple():
    from scripts.visualize_tracking import _draw_players
    frame = _blank()
    dets = [
        {"bbox": [10, 10, 50, 80], "tracker_id": 1, "conf": 0.9},
        {"bbox": [60, 10, 100, 80], "tracker_id": 2, "conf": 0.8},
    ]
    result = _draw_players(frame, dets)
    assert result.shape == frame.shape
    assert result.sum() > 0


# ── _draw_ball ─────────────────────────────────────────────────────────────────

def test_draw_ball_returns_same_shape():
    from scripts.visualize_tracking import _draw_ball
    frame = _blank()
    result = _draw_ball(frame, [{"x": 100.0, "y": 50.0, "conf": 0.8}])
    assert result.shape == frame.shape


def test_draw_ball_modifies_pixels():
    from scripts.visualize_tracking import _draw_ball
    frame = _blank()
    result = _draw_ball(frame, [{"x": 100.0, "y": 50.0, "conf": 0.8}])
    assert result.sum() > 0


def test_draw_ball_empty_detections_unchanged():
    from scripts.visualize_tracking import _draw_ball
    frame = _blank()
    result = _draw_ball(frame, [])
    assert result.sum() == 0


def test_draw_ball_clips_to_frame_bounds():
    """Ball centroid at frame edge must not raise cv2 error."""
    from scripts.visualize_tracking import _draw_ball
    frame = _blank()
    result = _draw_ball(frame, [{"x": 0.0, "y": 0.0, "conf": 0.9}])
    assert result.shape == frame.shape
