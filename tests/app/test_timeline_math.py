"""Tests for timeline pure math functions — no Qt event loop required."""

import pytest

from src.app.widgets.timeline import choose_interval, fmt_time, t_to_x, x_to_t


def test_x_to_t_basic():
    # x=0 → t=0, x=total_w → t=duration
    assert x_to_t(0, 0, 1000, 100) == pytest.approx(0.0)
    assert x_to_t(1000, 0, 1000, 100) == pytest.approx(100.0)
    assert x_to_t(500, 0, 1000, 100) == pytest.approx(50.0)


def test_t_to_x_basic():
    assert t_to_x(0, 0, 1000, 100) == pytest.approx(0.0)
    assert t_to_x(100, 0, 1000, 100) == pytest.approx(1000.0)
    assert t_to_x(50, 0, 1000, 100) == pytest.approx(500.0)


def test_round_trip():
    # x_to_t(t_to_x(t)) == t
    total_w = 1200.0
    duration = 3600.0
    scroll_x = 0.0
    for t in [0.0, 120.0, 1800.0, 3600.0]:
        x = t_to_x(t, scroll_x, total_w, duration)
        recovered = x_to_t(x, scroll_x, total_w, duration)
        assert recovered == pytest.approx(t, abs=0.01)


def test_scroll_offset():
    # scroll_x shifts the mapping: with scroll_x=500, x=0 maps to t=50
    total_w = 1000.0
    duration = 100.0
    scroll_x = 500.0
    assert x_to_t(0, scroll_x, total_w, duration) == pytest.approx(50.0)
    assert x_to_t(500, scroll_x, total_w, duration) == pytest.approx(100.0)
    # t_to_x is inverse
    assert t_to_x(50, scroll_x, total_w, duration) == pytest.approx(0.0)


def test_zoom_scaling():
    # zoom=2 → total_w = 2 * widget_w; midpoint of widget shows t=duration/4
    widget_w = 1000.0
    zoom = 2.0
    total_w = widget_w * zoom  # 2000
    duration = 100.0
    scroll_x = 0.0
    # Pixel 1000 (right edge of widget at zoom=2) maps to t=50
    assert x_to_t(widget_w, scroll_x, total_w, duration) == pytest.approx(50.0)


def test_zero_guards():
    assert x_to_t(500, 0, 0, 100) == 0.0
    assert x_to_t(500, 0, 1000, 0) == 0.0
    assert t_to_x(50, 0, 1000, 0) == 0.0


def test_choose_interval_zoom1():
    # At zoom=1 with a 64-minute video and 1000px width, should pick a coarse interval
    duration = 64 * 60  # 3840 s
    width = 1000.0
    interval = choose_interval(1.0, duration, width)
    assert interval in [10, 30, 60, 120, 300, 600]
    # Should NOT produce more than 14 ticks
    assert duration / interval <= 14 * 1.5  # generous: allow slight overshoot


def test_choose_interval_zoom6():
    # At zoom=6 with same video and width, more px per sec → smaller interval possible
    duration = 64 * 60
    width = 1000.0
    interval_z1 = choose_interval(1.0, duration, width)
    interval_z6 = choose_interval(6.0, duration, width)
    # More zoom → finer ticks or same
    assert interval_z6 <= interval_z1
