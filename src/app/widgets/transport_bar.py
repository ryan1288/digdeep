"""TransportBar — playback controls, timecode, add/delete, zoom."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QSizePolicy,
                               QSlider, QWidget)

from src.app.widgets.buttons import GhostButton, ToolBtn
from src.app.widgets.cards import VSeparator

PANEL = "#272a30"
PANEL_LO = "#22252a"
BORDER = "#3f434b"
BORDER_HI = "#52575f"
TEXT = "#f1f2f4"
TEXT_DIM = "#a8acb3"
TEXT_MUTE = "#74797f"
CORAL = "#ec8a5e"


def _fmt_ms(s: float) -> str:
    s = max(0.0, s)
    m = int(s // 60)
    sec = int(s % 60)
    ms = int((s - int(s)) * 1000)
    return f"{m:02d}:{sec:02d}.{ms:03d}"


def _fmt(s: float) -> str:
    if s < 0:
        s = 0
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = int(s % 60)
    if h > 0:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"


class TransportBar(QWidget):
    """Fixed-height playback transport bar."""

    play_pause_clicked = Signal()
    prev_rally_clicked = Signal()
    next_rally_clicked = Signal()
    add_rally_clicked = Signal()
    delete_rally_clicked = Signal()
    zoom_changed = Signal(float)

    def __init__(self, session, parent=None) -> None:
        super().__init__(parent)
        self._session = session
        self.setFixedHeight(56)
        self.setStyleSheet(f"""
            QWidget {{
                background: {PANEL};
                border-top: 1px solid {BORDER};
                border-bottom: 1px solid {BORDER};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(10)

        # Prev / Play / Next cluster
        self._prev_btn = ToolBtn()
        self._prev_btn.setText("◀◀")
        self._prev_btn.setToolTip("Previous rally")
        self._prev_btn.clicked.connect(self.prev_rally_clicked)
        layout.addWidget(self._prev_btn)

        self._play_btn = QPushButton("▶")
        self._play_btn.setFixedSize(36, 36)
        self._play_btn.setStyleSheet(f"""
            QPushButton {{
                background: {CORAL}; color: white;
                border: none; border-radius: 7px; font-size: 14px;
            }}
            QPushButton:hover {{ background: #f09870; }}
            QPushButton:pressed {{ background: #c66b44; }}
        """)
        self._play_btn.clicked.connect(self.play_pause_clicked)
        layout.addWidget(self._play_btn)

        self._next_btn = ToolBtn()
        self._next_btn.setText("▶▶")
        self._next_btn.setToolTip("Next rally")
        self._next_btn.clicked.connect(self.next_rally_clicked)
        layout.addWidget(self._next_btn)

        # Timecode display
        self._time_lbl = QLabel("00:00.000 / 0:00")
        self._time_lbl.setMinimumWidth(168)
        self._time_lbl.setAlignment(Qt.AlignCenter)
        self._time_lbl.setStyleSheet(f"""
            background: {PANEL_LO}; border: 1px solid {BORDER};
            border-radius: 6px; padding: 6px 12px;
            font-family: 'JetBrains Mono'; font-size: 12px;
            color: {TEXT}; letter-spacing: 0.5px;
        """)
        layout.addWidget(self._time_lbl)

        layout.addStretch()

        # Add rally / Delete
        add_btn = QPushButton("+ Add rally")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: 1px solid {BORDER_HI};
                border-radius: 7px; padding: 7px 12px;
                color: {TEXT}; font-size: 12px; font-weight: 500;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,15); }}
        """)
        add_btn.clicked.connect(self.add_rally_clicked)
        layout.addWidget(add_btn)

        self._del_btn = QPushButton("🗑 Delete")
        self._del_btn.setEnabled(False)
        self._del_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: 1px solid {BORDER};
                border-radius: 7px; padding: 7px 12px;
                color: {TEXT_MUTE}; font-size: 12px; font-weight: 500;
            }}
            QPushButton:enabled {{
                border-color: {BORDER_HI}; color: {TEXT};
            }}
            QPushButton:enabled:hover {{ background: rgba(255,255,255,15); }}
        """)
        self._del_btn.clicked.connect(self.delete_rally_clicked)
        layout.addWidget(self._del_btn)

        layout.addWidget(VSeparator())

        # Zoom slider
        zoom_lbl = QLabel("Zoom")
        zoom_lbl.setStyleSheet(
            f"font-size: 11px; color: {TEXT_MUTE}; background: transparent;"
        )
        layout.addWidget(zoom_lbl)

        self._zoom_slider = QSlider(Qt.Horizontal)
        self._zoom_slider.setRange(10, 60)
        self._zoom_slider.setValue(10)
        self._zoom_slider.setFixedWidth(80)
        self._zoom_slider.valueChanged.connect(
            lambda v: self.zoom_changed.emit(v / 10.0)
        )
        layout.addWidget(self._zoom_slider)

        if session:
            session.playhead_changed.connect(self._update_time)
            session.play_state_changed.connect(self._update_play_icon)
            session.rally_selection_changed.connect(self._update_delete_btn)

    def _update_time(self, t: float) -> None:
        if self._session:
            dur = self._session.duration
            self._time_lbl.setText(f"{_fmt_ms(t)} / {_fmt(dur)}")

    def _update_play_icon(self, playing: bool) -> None:
        self._play_btn.setText("⏸" if playing else "▶")

    def _update_delete_btn(self, sel_id: str) -> None:
        self._del_btn.setEnabled(bool(sel_id))
