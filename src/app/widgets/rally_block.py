"""paint_rally_block — module-level painter function for timeline rally blocks."""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QFont, QFontMetrics,
                           QLinearGradient, QPainter, QPainterPath, QPen)

CORAL = "#ec8a5e"
CORAL_DIM = "#c66b44"
CORAL_HOVER = "#f09870"
CORAL_SEL = "#f4a080"
TEXT = "#f1f2f4"
TEXT_MUTE = "#74797f"
PANEL_LO = "#22252a"


def _fmt(s: float) -> str:
    if s < 0:
        s = 0
    m = int(s // 60)
    sec = int(s % 60)
    return f"{m}:{sec:02d}"


def paint_rally_block(
    painter: QPainter,
    rally_start: float,
    rally_end: float,
    rally_fp: bool,
    x: float,
    w: float,
    top: int,
    height: int,
    selected: bool,
    hovered: bool,
    index: int,
) -> None:
    """Paint one rally block onto the given QPainter.

    Args:
        painter: Active QPainter on the timeline widget.
        rally_start: Rally start time in seconds.
        rally_end: Rally end time in seconds.
        rally_fp: Whether the rally is marked as false-positive (skip).
        x: Left pixel position of the block.
        w: Width of the block in pixels.
        top: Top Y coordinate of the block.
        height: Height of the block in pixels.
        selected: Whether this block is selected.
        hovered: Whether the mouse is hovering over this block.
        index: 1-based rally number for label.
    """
    if w < 2:
        return

    rect = QRectF(x, top, w, height)

    # ── Gradient fill ──────────────────────────────────────────────
    if rally_fp:
        c_top = QColor(50, 54, 61, 128)
        c_bot = QColor(40, 44, 51, 128)
    elif selected:
        c_top = QColor(CORAL_SEL)
        c_bot = QColor(CORAL_DIM)
    elif hovered:
        c_top = QColor(CORAL_HOVER)
        c_bot = QColor(CORAL_DIM)
    else:
        c_top = QColor(CORAL)
        c_bot = QColor(CORAL_DIM)

    grad = QLinearGradient(0, top, 0, top + height)
    grad.setColorAt(0, c_top)
    grad.setColorAt(1, c_bot)

    path = QPainterPath()
    path.addRoundedRect(rect, 6, 6)

    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(grad))
    painter.drawPath(path)

    # ── Selected outline ───────────────────────────────────────────
    if selected:
        painter.setPen(QPen(QColor(TEXT), 2))
        painter.setBrush(Qt.NoBrush)
        outline_rect = QRectF(x - 1, top - 1, w + 2, height + 2)
        outline_path = QPainterPath()
        outline_path.addRoundedRect(outline_rect, 7, 7)
        painter.drawPath(outline_path)

    # ── Resize handle highlights ───────────────────────────────────
    if (selected or hovered) and w >= 16:
        handle_color = QColor(255, 255, 255, 60)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(handle_color))
        lh = QPainterPath()
        lh.addRoundedRect(QRectF(x, top, 8, height), 6, 0)
        painter.drawPath(lh)
        rh = QPainterPath()
        rh.addRoundedRect(QRectF(x + w - 8, top, 8, height), 0, 6)
        painter.drawPath(rh)

        # Edge accent lines
        edge_col = QColor(TEXT) if selected else QColor(255, 255, 255, 120)
        painter.setPen(QPen(edge_col, 1.5))
        painter.drawLine(QPointF(x + 1, top + 4), QPointF(x + 1, top + height - 4))
        painter.drawLine(
            QPointF(x + w - 1, top + 4), QPointF(x + w - 1, top + height - 4)
        )

    # ── Waveform texture bars ──────────────────────────────────────
    if w > 20:
        bar_area = QRectF(x + 8, top + 8, w - 16, height - 16)
        n_bars = max(6, int(w / 6))
        bar_w = max(1.5, (bar_area.width() - (n_bars - 1) * 2) / n_bars)
        painter.setPen(Qt.NoPen)
        waveform_color = QColor(255, 255, 255, 89)  # 35% opacity
        painter.setBrush(QBrush(waveform_color))
        for i in range(n_bars):
            bar_height_frac = 0.2 + abs(math.sin(i * 1.7 + rally_start)) * 0.6
            bh = bar_area.height() * bar_height_frac
            bx = bar_area.left() + i * (bar_w + 2)
            by = bar_area.bottom() - bh
            br = QRectF(bx, by, bar_w, bh)
            rpath = QPainterPath()
            rpath.addRoundedRect(br, 1, 1)
            painter.drawPath(rpath)

    # ── Label ──────────────────────────────────────────────────────
    if w > 40:
        label_font = QFont("Inter", 11)
        label_font.setWeight(600)
        painter.setFont(label_font)
        painter.setPen(QColor(255, 255, 255, 230))

        duration = rally_end - rally_start
        label = f"Rally {index}"
        if w > 110:
            label += f"  {_fmt(duration)}"
        if rally_fp and w > 130:
            label += "  [skipped]"

        label_rect = QRectF(x + 14, top, w - 28, height)
        painter.drawText(label_rect, Qt.AlignVCenter | Qt.AlignLeft, label)
