"""Reusable card, header, and layout widgets."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

PANEL = "#272a30"
PANEL_LO = "#22252a"
BORDER = "#3f434b"
BORDER_HI = "#52575f"
TEXT = "#f1f2f4"
TEXT_DIM = "#a8acb3"
TEXT_MUTE = "#74797f"
CORAL = "#ec8a5e"


class Card(QWidget):
    """Panel with border + radius 12, optional uppercase caption header."""

    def __init__(self, title: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self.setStyleSheet(f"""
            QWidget#Card {{
                background: {PANEL};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        if title:
            hdr = QLabel(title.upper())
            hdr.setStyleSheet(f"""
                QLabel {{
                    font-size: 11px;
                    font-weight: 600;
                    letter-spacing: 1px;
                    color: {TEXT_MUTE};
                    padding: 14px 18px 4px 18px;
                    background: transparent;
                }}
            """)
            outer.addWidget(hdr)

        self._inner = QWidget()
        self._inner.setStyleSheet("background: transparent;")
        inner_layout = QVBoxLayout(self._inner)
        inner_layout.setContentsMargins(8, 8, 8, 12)
        inner_layout.setSpacing(0)
        outer.addWidget(self._inner)

    def inner_layout(self) -> QVBoxLayout:
        return self._inner.layout()


class ScreenHeader(QWidget):
    """Standard screen header with title + subtitle."""

    def __init__(self, title: str, subtitle: str = "", parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(36, 26, 36, 18)
        layout.setSpacing(0)

        left = QVBoxLayout()
        left.setSpacing(4)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                font-weight: 600;
                color: {TEXT};
                letter-spacing: -0.4px;
                background: transparent;
            }}
        """)
        left.addWidget(title_lbl)

        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setStyleSheet(f"""
                QLabel {{
                    font-size: 13px;
                    color: {TEXT_DIM};
                    background: transparent;
                }}
            """)
            left.addWidget(sub_lbl)

        self._left_layout = left
        layout.addLayout(left)
        layout.addStretch()

        self._right_layout = QHBoxLayout()
        self._right_layout.setSpacing(10)
        layout.addLayout(self._right_layout)

    def add_right_widget(self, widget: QWidget) -> None:
        self._right_layout.addWidget(widget)


class HSeparator(QFrame):
    """1px horizontal separator line."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Plain)
        self.setFixedHeight(1)
        self.setStyleSheet(f"background: {BORDER}; border: none;")


class VSeparator(QFrame):
    """1px vertical separator line."""

    def __init__(self, height: int = 22, parent=None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Plain)
        self.setFixedWidth(1)
        self.setFixedHeight(height)
        self.setStyleSheet(f"background: {BORDER}; border: none;")
