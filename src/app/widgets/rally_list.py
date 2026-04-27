"""RallyList — right rail showing rally rows with filter tabs."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                               QScrollArea, QSizePolicy, QVBoxLayout, QWidget)

from src.app.widgets.buttons import KbdLabel

PANEL = "#272a30"
PANEL_HI = "#32363d"
PANEL_LO = "#22252a"
BORDER = "#3f434b"
BORDER_HI = "#52575f"
TEXT = "#f1f2f4"
TEXT_DIM = "#a8acb3"
TEXT_MUTE = "#74797f"
CORAL = "#ec8a5e"
GREEN = "#5cd0a5"


def _fmt(s: float) -> str:
    if s < 0:
        s = 0
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = int(s % 60)
    if h > 0:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"


class RallyList(QWidget):
    rally_selected = Signal(str)  # rally id

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedWidth(320)
        self.setStyleSheet(f"""
            QWidget {{
                background: {PANEL_LO};
                border-left: 1px solid {BORDER};
            }}
        """)

        self._session = None
        self._filter = "all"
        self._row_widgets: dict[str, _RallyRow] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setStyleSheet(
            f"background: transparent; border-bottom: 1px solid {BORDER};"
        )
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(16, 14, 16, 10)
        header_layout.setSpacing(12)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        flag_lbl = QLabel("⚑")
        flag_lbl.setStyleSheet(
            f"color: {CORAL}; font-size: 14px; background: transparent;"
        )
        title_row.addWidget(flag_lbl)
        self._title_lbl = QLabel("Rallies")
        self._title_lbl.setStyleSheet(
            f"font-size: 13px; font-weight: 600; color: {TEXT}; background: transparent;"
        )
        title_row.addWidget(self._title_lbl)
        self._count_badge = QLabel("0")
        self._count_badge.setStyleSheet(f"""
            font-family: 'JetBrains Mono'; font-size: 10px; color: {TEXT_DIM};
            background: {PANEL}; padding: 2px 7px; border-radius: 4px;
        """)
        title_row.addWidget(self._count_badge)
        title_row.addStretch()
        header_layout.addLayout(title_row)

        # Filter tabs
        filter_bar = QWidget()
        filter_bar.setStyleSheet(f"""
            background: {PANEL};
            border: 1px solid {BORDER};
            border-radius: 7px;
        """)
        filter_layout = QHBoxLayout(filter_bar)
        filter_layout.setContentsMargins(3, 3, 3, 3)
        filter_layout.setSpacing(0)

        self._filter_btns: dict[str, QPushButton] = {}
        for key, label in [("all", "All"), ("kept", "Kept"), ("skipped", "Skipped")]:
            btn = QPushButton(label)
            btn.setFlat(True)
            self._filter_btns[key] = btn
            btn.clicked.connect(lambda checked, k=key: self._set_filter(k))
            filter_layout.addWidget(btn)
        self._apply_filter_styles()
        header_layout.addWidget(filter_bar)

        layout.addWidget(header)

        # Scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setStyleSheet(f"background: {PANEL_LO};")

        self._list_widget = QWidget()
        self._list_widget.setStyleSheet(f"background: {PANEL_LO};")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 4, 0, 4)
        self._list_layout.setSpacing(0)
        self._list_layout.addStretch()
        self._scroll.setWidget(self._list_widget)
        layout.addWidget(self._scroll, stretch=1)

        # Footer hints
        footer = QWidget()
        footer.setStyleSheet(f"""
            background: {PANEL};
            border-top: 1px solid {BORDER};
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(14, 10, 14, 10)
        footer_layout.setSpacing(0)
        hints_widget = QWidget()
        hints_widget.setStyleSheet("background: transparent;")
        hints_layout = QVBoxLayout(hints_widget)
        hints_layout.setContentsMargins(0, 0, 0, 0)
        hints_layout.setSpacing(0)

        from PySide6.QtWidgets import QGridLayout

        grid = QWidget()
        grid.setStyleSheet("background: transparent;")
        grid_layout = QGridLayout(grid)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(4)

        hints = [
            ("Space", "play"),
            ("I", "set in"),
            ("O", "set out"),
            ("⌫", "delete"),
            ("⌘Z", "undo"),
        ]
        for i, (key, label) in enumerate(hints):
            kbd = KbdLabel(key)
            lbl = QLabel(label)
            lbl.setStyleSheet(
                f"font-size: 11px; color: {TEXT_MUTE}; background: transparent;"
            )
            grid_layout.addWidget(kbd, i // 3, (i % 3) * 2)
            grid_layout.addWidget(lbl, i // 3, (i % 3) * 2 + 1)

        hints_layout.addWidget(grid)
        footer_layout.addWidget(hints_widget)
        layout.addWidget(footer)

    def set_session(self, session) -> None:
        self._session = session
        session.rallies_changed.connect(self.refresh)
        session.rally_selection_changed.connect(self._on_selection_changed)
        session.playhead_changed.connect(self._on_playhead_changed)

    def refresh(self) -> None:
        if self._session is None:
            return
        rallies = self._session.rallies
        self._count_badge.setText(str(len(rallies)))

        # Update filter sub-counts
        kept = sum(1 for r in rallies if not r.fp)
        skipped = sum(1 for r in rallies if r.fp)
        btns = self._filter_btns
        btns["all"].setText(f"All  {len(rallies)}")
        btns["kept"].setText(f"Kept  {kept}")
        btns["skipped"].setText(f"Skipped  {skipped}")

        # Filter
        if self._filter == "kept":
            visible = [r for r in rallies if not r.fp]
        elif self._filter == "skipped":
            visible = [r for r in rallies if r.fp]
        else:
            visible = rallies

        # Rebuild rows
        old_rows = dict(self._row_widgets)
        self._row_widgets.clear()

        # Remove stretch
        stretch_item = self._list_layout.takeAt(self._list_layout.count() - 1)

        # Clear and rebuild
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        sel_id = self._session.selected_id
        ph = self._session.playhead

        for i, rally in enumerate(visible):
            idx = rallies.index(rally) + 1
            is_playing = rally.start <= ph <= rally.end
            row = _RallyRow(
                rally, idx, selected=(rally.id == sel_id), playing=is_playing
            )
            row.clicked.connect(lambda rid=rally.id: self._on_row_clicked(rid))
            row.skip_toggled.connect(
                lambda rid=rally.id: self._session.toggle_skip(rid)
            )
            self._row_widgets[rally.id] = row
            self._list_layout.addWidget(row)

        self._list_layout.addStretch()

    def _on_selection_changed(self, rally_id: str) -> None:
        self.refresh()
        QTimer.singleShot(0, lambda: self._scroll_to(rally_id))

    def _on_playhead_changed(self, t: float) -> None:
        self.refresh()

    def _scroll_to(self, rally_id: str) -> None:
        row = self._row_widgets.get(rally_id)
        if row:
            self._scroll.ensureWidgetVisible(row, 0, 40)

    def _on_row_clicked(self, rally_id: str) -> None:
        if self._session:
            self._session._raw_set_selected(rally_id)
            rally = self._session.rally_by_id(rally_id)
            if rally:
                self._session._raw_set_playhead(rally.start + 0.5)
        self.rally_selected.emit(rally_id)

    def _set_filter(self, f: str) -> None:
        self._filter = f
        self._apply_filter_styles()
        self.refresh()

    def _apply_filter_styles(self) -> None:
        for key, btn in self._filter_btns.items():
            active = key == self._filter
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {'#32363d' if active else 'transparent'};
                    color: {'#f1f2f4' if active else '#a8acb3'};
                    border: none; border-radius: 5px;
                    padding: 5px 8px; font-size: 11px; font-weight: 500;
                    font-family: 'Inter';
                }}
            """)


class _RallyRow(QWidget):
    clicked = Signal()
    skip_toggled = Signal()

    def __init__(
        self, rally, idx: int, selected: bool, playing: bool, parent=None
    ) -> None:
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)

        left_bar_color = TEXT_MUTE if rally.fp else (GREEN if playing else CORAL)
        bg = PANEL_HI if selected else "transparent"
        border_color = BORDER_HI if selected else "transparent"

        self.setStyleSheet(f"""
            QWidget#RallyRow {{
                background: {bg};
                border: 1px solid {border_color};
                border-left: 3px solid {left_bar_color};
                border-radius: 7px;
                margin: 2px 8px;
            }}
        """)
        self.setObjectName("RallyRow")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        idx_lbl = QLabel(f"#{idx:02d}")
        idx_lbl.setFixedWidth(26)
        idx_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        idx_lbl.setStyleSheet(
            f"font-family: 'JetBrains Mono'; font-size: 11px; color: {TEXT_DIM}; background: transparent; letter-spacing: 0.5px;"
        )
        layout.addWidget(idx_lbl)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_lbl = QLabel(f"Rally {idx}")
        title_lbl.setStyleSheet(f"""
            font-size: 12px; font-weight: 500; color: {TEXT if not rally.fp else TEXT_MUTE};
            text-decoration: {'line-through' if rally.fp else 'none'};
            background: transparent;
        """)
        title_row.addWidget(title_lbl)

        if playing:
            now_badge = QLabel("now")
            now_badge.setStyleSheet(f"""
                font-size: 9px; font-weight: 700; padding: 1px 6px;
                border-radius: 3px; background: {GREEN}; color: black;
                letter-spacing: 0.5px; text-transform: uppercase;
            """)
            title_row.addWidget(now_badge)
        title_row.addStretch()
        text_col.addLayout(title_row)

        meta_lbl = QLabel(
            f"{_fmt(rally.start)} → {_fmt(rally.end)}  ·  {_fmt(rally.duration)}"
        )
        meta_lbl.setStyleSheet(
            f"font-family: 'JetBrains Mono'; font-size: 10px; color: {TEXT_MUTE}; background: transparent;"
        )
        text_col.addWidget(meta_lbl)

        layout.addLayout(text_col, stretch=1)

        skip_btn = QPushButton("↻" if rally.fp else "×")
        skip_btn.setFixedSize(24, 24)
        skip_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: 1px solid {BORDER};
                border-radius: 5px; color: {TEXT_DIM}; font-size: 13px;
            }}
            QPushButton:hover {{
                background: {PANEL_HI}; color: {TEXT};
            }}
        """)
        skip_btn.setToolTip("Restore" if rally.fp else "Skip")
        skip_btn.clicked.connect(self.skip_toggled)
        layout.addWidget(skip_btn)

        self._opacity = 0.55 if rally.fp else 1.0

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

    def paintEvent(self, event) -> None:
        from PySide6.QtGui import QPainter

        p = QPainter(self)
        p.setOpacity(self._opacity)
        super().paintEvent(event)
        p.end()
