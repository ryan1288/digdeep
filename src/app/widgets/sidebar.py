"""App sidebar with navigation items."""

from __future__ import annotations

from PySide6.QtCore import QByteArray, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QSizePolicy,
                               QVBoxLayout, QWidget)

PANEL_LO = "#22252a"
PANEL_HI = "#32363d"
BORDER = "#3f434b"
TEXT = "#f1f2f4"
TEXT_DIM = "#a8acb3"
TEXT_MUTE = "#74797f"
CORAL = "#ec8a5e"
CORAL_DIM = "#c66b44"
GREEN = "#5cd0a5"

# SVG path data for icons
ICONS = {
    "film": "M3 5h18v14H3zM3 9h18M3 15h18M7 5v14M17 5v14",
    "upload": "M12 16V4M6 10l6-6 6 6M4 18h16",
    "scissors": "M6 6l12 12M6 18l4.5-4.5M18 6l-4.5 4.5M8 8a2 2 0 1 1-4 0 2 2 0 0 1 4 0zM8 18a2 2 0 1 1-4 0 2 2 0 0 1 4 0z",
    "volleyball": "M12 3a9 9 0 1 1 0 18 9 9 0 0 1 0-18zM12 3c3 4 3 14 0 18M12 3c-3 4-3 14 0 18M3 12c4-3 14-3 18 0",
    "download": "M12 4v12M6 12l6 6 6-6M4 20h16",
    "settings": "M12 9a3 3 0 1 1 0 6 3 3 0 0 1 0-6zM19 12a7 7 0 0 0-.1-1.2l2-1.6-2-3.5-2.4.9a7 7 0 0 0-2-1.2L14 3h-4l-.4 2.4a7 7 0 0 0-2 1.2l-2.4-.9-2 3.5 2 1.6A7 7 0 0 0 5 12c0 .4 0 .8.1 1.2l-2 1.6 2 3.5 2.4-.9c.6.5 1.3.9 2 1.2L10 21h4l.4-2.4c.7-.3 1.4-.7 2-1.2l2.4.9 2-3.5-2-1.6c.1-.4.1-.8.1-1.2z",
}


def _make_icon(path_data: str, size: int = 15, color: str = TEXT_DIM) -> QIcon:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.6" '
        f'stroke-linecap="round" stroke-linejoin="round">'
        f'<path d="{path_data}"/></svg>'
    )
    renderer = QSvgRenderer(QByteArray(svg.encode()))
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    renderer.render(p)
    p.end()
    return QIcon(pix)


