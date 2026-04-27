"""VideoPanel — QVideoWidget inside a black surface with overlay labels."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

TEXT = "#f1f2f4"
TEXT_DIM = "#a8acb3"
CORAL = "#ec8a5e"
BORDER = "#3f434b"


def _fmt_ms(s: float) -> str:
    s = max(0.0, s)
    m = int(s // 60)
    sec = int(s % 60)
    ms = int((s - int(s)) * 1000)
    return f"{m:02d}:{sec:02d}.{ms:03d}"


def _fmt(s: float) -> str:
    if s < 0:
        s = 0
    m = int(s // 60)
    sec = int(s % 60)
    return f"{m}:{sec:02d}"


class VideoPanel(QWidget):
    """QVideoWidget with overlay pills for rally state + timecode."""

    def __init__(self, media_player, session, parent=None) -> None:
        super().__init__(parent)
        self._player = media_player
        self._session = session
        self.setStyleSheet("background: #000000;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Video widget
        self._video_widget = QVideoWidget(self)
        media_player.setVideoOutput(self._video_widget)
        self._video_widget.setStyleSheet("background: #000;")

        # Top-left pill
        self._rally_pill = QLabel("Between rallies", self)
        self._rally_pill.setStyleSheet(f"""
            background: rgba(0,0,0,0.6);
            color: {TEXT_DIM};
            border: 1px solid {BORDER};
            border-radius: 999px;
            padding: 6px 12px;
            font-size: 11px;
            font-weight: 500;
        """)
        self._rally_pill.adjustSize()

        # Bottom-right timecode
        self._timecode_lbl = QLabel("00:00.000", self)
        self._timecode_lbl.setStyleSheet(f"""
            background: rgba(0,0,0,0.7);
            color: {TEXT};
            border-radius: 5px;
            padding: 5px 10px;
            font-family: 'JetBrains Mono';
            font-size: 12px;
            letter-spacing: 0.5px;
        """)
        self._timecode_lbl.adjustSize()

        if session:
            session.playhead_changed.connect(self._update_overlay)
            session.rallies_changed.connect(
                lambda: self._update_overlay(session.playhead)
            )

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        self._video_widget.setGeometry(0, 0, w, h)
        # Position overlay pills
        self._rally_pill.adjustSize()
        self._rally_pill.move(16, 16)
        self._timecode_lbl.adjustSize()
        tc_w = self._timecode_lbl.width()
        tc_h = self._timecode_lbl.height()
        self._timecode_lbl.move(w - tc_w - 16, h - tc_h - 16)

    def _update_overlay(self, t: float) -> None:
        if self._session is None:
            return
        self._timecode_lbl.setText(_fmt_ms(t))
        self._timecode_lbl.adjustSize()
        tc_w = self._timecode_lbl.width()
        tc_h = self._timecode_lbl.height()
        self._timecode_lbl.move(self.width() - tc_w - 16, self.height() - tc_h - 16)

        rally = self._session.rally_at_time(t)
        rallies = self._session.rallies
        if rally and rallies:
            try:
                idx = next(i for i, r in enumerate(rallies) if r.id == rally.id) + 1
            except StopIteration:
                idx = 1
            total = len(rallies)
            elapsed = t - rally.start
            dur = rally.duration
            self._rally_pill.setText(
                f"Rally {idx} of {total}   {_fmt(elapsed)} / {_fmt(dur)}"
            )
            self._rally_pill.setStyleSheet(f"""
                background: rgba(0,0,0,0.6);
                color: {TEXT};
                border: 1px solid {CORAL};
                border-radius: 999px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.5px;
            """)
        else:
            self._rally_pill.setText("Between rallies")
            self._rally_pill.setStyleSheet(f"""
                background: rgba(0,0,0,0.6);
                color: {TEXT_DIM};
                border: 1px solid {BORDER};
                border-radius: 999px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 500;
            """)
        self._rally_pill.adjustSize()
        self._rally_pill.move(16, 16)
