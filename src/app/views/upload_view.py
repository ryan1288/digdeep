"""Upload view — drop zone + progress bar."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (QFileDialog, QFrame, QHBoxLayout, QLabel,
                               QProgressBar, QPushButton, QVBoxLayout, QWidget)

from src.app.widgets.buttons import GhostButton
from src.app.widgets.cards import ScreenHeader

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


class UploadView(QWidget):
    process_requested = Signal(str)
    cancelled = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"background: {BG};")
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(
            ScreenHeader(
                "New match", "Drop a full-match recording. We'll handle the trimming."
            )
        )

        inner = QWidget()
        inner.setStyleSheet(f"background: {BG};")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(36, 8, 36, 36)
        inner_layout.setSpacing(0)

        self._stack = QWidget()
        stack_layout = QVBoxLayout(self._stack)
        stack_layout.setContentsMargins(0, 0, 0, 0)
        stack_layout.setSpacing(0)

        self._drop_zone = self._build_drop_zone()
        stack_layout.addWidget(self._drop_zone)

        self._loading_panel = self._build_loading_panel()
        self._loading_panel.hide()
        stack_layout.addWidget(self._loading_panel)

        inner_layout.addWidget(self._stack, stretch=1)
        layout.addWidget(inner, stretch=1)

        self._file_path = ""

    def _build_drop_zone(self) -> QWidget:
        w = QWidget()
        w.setMinimumHeight(320)
        w.setStyleSheet(f"""
            QWidget#DropZone {{
                border: 2px dashed {BORDER_HI};
                border-radius: 16px;
                background: {PANEL_LO};
            }}
            QWidget#DropZone:hover {{
                border-color: {CORAL};
                background: {PANEL};
            }}
        """)
        w.setObjectName("DropZone")
        w.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(18)

        icon_tile = QWidget()
        icon_tile.setFixedSize(72, 72)
        icon_tile.setStyleSheet(f"""
            background: {PANEL};
            border: 1px solid {BORDER};
            border-radius: 18px;
        """)
        icon_inner = QVBoxLayout(icon_tile)
        icon_inner.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel("↑")
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(
            f"color: {CORAL}; font-size: 28px; background: transparent; border: none;"
        )
        icon_inner.addWidget(icon_lbl)
        layout.addWidget(icon_tile, alignment=Qt.AlignCenter)

        text_col = QWidget()
        text_col.setStyleSheet("background: transparent;")
        text_layout = QVBoxLayout(text_col)
        text_layout.setSpacing(6)
        text_layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Drop a match video here")
        title.setStyleSheet(
            f"font-size: 18px; font-weight: 600; color: {TEXT}; background: transparent;"
        )
        title.setAlignment(Qt.AlignCenter)
        text_layout.addWidget(title)

        sub = QLabel("or click to browse · MP4, MOV, MKV up to 8 GB")
        sub.setStyleSheet(
            f"font-size: 13px; color: {TEXT_DIM}; background: transparent;"
        )
        sub.setAlignment(Qt.AlignCenter)
        text_layout.addWidget(sub)
        layout.addWidget(text_col)

        btn = QPushButton("Choose file")
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {CORAL}; color: white;
                border: none; border-radius: 7px;
                padding: 8px 16px; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background: #f09870; }}
        """)
        btn.clicked.connect(self._browse)
        layout.addWidget(btn, alignment=Qt.AlignCenter)

        tips = self._build_tips()
        layout.addWidget(tips)

        w.mousePressEvent = lambda e: (
            self._browse() if e.button() == Qt.LeftButton else None
        )
        return w

    def _build_tips(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(w)
        layout.setSpacing(24)
        layout.setAlignment(Qt.AlignCenter)
        for h, b in [
            ("Static camera", "Tripod or stable mount works best"),
            ("Whole court visible", "Both sides + sidelines in frame"),
            ("1080p is plenty", "Higher res doesn't improve detection"),
        ]:
            col = QWidget()
            col.setStyleSheet("background: transparent;")
            col.setMaximumWidth(180)
            col_layout = QVBoxLayout(col)
            col_layout.setSpacing(2)
            col_layout.setAlignment(Qt.AlignCenter)
            head = QLabel(h)
            head.setStyleSheet(
                f"font-size: 12px; font-weight: 600; color: {TEXT_DIM}; background: transparent;"
            )
            head.setAlignment(Qt.AlignCenter)
            body = QLabel(b)
            body.setStyleSheet(
                f"font-size: 11px; color: {TEXT_MUTE}; background: transparent;"
            )
            body.setAlignment(Qt.AlignCenter)
            body.setWordWrap(True)
            col_layout.addWidget(head)
            col_layout.addWidget(body)
            layout.addWidget(col)
        return w

    def _build_loading_panel(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background: {BG};")

        outer = QVBoxLayout(w)
        outer.setAlignment(Qt.AlignCenter)
        outer.setSpacing(0)

        card = QWidget()
        card.setFixedWidth(480)
        card.setStyleSheet(f"""
            background: {PANEL};
            border: 1px solid {BORDER};
            border-radius: 14px;
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(18)

        # File row
        file_row = QHBoxLayout()
        file_icon = QWidget()
        file_icon.setFixedSize(44, 44)
        file_icon.setStyleSheet(f"""
            background: {PANEL_HI};
            border-radius: 10px;
        """)
        file_icon_lbl = QLabel("🎬")
        file_icon_lbl.setAlignment(Qt.AlignCenter)
        file_icon_lbl.setStyleSheet("background: transparent; font-size: 18px;")
        QVBoxLayout(file_icon).addWidget(file_icon_lbl)
        file_row.addWidget(file_icon)

        file_text = QVBoxLayout()
        file_text.setSpacing(2)
        self._file_name_lbl = QLabel("")
        self._file_name_lbl.setStyleSheet(
            f"font-size: 14px; font-weight: 600; color: {TEXT}; background: transparent;"
        )
        self._file_size_lbl = QLabel("")
        self._file_size_lbl.setStyleSheet(
            f"font-family: 'JetBrains Mono'; font-size: 11px; color: {TEXT_MUTE}; background: transparent;"
        )
        file_text.addWidget(self._file_name_lbl)
        file_text.addWidget(self._file_size_lbl)
        file_row.addLayout(file_text, stretch=1)

        cancel_btn = QPushButton("×")
        cancel_btn.setFixedSize(28, 28)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: 1px solid {BORDER};
                border-radius: 7px; color: {TEXT_DIM}; font-size: 16px;
            }}
            QPushButton:hover {{ background: {PANEL_HI}; color: {TEXT}; }}
        """)
        cancel_btn.clicked.connect(self._cancel)
        file_row.addWidget(cancel_btn)
        card_layout.addLayout(file_row)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(6)
        card_layout.addWidget(self._progress)

        bottom_row = QHBoxLayout()
        self._progress_lbl = QLabel("Preparing...")
        self._progress_lbl.setStyleSheet(
            f"font-family: 'JetBrains Mono'; font-size: 11px; color: {TEXT_DIM}; background: transparent;"
        )
        self._pct_lbl = QLabel("0%")
        self._pct_lbl.setStyleSheet(
            f"font-family: 'JetBrains Mono'; font-size: 11px; color: {TEXT_DIM}; background: transparent;"
        )
        bottom_row.addWidget(self._progress_lbl)
        bottom_row.addStretch()
        bottom_row.addWidget(self._pct_lbl)
        card_layout.addLayout(bottom_row)

        outer.addWidget(card)
        return w

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Match Video",
            "",
            "Video Files (*.mp4 *.mov *.mkv *.avi *.m4v)",
        )
        if path:
            self._start_loading(path)

    def _start_loading(self, path: str) -> None:
        self._file_path = path
        name = Path(path).name
        size_bytes = Path(path).stat().st_size if Path(path).exists() else 0
        size_str = (
            f"{size_bytes / 1e9:.1f} GB"
            if size_bytes > 1e9
            else f"{size_bytes / 1e6:.0f} MB"
        )

        self._file_name_lbl.setText(name)
        self._file_size_lbl.setText(size_str)
        self._progress.setValue(0)
        self._pct_lbl.setText("0%")
        self._progress_lbl.setText("Validating…")

        self._drop_zone.hide()
        self._loading_panel.show()

        # Brief validation delay then go straight to processing
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._emit_process)
        self._timer.start(600)

        # Animate progress bar while waiting
        self._anim_value = 0
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._advance_progress)
        self._anim_timer.start(30)

    def _advance_progress(self) -> None:
        self._anim_value = min(90, self._anim_value + 3)
        self._progress.setValue(int(self._anim_value))
        self._pct_lbl.setText(f"{int(self._anim_value)}%")

    def _emit_process(self) -> None:
        self._anim_timer.stop()
        self._progress.setValue(100)
        self._pct_lbl.setText("100%")
        self.process_requested.emit(self._file_path)

    def _cancel(self) -> None:
        if hasattr(self, "_timer"):
            self._timer.stop()
        if hasattr(self, "_anim_timer"):
            self._anim_timer.stop()
        self._loading_panel.hide()
        self._drop_zone.show()
        self.cancelled.emit()

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if Path(path).suffix.lower() in (".mp4", ".mov", ".mkv", ".avi", ".m4v"):
                self._start_loading(path)