class SidebarItem(QPushButton):
    """Single sidebar navigation button."""

    def __init__(
        self,
        label: str,
        icon_key: str,
        badge: str = "",
        subtle: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._label = label
        self._icon_key = icon_key
        self._badge = badge
        self._active = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        self._icon_lbl = QLabel()
        self._icon_lbl.setFixedSize(15, 15)
        self._icon_lbl.setStyleSheet("background: transparent;")
        layout.addWidget(self._icon_lbl)

        self._text_lbl = QLabel(label)
        self._text_lbl.setStyleSheet(
            f"background: transparent; color: {'#74797f' if subtle else TEXT_DIM};"
        )
        self._text_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        layout.addWidget(self._text_lbl, stretch=1)

        if badge:
            badge_lbl = QLabel(badge.upper())
            badge_lbl.setStyleSheet(f"""
                QLabel {{
                    font-size: 9px; font-weight: 600; padding: 2px 6px;
                    border-radius: 4px; background: {PANEL_HI};
                    color: {TEXT_MUTE}; letter-spacing: 0.5px;
                    background: transparent;
                }}
            """)
            layout.addWidget(badge_lbl)

        self.setFlat(True)
        self.setFixedHeight(36)
        self._set_style(False)
        self.setCursor(Qt.PointingHandCursor)

    def set_active(self, active: bool) -> None:
        self._active = active
        self._set_style(active)

    def _set_style(self, active: bool) -> None:
        bg = PANEL_HI if active else "transparent"
        color = TEXT if active else TEXT_DIM
        self.setStyleSheet(f"""
            QPushButton {{
                background: {bg};
                border: none;
                border-radius: 7px;
                text-align: left;
                color: {color};
                font-size: 13px;
                font-weight: {'500' if active else '400'};
            }}
            QPushButton:hover {{
                background: {'#32363d' if active else 'rgba(255,255,255,8)'};
            }}
        """)
        icon_color = CORAL if active else TEXT_DIM
        icon_path = ICONS.get(self._icon_key, "")
        if icon_path:
            icon = _make_icon(icon_path, 15, icon_color)
            pix = icon.pixmap(15, 15)
            self._icon_lbl.setPixmap(pix)
        self._text_lbl.setStyleSheet(f"background: transparent; color: {color};")


class Sidebar(QWidget):
    """220px fixed-width sidebar."""

    navigate = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedWidth(220)
        self.setStyleSheet(f"""
            QWidget {{
                background: {PANEL_LO};
                border-right: 1px solid {BORDER};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo block
        logo_widget = QWidget()
        logo_widget.setStyleSheet("background: transparent; border: none;")
        logo_layout = QHBoxLayout(logo_widget)
        logo_layout.setContentsMargins(18, 18, 18, 14)
        logo_layout.setSpacing(10)

        logo_mark = _LogoMark()
        logo_layout.addWidget(logo_mark)

        logo_text = QLabel("DigDeep")
        logo_text.setStyleSheet(f"""
            QLabel {{
                font-size: 14px; font-weight: 600; color: {TEXT};
                letter-spacing: 0.2px; background: transparent;
            }}
        """)
        logo_layout.addWidget(logo_text)
        logo_layout.addStretch()
        layout.addWidget(logo_widget)

        # Top nav section
        top_nav = QWidget()
        top_nav.setStyleSheet("background: transparent; border: none;")
        top_layout = QVBoxLayout(top_nav)
        top_layout.setContentsMargins(12, 0, 12, 8)
        top_layout.setSpacing(2)

        self._library_btn = SidebarItem("Library", "film")
        self._library_btn.clicked.connect(lambda: self.navigate.emit("library"))
        top_layout.addWidget(self._library_btn)

        self._new_match_btn = SidebarItem("New Match", "upload")
        self._new_match_btn.clicked.connect(lambda: self.navigate.emit("upload"))
        top_layout.addWidget(self._new_match_btn)

        layout.addWidget(top_nav)

        # Project section (hidden until project opened)
        self._project_section = QWidget()
        self._project_section.setStyleSheet("background: transparent; border: none;")
        proj_layout = QVBoxLayout(self._project_section)
        proj_layout.setContentsMargins(0, 0, 0, 0)
        proj_layout.setSpacing(0)

        section_lbl = QLabel("CURRENT MATCH")
        section_lbl.setStyleSheet(f"""
            QLabel {{
                font-size: 10px; font-weight: 600; letter-spacing: 1px;
                color: {TEXT_MUTE}; padding: 14px 22px 6px 22px;
                background: transparent;
            }}
        """)
        proj_layout.addWidget(section_lbl)

        inner = QWidget()
        inner.setStyleSheet("background: transparent; border: none;")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(12, 0, 12, 8)
        inner_layout.setSpacing(2)

        self._editor_btn = SidebarItem("Rally Editor", "scissors")
        self._editor_btn.clicked.connect(lambda: self.navigate.emit("editor"))
        inner_layout.addWidget(self._editor_btn)

        self._stats_btn = SidebarItem("Stats", "volleyball", badge="Soon")
        self._stats_btn.clicked.connect(lambda: self.navigate.emit("stats"))
        inner_layout.addWidget(self._stats_btn)

        self._export_btn = SidebarItem("Export", "download")
        self._export_btn.clicked.connect(lambda: self.navigate.emit("export"))
        inner_layout.addWidget(self._export_btn)

        proj_layout.addWidget(inner)
        layout.addWidget(self._project_section)
        self._project_section.hide()

        # Spacer
        layout.addStretch()

        # Bottom section
        bottom = QWidget()
        bottom.setStyleSheet(
            f"background: transparent; border-top: 1px solid {BORDER};"
        )
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(12, 12, 12, 0)
        bottom_layout.setSpacing(2)

        self._settings_btn = SidebarItem("Settings", "settings", subtle=True)
        self._settings_btn.clicked.connect(lambda: self.navigate.emit("settings"))
        bottom_layout.addWidget(self._settings_btn)

        footer = QLabel("v0.1.0 · models v0.1\n● CUDA ready")
        footer.setStyleSheet(f"""
            QLabel {{
                font-family: "JetBrains Mono"; font-size: 10px;
                color: {TEXT_MUTE}; padding: 8px 10px;
                background: transparent; line-height: 1.5;
            }}
        """)
        bottom_layout.addWidget(footer)
        layout.addWidget(bottom)

        self._all_items = [
            ("library", self._library_btn),
            ("upload", self._new_match_btn),
            ("editor", self._editor_btn),
            ("stats", self._stats_btn),
            ("export", self._export_btn),
            ("settings", self._settings_btn),
        ]
        self._current = "library"
        self._set_active("library")

    def set_view(self, view: str) -> None:
        self._current = view
        self._set_active(view)

    def set_project_active(self, active: bool) -> None:
        if active:
            self._project_section.show()
        else:
            self._project_section.hide()

    def _set_active(self, view: str) -> None:
        for name, btn in self._all_items:
            btn.set_active(name == view)


class _LogoMark(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(26, 26)
        self.setStyleSheet("background: transparent; border: none;")

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, 26, 26, 7, 7)
        from PySide6.QtGui import QLinearGradient

        grad = QLinearGradient(0, 0, 26, 26)
        grad.setColorAt(0, QColor(CORAL))
        grad.setColorAt(1, QColor(CORAL_DIM))
        from PySide6.QtGui import QBrush

        p.fillPath(path, QBrush(grad))
        p.setPen(QColor("white"))
        from PySide6.QtGui import QFont

        f = QFont("Inter", 13)
        f.setWeight(700)
        p.setFont(f)
        p.drawText(self.rect(), Qt.AlignCenter, "D")
        p.end()
