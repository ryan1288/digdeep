"""EditorView — the centerpiece editing screen."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QSizePolicy,
                               QSplitter, QVBoxLayout, QWidget)

from src.app.widgets.rally_list import RallyList
from src.app.widgets.timeline import Timeline
from src.app.widgets.transport_bar import TransportBar
from src.app.widgets.video_panel import VideoPanel

PANEL = "#272a30"
PANEL_LO = "#22252a"
BORDER = "#3f434b"
BORDER_HI = "#52575f"
TEXT = "#f1f2f4"
TEXT_DIM = "#a8acb3"
TEXT_MUTE = "#74797f"
CORAL = "#ec8a5e"
BG = "#1d1f24"


class EditorView(QWidget):
    """Full editor: video, transport, timeline, rally list.

    Args:
        session: Shared MatchSession instance.
        media_player: Shared QMediaPlayer instance (already has audio output set).
    """

    export_requested = Signal()

    def __init__(self, session, media_player: QMediaPlayer, parent=None) -> None:
        super().__init__(parent)
        self._session = session
        self._media_player = media_player
        self.setStyleSheet(f"background: {BG};")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Top bar
        self._top_bar = _EditorTopBar(session)
        self._top_bar.export_clicked.connect(self.export_requested)
        self._top_bar.undo_clicked.connect(session.undo)
        self._top_bar.redo_clicked.connect(session.redo)
        root.addWidget(self._top_bar)

        # Splitter: left column + rally list
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {BORDER};
                width: 1px;
            }}
        """)
        splitter.setChildrenCollapsible(False)
        root.addWidget(splitter, stretch=1)

        # Left column: video + transport + timeline
        left = QWidget()
        left.setStyleSheet(f"background: {BG};")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self._video_panel = VideoPanel(media_player, session)
        left_layout.addWidget(self._video_panel, stretch=1)

        self._transport = TransportBar(session)
        self._transport.play_pause_clicked.connect(self._toggle_play)
        self._transport.prev_rally_clicked.connect(self._prev_rally)
        self._transport.next_rally_clicked.connect(self._next_rally)
        self._transport.add_rally_clicked.connect(self._add_rally)
        self._transport.delete_rally_clicked.connect(self._delete_selected)
        self._transport.zoom_changed.connect(self._on_zoom_changed)
        left_layout.addWidget(self._transport)

        self._timeline = Timeline()
        self._timeline.set_session(session)
        left_layout.addWidget(self._timeline)

        splitter.addWidget(left)

        # Right: rally list
        self._rally_list = RallyList()
        self._rally_list.set_session(session)
        self._rally_list.rally_selected.connect(self._on_rally_selected)
        splitter.addWidget(self._rally_list)

        # Splitter stretch: left takes all extra space
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        # Media player → session playhead (one direction)
        self._media_player.positionChanged.connect(self._on_position_changed)
        # Session playhead → media player (other direction, guarded)
        session.playhead_changed.connect(self._on_session_playhead)

        # Undo/redo state → top bar buttons
        session.can_undo_changed.connect(self._top_bar.set_can_undo)
        session.can_redo_changed.connect(self._top_bar.set_can_redo)

        self._install_shortcuts()
        self._syncing_playhead = False

    # ── Playhead sync (two-way, guarded) ──────────────────────────

    def _on_position_changed(self, ms: int) -> None:
        if self._syncing_playhead:
            return
        self._syncing_playhead = True
        self._session._raw_set_playhead(ms / 1000.0)
        self._syncing_playhead = False

    def _on_session_playhead(self, t: float) -> None:
        if self._syncing_playhead:
            return
        target_ms = int(t * 1000)
        if abs(self._media_player.position() - target_ms) > 100:
            self._syncing_playhead = True
            self._media_player.setPosition(target_ms)
            self._syncing_playhead = False

    # ── Transport actions ──────────────────────────────────────────

    def _toggle_play(self) -> None:
        if self._media_player.playbackState() == QMediaPlayer.PlayingState:
            self._media_player.pause()
            self._session.play_state_changed.emit(False)
        else:
            self._media_player.play()
            self._session.play_state_changed.emit(True)

    def _prev_rally(self) -> None:
        if self._session is None:
            return
        ph = self._session.playhead
        rallies = self._session.rallies
        for r in reversed(rallies):
            if r.start < ph - 0.5:
                self._session._raw_set_selected(r.id)
                self._session._raw_set_playhead(r.start)
                return

    def _next_rally(self) -> None:
        if self._session is None:
            return
        ph = self._session.playhead
        rallies = self._session.rallies
        for r in rallies:
            if r.start > ph + 0.5:
                self._session._raw_set_selected(r.id)
                self._session._raw_set_playhead(r.start)
                return

    def _add_rally(self) -> None:
        t = self._session.playhead
        self._session.add_rally(t)

    def _delete_selected(self) -> None:
        sel = self._session.selected_id
        if sel:
            self._session.delete_rally(sel)

    def _on_zoom_changed(self, zoom: float) -> None:
        self._timeline.set_zoom(zoom)

    def _on_rally_selected(self, rally_id: str) -> None:
        rally = self._session.rally_by_id(rally_id)
        if rally:
            self._media_player.setPosition(int(rally.start * 1000))

    # ── Keyboard shortcuts ─────────────────────────────────────────

    def _install_shortcuts(self) -> None:
        def sc(seq, fn):
            s = QShortcut(QKeySequence(seq), self)
            s.activated.connect(fn)
            return s

        sc("Space", self._toggle_play)
        sc("Left", lambda: self._nudge(-1.0))
        sc("Right", lambda: self._nudge(1.0))
        sc("Shift+Left", lambda: self._nudge(-5.0))
        sc("Shift+Right", lambda: self._nudge(5.0))
        sc("I", self._set_in)
        sc("O", self._set_out)
        sc("Delete", self._delete_selected)
        sc("Backspace", self._delete_selected)
        sc("Ctrl+Z", self._session.undo)
        sc("Ctrl+Shift+Z", self._session.redo)

    def _nudge(self, dt: float) -> None:
        t = max(0.0, self._session.playhead + dt)
        if self._session.duration > 0:
            t = min(self._session.duration, t)
        self._session._raw_set_playhead(t)

    def _set_in(self) -> None:
        sel = self._session.selected_id
        if sel:
            self._session.set_in(sel, self._session.playhead)

    def _set_out(self) -> None:
        sel = self._session.selected_id
        if sel:
            self._session.set_out(sel, self._session.playhead)


