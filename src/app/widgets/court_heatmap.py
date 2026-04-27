"""CourtHeatmap — 2D court diagram with radial gradient heat blobs."""

from __future__ import annotations

import math
from typing import List, Tuple

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QPainter, QPainterPath, QPen,
                           QRadialGradient)
from PySide6.QtWidgets import QSizePolicy, QWidget

PANEL_LO = "#22252a"
BORDER = "#3f434b"
TEXT_MUTE = "#74797f"
CORAL = "#ec8a5e"


class CourtHeatmap(QWidget):
    """Top-down volleyball court diagram with heat blob overlay.

    Call set_points() with a list of (x_frac, y_frac) values in [0,1] space
    where (0,0) is top-left of the court.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._points: List[Tuple[float, float]] = []
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(200, 120)

    def set_points(self, points: List[Tuple[float, float]]) -> None:
        self._points = points
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Court area with margins
        margin = 16
        court_rect = QRectF(margin, margin, w - 2 * margin, h - 2 * margin)

        # Court background
        p.fillRect(court_rect.toRect(), QColor(PANEL_LO))
        p.setPen(QPen(QColor(BORDER), 1))
        p.drawRect(court_rect)

        cx = court_rect.x()
        cy = court_rect.y()
        cw = court_rect.width()
        ch = court_rect.height()

        # Court lines (white-ish)
        line_pen = QPen(QColor(TEXT_MUTE), 1)
        p.setPen(line_pen)

        # Net (center horizontal line)
        mid_y = cy + ch / 2
        p.drawLine(QPointF(cx, mid_y), QPointF(cx + cw, mid_y))

        # Attack lines (3m from net on each side; court is 18m, attack at 9±3)
        atk_frac = 3.0 / 9.0  # fraction of half-court
        p.drawLine(
            QPointF(cx, cy + ch / 2 - ch / 2 * atk_frac),
            QPointF(cx + cw, cy + ch / 2 - ch / 2 * atk_frac),
        )
        p.drawLine(
            QPointF(cx, cy + ch / 2 + ch / 2 * atk_frac),
            QPointF(cx + cw, cy + ch / 2 + ch / 2 * atk_frac),
        )

        # Center vertical dividers (6 zones each side)
        for i in range(1, 3):
            x = cx + cw * i / 3
            p.drawLine(QPointF(x, cy), QPointF(x, mid_y))
            p.drawLine(QPointF(x, mid_y), QPointF(x, cy + ch))

        # Heat blobs
        if self._points:
            blob_r = max(cw, ch) * 0.12
            for fx, fy in self._points:
                bx = cx + fx * cw
                by = cy + fy * ch
                grad = QRadialGradient(QPointF(bx, by), blob_r)
                grad.setColorAt(0.0, QColor(236, 138, 94, 160))
                grad.setColorAt(0.5, QColor(236, 138, 94, 60))
                grad.setColorAt(1.0, QColor(236, 138, 94, 0))
                p.setBrush(QBrush(grad))
                p.setPen(Qt.NoPen)
                p.drawEllipse(QPointF(bx, by), blob_r, blob_r)

        p.end()
