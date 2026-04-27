"""Reusable button and label primitives."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QLabel, QPushButton, QSizePolicy

# ── Colour tokens ──────────────────────────────────────────────────────
BG = "#1d1f24"
PANEL = "#272a30"
PANEL_HI = "#32363d"
PANEL_LO = "#22252a"
BORDER = "#3f434b"
BORDER_HI = "#52575f"
TEXT = "#f1f2f4"
TEXT_DIM = "#a8acb3"
TEXT_MUTE = "#74797f"
CORAL = "#ec8a5e"
CORAL_DIM = "#c66b44"
CORAL_SOFT = "#7a4a32"
GREEN = "#5cd0a5"


def _svg_icon(path_data: str, size: int = 15, color: str = TEXT_DIM) -> QIcon:
    """Create a QIcon from an SVG path string."""
    from PySide6.QtCore import QByteArray
    from PySide6.QtSvg import QSvgRenderer

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24"
              fill="none" stroke="{color}" stroke-width="1.6"
              stroke-linecap="round" stroke-linejoin="round">
              <path d="{path_data}"/></svg>"""
    renderer = QSvgRenderer(QByteArray(svg.encode()))
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    renderer.render(p)
    p.end()
    return QIcon(pix)


class PrimaryButton(QPushButton):
    """Coral-filled action button."""

    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            QPushButton {{
                background: {CORAL};
                color: white;
                border: none;
                border-radius: 7px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: #f09870;
            }}
            QPushButton:pressed {{
                background: {CORAL_DIM};
            }}
            QPushButton:disabled {{
                background: {PANEL_HI};
                color: {TEXT_MUTE};
            }}
        """)


class GhostButton(QPushButton):
    """Transparent button with 1px border."""

    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_DIM};
                border: 1px solid {BORDER};
                border-radius: 7px;
                padding: 7px 14px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: rgba(255,255,255,20);
                color: {TEXT};
                border-color: {BORDER_HI};
            }}
            QPushButton:pressed {{
                background: {PANEL_HI};
            }}
            QPushButton:disabled {{
                color: {TEXT_MUTE};
                border-color: {BORDER};
                opacity: 0.5;
            }}
        """)


class CoralGhostButton(QPushButton):
    """Ghost button with coral text and border."""

    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {CORAL};
                border: 1px solid {CORAL};
                border-radius: 7px;
                padding: 7px 14px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {CORAL_SOFT};
            }}
            QPushButton:pressed {{
                background: {CORAL_SOFT};
            }}
        """)


class ToolBtn(QPushButton):
    """32×32 icon button used in toolbars."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(32, 32)
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid transparent;
                border-radius: 6px;
                color: {TEXT_DIM};
            }}
            QPushButton:hover:enabled {{
                background: rgba(255,255,255,20);
            }}
            QPushButton:pressed:enabled {{
                background: {PANEL_HI};
            }}
            QPushButton:disabled {{
                color: {TEXT_MUTE};
                opacity: 0.5;
            }}
        """)


class IconButton(QPushButton):
    """28×28 icon button with border."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(28, 28)
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {BORDER};
                border-radius: 7px;
                color: {TEXT_DIM};
            }}
            QPushButton:hover {{
                background: rgba(255,255,255,20);
                color: {TEXT};
            }}
            QPushButton:pressed {{
                background: {PANEL_HI};
            }}
        """)


class KbdLabel(QLabel):
    """Keyboard shortcut label styled like a keycap."""

    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            QLabel {{
                font-family: "JetBrains Mono";
                font-size: 10px;
                padding: 1px 5px;
                border-radius: 3px;
                background: {PANEL_HI};
                border: 1px solid {BORDER};
                color: {TEXT_DIM};
            }}
        """)