# ── EditorTopBar ────────────────────────────────────────────────────────


class _EditorTopBar(QWidget):
    """56px fixed-height top bar: title, undo/redo, export."""

    export_clicked = Signal()
    undo_clicked = Signal()
    redo_clicked = Signal()

    def __init__(self, session, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(56)
        self.setStyleSheet(f"""
            QWidget {{
                background: {PANEL};
                border-bottom: 1px solid {BORDER};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(12)

        # Scissors + title
        icon_lbl = QLabel("✂")
        icon_lbl.setStyleSheet(
            f"font-size: 16px; color: {CORAL}; background: transparent;"
        )
        layout.addWidget(icon_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        title_lbl = QLabel("Rally Editor")
        title_lbl.setStyleSheet(
            f"font-size: 13px; font-weight: 600; color: {TEXT}; background: transparent;"
        )
        title_col.addWidget(title_lbl)
        sub_lbl = QLabel("Drag handles or use I/O keys to trim")
        sub_lbl.setStyleSheet(
            f"font-family: 'JetBrains Mono'; font-size: 10px; color: {TEXT_MUTE}; background: transparent;"
        )
        title_col.addWidget(sub_lbl)
        layout.addLayout(title_col)

        layout.addStretch()

        # Undo button
        self._undo_btn = _TopBtn("↩ Undo")
        self._undo_btn.setEnabled(False)
        self._undo_btn.clicked.connect(self.undo_clicked)
        layout.addWidget(self._undo_btn)

        # Redo button
        self._redo_btn = _TopBtn("↪ Redo")
        self._redo_btn.setEnabled(False)
        self._redo_btn.clicked.connect(self.redo_clicked)
        layout.addWidget(self._redo_btn)

        # Auto-save badge
        badge = QLabel("● Auto-saved")
        badge.setStyleSheet(f"""
            font-size: 10px; color: #5cd0a5;
            background: transparent; padding: 0 8px;
        """)
        layout.addWidget(badge)

        # Export button
        export_btn = QPushButton("Export")
        export_btn.setFixedHeight(34)
        export_btn.setStyleSheet(f"""
            QPushButton {{
                background: {CORAL}; color: white;
                border: none; border-radius: 7px;
                padding: 0 18px; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background: #f09870; }}
            QPushButton:pressed {{ background: #c66b44; }}
        """)
        export_btn.clicked.connect(self.export_clicked)
        layout.addWidget(export_btn)

        if session:
            session.can_undo_changed.connect(self.set_can_undo)
            session.can_redo_changed.connect(self.set_can_redo)

    def set_can_undo(self, enabled: bool) -> None:
        self._undo_btn.setEnabled(enabled)

    def set_can_redo(self, enabled: bool) -> None:
        self._redo_btn.setEnabled(enabled)


class _TopBtn(QPushButton):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)
        self.setFixedHeight(32)
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: 1px solid {BORDER_HI};
                border-radius: 6px; padding: 0 12px;
                color: {TEXT_DIM}; font-size: 12px;
            }}
            QPushButton:enabled {{
                color: {TEXT};
            }}
            QPushButton:enabled:hover {{
                background: rgba(255,255,255,12);
            }}
            QPushButton:disabled {{
                color: {TEXT_MUTE}; border-color: {BORDER};
            }}
        """)
