"""RadialProgress — custom painted circular progress indicator."""

from __future__ import annotations

import math

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

PANEL = "#272a30"
CORAL = "#ec8a5e"
TEXT = "#f1f2f4"
TEXT_MUTE = "#74797f"


class RadialProgress(QWidget):
    """240×240 radial progress arc with percent label."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(240, 240)
        self._value: float = 0.0

    def set_value(self, value: float) -> None:
        self._value = max(0.0, min(100.0, value))
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        r = 108
        cx, cy = 120, 120
        rect_margin = cx - r
        from PySide6.QtCore import QRectF

        rect = QRectF(rect_margin, rect_margin, r * 2, r * 2)

        # Background arc
        pen = QPen(QColor(PANEL), 14)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.drawArc(rect, 0, 360 * 16)

        # Progress arc (coral, starts at 12 o'clock = 90°)
        if self._value > 0:
            coral_pen = QPen(QColor(CORAL), 14)
            coral_pen.setCapStyle(Qt.RoundCap)
            p.setPen(coral_pen)
            span = -int(360 * 16 * self._value / 100)
            p.drawArc(rect, 90 * 16, span)

        # Percent label
        pct_font = QFont("JetBrains Mono", 38)
        pct_font.setWeight(500)
        p.setFont(pct_font)
        p.setPen(QColor(TEXT))
        p.drawText(
            QRectF(0, 80, 240, 60),
            Qt.AlignHCenter | Qt.AlignVCenter,
            str(int(self._value)),
        )

        # "%" suffix (smaller)
        suffix_font = QFont("JetBrains Mono", 18)
        p.setFont(suffix_font)
        p.setPen(QColor(TEXT_MUTE))
        # Position suffix to right of number
        fm = p.fontMetrics()
        num_text = str(int(self._value))
        num_w = QFont("JetBrains Mono", 38)
        from PySide6.QtGui import QFontMetrics

        num_fm = QFontMetrics(num_w)
        num_width = num_fm.horizontalAdvance(num_text)
        p.drawText(cx + num_width // 2 + 2, cy + 16, "%")

        # Remaining time label
        remaining = max(1, math.ceil(((100 - self._value) / 100) * 8))
        sub_font = QFont("Inter", 11)
        p.setFont(sub_font)
        p.setPen(QColor(TEXT_MUTE))
        p.drawText(
            QRectF(0, 140, 240, 20),
            Qt.AlignHCenter | Qt.AlignVCenter,
            f"{remaining} MIN REMAINING",
        )

        p.end()
