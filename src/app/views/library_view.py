"""Library view — grid of past processed matches + New Match CTA."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QPushButton, QScrollArea, QSizePolicy,
                               QVBoxLayout, QWidget)

from src.app.widgets.cards import ScreenHeader
from src.app.widgets.striped_placeholder import StripedPlaceholder

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

_PROJECTS_FILE = Path.home() / ".digdeep" / "projects.json"


class LibraryView(QWidget):
    new_match = Signal()
    open_project = Signal(dict)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"background: {BG};")
        self._projects: List[dict] = self._load_projects()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(ScreenHeader("Library", "Your processed matches"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background: {BG};")

        content = QWidget()
        content.setStyleSheet(f"background: {BG};")
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(36, 8, 36, 36)
        self._content_layout.setSpacing(24)

        self._cta = self._build_cta()
        self._content_layout.addWidget(self._cta)

        self._grid_section = QWidget()
        self._grid_section.setStyleSheet("background: transparent;")
        self._grid_outer = QVBoxLayout(self._grid_section)
        self._grid_outer.setContentsMargins(0, 0, 0, 0)
        self._grid_outer.setSpacing(14)
        self._content_layout.addWidget(self._grid_section)
        self._content_layout.addStretch()

        self._rebuild_grid()
        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

    def _build_cta(self) -> QWidget:
        w = QWidget()
        w.setCursor(Qt.PointingHandCursor)
        w.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {PANEL_LO}, stop:1 {PANEL});
                border: 1px dashed {BORDER_HI};
                border-radius: 14px;
            }}
            QWidget:hover {{ border-color: {CORAL}; }}
        """)
        w.mousePressEvent = lambda e: self.new_match.emit()

        row = QHBoxLayout(w)
        row.setContentsMargins(28, 28, 28, 28)
        row.setSpacing(24)

        # Icon tile
        icon_tile = QWidget()
        icon_tile.setFixedSize(56, 56)
        icon_tile.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {CORAL}, stop:1 {CORAL_DIM});
            border-radius: 14px;
        """)
        icon_inner = QVBoxLayout(icon_tile)
        icon_inner.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel("↑")
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(
            "color: white; font-size: 22px; font-weight: 600; background: transparent;"
        )
        icon_inner.addWidget(icon_lbl)
        row.addWidget(icon_tile)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        title = QLabel("Process a new match")
        title.setStyleSheet(
            f"font-size: 18px; font-weight: 600; color: {TEXT}; background: transparent;"
        )
        sub = QLabel(
            "Drop in a full-match video. DigDeep finds the rallies, you fine-tune."
        )
        sub.setStyleSheet(
            f"font-size: 13px; color: {TEXT_DIM}; background: transparent;"
        )
        text_col.addWidget(title)
        text_col.addWidget(sub)
        row.addLayout(text_col, stretch=1)

        btn = QPushButton("Choose video")
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {CORAL}; color: white;
                border: none; border-radius: 7px;
                padding: 8px 14px; font-size: 13px; font-weight: 600;
            }}
        """)
        btn.clicked.connect(self.new_match)
        row.addWidget(btn)
        return w

    def _rebuild_grid(self) -> None:
        # Clear existing grid
        while self._grid_outer.count():
            item = self._grid_outer.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._projects:
            return

        # Section header
        hdr_row = QWidget()
        hdr_row.setStyleSheet("background: transparent;")
        hdr_layout = QHBoxLayout(hdr_row)
        hdr_layout.setContentsMargins(0, 0, 0, 0)
        hdr_layout.setSpacing(12)
        lbl = QLabel("RECENT")
        lbl.setStyleSheet(
            f"font-size: 12px; font-weight: 600; color: {TEXT_MUTE}; letter-spacing: 1px; background: transparent;"
        )
        hdr_layout.addWidget(lbl)
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {BORDER}; border: none;")
        sep.setFixedHeight(1)
        hdr_layout.addWidget(sep, stretch=1)
        self._grid_outer.addWidget(hdr_row)

        grid_widget = QWidget()
        grid_widget.setStyleSheet("background: transparent;")
        grid = QGridLayout(grid_widget)
        grid.setSpacing(14)
        grid.setContentsMargins(0, 0, 0, 0)

        cols = 4
        for i, project in enumerate(self._projects):
            card = _ProjectCard(project)
            card.clicked.connect(lambda p=project: self.open_project.emit(p))
            grid.addWidget(card, i // cols, i % cols)

        self._grid_outer.addWidget(grid_widget)

    def add_project_from_session(
        self, session, output_path: str, source_path: str
    ) -> None:
        import datetime

        from src.app.session import MatchSession

        name = Path(source_path).stem if source_path else Path(output_path).stem
        kept = [r for r in session.rallies if not r.fp]
        dur = sum(r.duration for r in kept)

        project = {
            "id": str(Path(output_path).stem),
            "name": name,
            "date": datetime.date.today().strftime("%b %d, %Y"),
            "duration": _fmt(session.duration),
            "rallies": len(session.rallies),
            "output_path": output_path,
            "source_path": source_path,
            "analytics_path": output_path.replace(".mp4", "_analytics.json"),
        }
        self._projects.insert(0, project)
        self._save_projects()
        self._rebuild_grid()

    def _load_projects(self) -> list[dict]:
        if _PROJECTS_FILE.exists():
            try:
                return json.loads(_PROJECTS_FILE.read_text())
            except Exception:
                pass
        return []

    def _save_projects(self) -> None:
        _PROJECTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        _PROJECTS_FILE.write_text(json.dumps(self._projects, indent=2))


class _ProjectCard(QWidget):
    clicked = Signal()

    def __init__(self, project: dict, parent=None) -> None:
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumWidth(220)
        self.setStyleSheet(f"""
            QWidget#ProjectCard {{
                background: {PANEL};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
            QWidget#ProjectCard:hover {{
                border-color: {BORDER_HI};
            }}
        """)
        self.setObjectName("ProjectCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        thumb = StripedPlaceholder(130, project.get("name", "match footage"))
        layout.addWidget(thumb)

        meta = QWidget()
        meta.setStyleSheet("background: transparent;")
        meta_layout = QVBoxLayout(meta)
        meta_layout.setContentsMargins(14, 12, 14, 12)
        meta_layout.setSpacing(4)

        title = QLabel(project.get("name", "Match"))
        title.setStyleSheet(
            f"font-size: 14px; font-weight: 600; color: {TEXT}; background: transparent;"
        )
        title.setMaximumWidth(210)
        meta_layout.addWidget(title)

        dot = f"<span style='color:{TEXT_MUTE}'>·</span>"
        info = QLabel(
            f"{project.get('date','')} {dot} "
            f"{project.get('duration','')} {dot} "
            f"<span style='color:{CORAL}'>{project.get('rallies',0)} rallies</span>"
        )
        info.setStyleSheet(
            f"font-size: 11px; color: {TEXT_MUTE}; background: transparent;"
        )
        info.setTextFormat(Qt.RichText)
        meta_layout.addWidget(info)

        layout.addWidget(meta)

    def mousePressEvent(self, event) -> None:
        self.clicked.emit()


def _fmt(s: float) -> str:
    if s <= 0:
        return "0:00"
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = int(s % 60)
    if h > 0:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"
