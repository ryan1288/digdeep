"""Processing view — radial progress + stage list wired to PipelineWorker."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from src.app.widgets.buttons import GhostButton
from src.app.widgets.cards import ScreenHeader
from src.app.widgets.radial_progress import RadialProgress

BG = "#1d1f24"
PANEL = "#272a30"
PANEL_HI = "#32363d"
PANEL_LO = "#22252a"
BORDER = "#3f434b"
TEXT = "#f1f2f4"
TEXT_DIM = "#a8acb3"
TEXT_MUTE = "#74797f"
CORAL = "#ec8a5e"
GREEN = "#5cd0a5"

STAGES = [
    ("decode", "Decoding video", "Reading frames at source resolution"),
    ("ball", "Tracking the ball", "Heatmap regression over 9-frame windows"),
    ("players", "Finding players", "RF-DETR on every frame"),
    ("track", "Linking players across frames", "BoT-SORT-ReID with appearance memory"),
    ("rally", "Detecting rallies", "Ball trajectory + game-state fusion"),
    ("snip", "Snipping rallies", "Almost done…"),
]

_STAGE_KEYWORDS = {
    "opening": 0,
    "loading": 0,
    "decoding": 0,
    "ball": 1,
    "tracking": 1,
    "player": 2,
    "finding": 2,
    "linking": 3,
    "rally": 4,
    "detecting": 4,
    "extracting": 5,
    "snipping": 5,
    "writing": 5,
}


class ProcessingView(QWidget):
    processing_done = Signal(str)
    cancelled = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"background: {BG};")
        self._worker = None
        self._stage_idx = 0
        self._stage_rows: list[_StageRow] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._header = ScreenHeader("Processing match", "")
        layout.addWidget(self._header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background: {BG};")

        content = QWidget()
        content.setStyleSheet(f"background: {BG};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(36, 8, 36, 36)
        content_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        content_layout.setSpacing(24)

        self._radial = RadialProgress()
        content_layout.addWidget(self._radial, alignment=Qt.AlignHCenter)

        # Current-stage card
        self._stage_card = QWidget()
        self._stage_card.setFixedWidth(480)
        self._stage_card.setStyleSheet(f"""
            background: {PANEL};
            border: 1px solid {BORDER};
            border-radius: 12px;
        """)
        sc_layout = QVBoxLayout(self._stage_card)
        sc_layout.setContentsMargins(20, 16, 20, 16)
        sc_layout.setSpacing(4)
        self._stage_title_lbl = QLabel("Initialising…")
        self._stage_title_lbl.setStyleSheet(
            f"font-size: 15px; font-weight: 600; color: {TEXT}; background: transparent;"
        )
        self._stage_title_lbl.setAlignment(Qt.AlignCenter)
        self._stage_detail_lbl = QLabel("")
        self._stage_detail_lbl.setStyleSheet(
            f"font-size: 12px; color: {TEXT_DIM}; background: transparent;"
        )
        self._stage_detail_lbl.setAlignment(Qt.AlignCenter)
        sc_layout.addWidget(self._stage_title_lbl)
        sc_layout.addWidget(self._stage_detail_lbl)
        content_layout.addWidget(self._stage_card, alignment=Qt.AlignHCenter)

        # Stage list
        stage_list_container = QWidget()
        stage_list_container.setFixedWidth(560)
        stage_list_container.setStyleSheet(f"""
            background: {PANEL};
            border: 1px solid {BORDER};
            border-radius: 12px;
        """)
        stage_list_layout = QVBoxLayout(stage_list_container)
        stage_list_layout.setContentsMargins(4, 4, 4, 4)
        stage_list_layout.setSpacing(0)

        for i, (key, label, detail) in enumerate(STAGES):
            row = _StageRow(i + 1, label)
            stage_list_layout.addWidget(row)
            self._stage_rows.append(row)

        content_layout.addWidget(stage_list_container, alignment=Qt.AlignHCenter)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.setAlignment(Qt.AlignHCenter)
        cancel_btn = GhostButton("Cancel")
        cancel_btn.clicked.connect(self._cancel)
        self._skip_btn = GhostButton("Skip ahead (demo)")
        self._skip_btn.clicked.connect(self._skip_demo)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(self._skip_btn)
        content_layout.addLayout(btn_row)

        self._error_lbl = QLabel("")
        self._error_lbl.setStyleSheet(f"""
            background: #4a1a1a; color: #f08080;
            border: 1px solid #7a2a2a; border-radius: 8px;
            padding: 10px 16px; font-size: 13px;
        """)
        self._error_lbl.setWordWrap(True)
        self._error_lbl.hide()
        content_layout.addWidget(self._error_lbl)

        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

    def set_worker(self, worker) -> None:
        self._worker = worker
        self._stage_idx = 0
        self._error_lbl.hide()
        self._radial.set_value(0)
        for row in self._stage_rows:
            row.set_state("pending")
        if worker:
            fname = getattr(worker, "_video_path", "")
            self._header = ScreenHeader(
                "Processing match", fname.split("/")[-1] if fname else ""
            )
            worker.stage_changed.connect(self._on_stage_changed)
            worker.progress.connect(self._on_progress)
            worker.finished.connect(self._on_finished)
            worker.error.connect(self._on_error)

    @Slot(str)
    def _on_stage_changed(self, stage: str) -> None:
        stage_lower = stage.lower()
        idx = None
        for kw, i in _STAGE_KEYWORDS.items():
            if kw in stage_lower:
                idx = i
                break
        if idx is not None and idx != self._stage_idx:
            if self._stage_idx < len(self._stage_rows):
                self._stage_rows[self._stage_idx].set_state("done")
            self._stage_idx = idx
            if idx < len(self._stage_rows):
                self._stage_rows[idx].set_state("active")
        self._stage_title_lbl.setText(
            STAGES[self._stage_idx][1] if self._stage_idx < len(STAGES) else stage
        )
        self._stage_detail_lbl.setText(stage)

    @Slot(int, int)
    def _on_progress(self, current: int, total: int) -> None:
        if total > 0:
            self._radial.set_value(current / total * 100)

    @Slot(str)
    def _on_finished(self, path: str) -> None:
        self._radial.set_value(100)
        for row in self._stage_rows:
            row.set_state("done")
        QTimer.singleShot(500, lambda: self.processing_done.emit(path))

    @Slot(str)
    def _on_error(self, msg: str) -> None:
        self._error_lbl.setText(f"Error: {msg}")
        self._error_lbl.show()

    def _cancel(self) -> None:
        if self._worker:
            self._worker.terminate()
        self.cancelled.emit()

    def _skip_demo(self) -> None:
        # Demo shortcut — jumps to done state
        self._on_finished("")


class _StageRow(QWidget):
    def __init__(self, number: int, label: str, parent=None) -> None:
        super().__init__(parent)
        self._number = number
        self._label = label
        self._state = "pending"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(14)

        self._icon_lbl = QLabel(str(number))
        self._icon_lbl.setFixedSize(22, 22)
        self._icon_lbl.setAlignment(Qt.AlignCenter)
        self._icon_lbl.setStyleSheet(f"""
            background: {PANEL_LO}; color: {TEXT_MUTE};
            border: 1px solid {BORDER}; border-radius: 11px;
            font-family: 'JetBrains Mono'; font-size: 11px; font-weight: 600;
        """)
        layout.addWidget(self._icon_lbl)

        self._label_lbl = QLabel(label)
        self._label_lbl.setStyleSheet(
            f"color: {TEXT_MUTE}; font-size: 13px; background: transparent;"
        )
        layout.addWidget(self._label_lbl, stretch=1)

        self._done_lbl = QLabel("")
        self._done_lbl.setStyleSheet(
            f"font-family: 'JetBrains Mono'; font-size: 10px; color: {TEXT_MUTE}; background: transparent;"
        )
        layout.addWidget(self._done_lbl)

        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._pulse)
        self._pulse_phase = 0

    def set_state(self, state: str) -> None:
        self._state = state
        self._pulse_timer.stop()

        if state == "done":
            self.setStyleSheet("background: transparent;")
            self._icon_lbl.setText("✓")
            self._icon_lbl.setStyleSheet(f"""
                background: {GREEN}; color: black;
                border: 1px solid {GREEN}; border-radius: 11px;
                font-size: 11px; font-weight: 700;
            """)
            self._label_lbl.setStyleSheet(
                f"color: {TEXT_DIM}; font-size: 13px; background: transparent;"
            )
            self._done_lbl.setText("done")
        elif state == "active":
            self.setStyleSheet(f"background: {PANEL_HI}; border-radius: 8px;")
            self._icon_lbl.setText("●")
            self._icon_lbl.setStyleSheet(f"""
                background: {CORAL}; color: white;
                border: 1px solid {CORAL}; border-radius: 11px;
                font-size: 11px;
            """)
            self._label_lbl.setStyleSheet(
                f"color: {TEXT}; font-size: 13px; font-weight: 600; background: transparent;"
            )
            self._done_lbl.setText("")
            self._pulse_timer.start(600)
        else:
            self.setStyleSheet("background: transparent;")
            self._icon_lbl.setText(str(self._number))
            self._icon_lbl.setStyleSheet(f"""
                background: {PANEL_LO}; color: {TEXT_MUTE};
                border: 1px solid {BORDER}; border-radius: 11px;
                font-family: 'JetBrains Mono'; font-size: 11px; font-weight: 600;
            """)
            self._label_lbl.setStyleSheet(
                f"color: {TEXT_MUTE}; font-size: 13px; background: transparent;"
            )
            self._done_lbl.setText("")

    def _pulse(self) -> None:
        self._pulse_phase = (self._pulse_phase + 1) % 2
        if self._pulse_phase == 0:
            self._icon_lbl.setText("●")
        else:
            self._icon_lbl.setText("○")
