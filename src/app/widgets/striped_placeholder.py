"""Striped placeholder widget — used as thumbnail / video stand-in."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

PANEL = "#272a30"
PANEL_HI = "#32363d"
BORDER = "#3f434b"
TEXT_MUTE = "#74797f"
PANEL_LO = "#22252a"


class StripedPlaceholder(QWidget):
    """Diagonal stripe pattern used as thumbnail placeholder."""

    def __init__(
        self, height: int = 130, label: str = "match footage", parent=None
    ) -> None:
        super().__init__(parent)
        self._label = label
        self._fixed_height = height
        if height > 0:
            self.setFixedHeight(height)
        self.setStyleSheet(f"border-bottom: 1px solid {BORDER};")

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)

        w = self.width()
        h = self.height()

        # Draw diagonal stripes manually
        stripe = 16
        c1 = QColor(PANEL_HI)
        c2 = QColor(PANEL)

        # Fill background first
        p.fillRect(0, 0, w, h, c2)

        # Draw stripes at 135°
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(c1))
        total = w + h
        for i in range(0, total // stripe + 2, 2):
            x0 = i * stripe - h
            pts_x = [x0, x0 + stripe, x0 + stripe + h, x0 + h]
            pts_y = [0, 0, h, h]
            from PySide6.QtCore import QPoint
            from PySide6.QtGui import QPolygon

            poly = QPolygon([QPoint(int(pts_x[j]), int(pts_y[j])) for j in range(4)])
            p.drawPolygon(poly)

        # Center label on semi-transparent background
        fm = p.fontMetrics()
        label_w = fm.horizontalAdvance(self._label) + 16
        label_h = fm.height() + 6
        lx = (w - label_w) // 2
        ly = (h - label_h) // 2

        p.setBrush(QBrush(QColor(PANEL_LO)))
        p.setPen(QPen(QColor(BORDER), 1))
        from PySide6.QtCore import QRectF

        p.drawRoundedRect(QRectF(lx, ly, label_w, label_h), 4, 4)

        p.setPen(QColor(TEXT_MUTE))
        from PySide6.QtGui import QFont

        f = QFont("JetBrains Mono", 10)
        p.setFont(f)
        p.drawText(lx, ly, label_w, label_h, Qt.AlignCenter, self._label)

        p.end()
