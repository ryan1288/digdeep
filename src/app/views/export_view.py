"""ExportView — format selection, options, and export execution."""

from __future__ import annotations

import subprocess
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (QButtonGroup, QFileDialog, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QRadioButton,
                               QSizePolicy, QVBoxLayout, QWidget)

from src.app.widgets.cards import ScreenHeader

BG = "#1d1f24"
PANEL = "#272a30"
PANEL_LO = "#22252a"
BORDER = "#3f434b"
BORDER_HI = "#52575f"
TEXT = "#f1f2f4"
TEXT_DIM = "#a8acb3"
TEXT_MUTE = "#74797f"
CORAL = "#ec8a5e"
GREEN = "#5cd0a5"


class ExportView(QWidget):
    """Export configuration and progress screen.

    Args:
        session: Shared MatchSession.
    """

    def __init__(self, session, parent=None) -> None:
        super().__init__(parent)
        self._session = session
        self._source_path = ""
        self._output_path = ""
        self._worker: "_ExportWorker | None" = None
        self.setStyleSheet(f"background: {BG};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = ScreenHeader(
            "Export",
            "Render rally-only clips to disk",
        )
        layout.addWidget(header)

        scroll_content = QWidget()
        scroll_content.setStyleSheet(f"background: {BG};")
        inner = QVBoxLayout(scroll_content)
        inner.setContentsMargins(24, 24, 24, 24)
        inner.setSpacing(20)

        # Two-column layout
        cols = QHBoxLayout()
        cols.setSpacing(20)
        cols.setAlignment(Qt.AlignTop)

        # Left: options
        left = QVBoxLayout()
        left.setSpacing(16)

        # Format card
        fmt_card = _SectionCard("Output Format")
        fmt_layout = QVBoxLayout(fmt_card)
        fmt_layout.setContentsMargins(16, 16, 16, 16)
        fmt_layout.setSpacing(10)
        self._fmt_group = QButtonGroup()
        for label, value, checked in [
            ("Single MP4 (all rallies combined)", "single", True),
            ("Per-clip MP4s (one file per rally)", "clips", False),
            ("GIF (first 30 s, for sharing)", "gif", False),
        ]:
            rb = QRadioButton(label)
            rb.setChecked(checked)
            rb.setProperty("value", value)
            rb.setStyleSheet(f"""
                QRadioButton {{
                    color: {TEXT}; font-size: 12px; background: transparent;
                    spacing: 8px;
                }}
                QRadioButton::indicator {{
                    width: 14px; height: 14px;
                    border: 1px solid {BORDER_HI};
                    border-radius: 7px; background: transparent;
                }}
                QRadioButton::indicator:checked {{
                    background: {CORAL}; border-color: {CORAL};
                }}
            """)
            self._fmt_group.addButton(rb)
            fmt_layout.addWidget(rb)
        left.addWidget(fmt_card)

        # Options card
        opt_card = _SectionCard("Options")
        opt_layout = QVBoxLayout(opt_card)
        opt_layout.setContentsMargins(16, 16, 16, 16)
        opt_layout.setSpacing(10)
        self._pre_roll_cb = _OptionRow(
            "Pre-roll padding", "2 s before each rally", True
        )
        self._post_roll_cb = _OptionRow(
            "Post-roll padding", "2 s after each rally", True
        )
        self._skip_fp_cb = _OptionRow(
            "Skip false positives", "Exclude marked rallies", True
        )
        opt_layout.addWidget(self._pre_roll_cb)
        opt_layout.addWidget(self._post_roll_cb)
        opt_layout.addWidget(self._skip_fp_cb)
        left.addWidget(opt_card)

        # Output folder
        folder_card = _SectionCard("Output Folder")
        folder_layout = QHBoxLayout(folder_card)
        folder_layout.setContentsMargins(16, 14, 16, 14)
        folder_layout.setSpacing(8)
        self._folder_edit = QLineEdit()
        self._folder_edit.setReadOnly(True)
        self._folder_edit.setPlaceholderText("Same folder as source video")
        self._folder_edit.setStyleSheet(f"""
            QLineEdit {{
                background: {PANEL_LO}; border: 1px solid {BORDER};
                border-radius: 6px; padding: 6px 10px;
                color: {TEXT}; font-size: 12px;
            }}
        """)
        folder_layout.addWidget(self._folder_edit, stretch=1)
        browse_btn = QPushButton("Browse…")
        browse_btn.setFixedHeight(32)
        browse_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: 1px solid {BORDER_HI};
                border-radius: 6px; padding: 0 12px;
                color: {TEXT}; font-size: 11px;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,10); }}
        """)
        browse_btn.clicked.connect(self._pick_folder)
        folder_layout.addWidget(browse_btn)
        left.addWidget(folder_card)

        cols.addLayout(left, stretch=3)

        # Right: summary card + export button
        right = QVBoxLayout()
        right.setSpacing(16)
        right.setAlignment(Qt.AlignTop)

        self._summary_card = _SummaryCard(session)
        right.addWidget(self._summary_card)

        self._export_btn = QPushButton("Export")
        self._export_btn.setFixedHeight(44)
        self._export_btn.setStyleSheet(f"""
            QPushButton {{
                background: {CORAL}; color: white;
                border: none; border-radius: 8px;
                font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background: #f09870; }}
            QPushButton:pressed {{ background: #c66b44; }}
        """)
        self._export_btn.clicked.connect(self._start_export)
        right.addWidget(self._export_btn)

        # Success / progress state (hidden by default)
        self._progress_lbl = QLabel("")
        self._progress_lbl.setAlignment(Qt.AlignCenter)
        self._progress_lbl.setStyleSheet(
            f"font-size: 12px; color: {TEXT_DIM}; background: transparent;"
        )
        self._progress_lbl.hide()
        right.addWidget(self._progress_lbl)

        self._reveal_btn = QPushButton("📂 Reveal in Files")
        self._reveal_btn.setFixedHeight(36)
        self._reveal_btn.hide()
        self._reveal_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: 1px solid {BORDER_HI};
                border-radius: 7px; color: {TEXT}; font-size: 12px;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,10); }}
        """)
        self._reveal_btn.clicked.connect(self._reveal_output)
        right.addWidget(self._reveal_btn)

        cols.addLayout(right, stretch=2)
        inner.addLayout(cols)
        inner.addStretch()

        layout.addWidget(scroll_content, stretch=1)

        if session:
            session.rallies_changed.connect(self._summary_card.refresh)

    def set_export_context(self, source_path: str, output_path: str) -> None:
        self._source_path = source_path
        self._output_path = output_path
        self._summary_card.refresh()

    def _pick_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose output folder")
        if folder:
            self._folder_edit.setText(folder)

    def _start_export(self) -> None:
        output_path = self._output_path
        if not output_path:
            self._progress_lbl.setText("No processed video available.")
            self._progress_lbl.show()
            return

        out_dir = self._folder_edit.text() or str(Path(output_path).parent)
        checked_btn = self._fmt_group.checkedButton()
        mode = checked_btn.property("value") if checked_btn else "single"
        pre_roll = self._pre_roll_cb.is_checked()
        post_roll = self._post_roll_cb.is_checked()
        skip_fp = self._skip_fp_cb.is_checked()

        rallies = self._session.rallies if self._session else []
        if skip_fp:
            rallies = [r for r in rallies if not r.fp]

        self._export_btn.setEnabled(False)
        self._progress_lbl.setText("Exporting…")
        self._progress_lbl.show()
        self._reveal_btn.hide()

        self._worker = _ExportWorker(
            output_path, out_dir, mode, rallies, pre_roll, post_roll
        )
        self._worker.finished.connect(self._on_export_done)
        self._worker.error.connect(self._on_export_error)
        self._worker.start()

    @Slot(str)
    def _on_export_done(self, path: str) -> None:
        self._last_output_dir = str(Path(path).parent)
        self._progress_lbl.setText(f"Saved to {Path(path).name}")
        self._reveal_btn.show()
        self._export_btn.setEnabled(True)

    @Slot(str)
    def _on_export_error(self, msg: str) -> None:
        self._progress_lbl.setText(f"Error: {msg}")
        self._export_btn.setEnabled(True)

    def _reveal_output(self) -> None:
        d = getattr(self, "_last_output_dir", "")
        if not d:
            return
        try:
            subprocess.Popen(["xdg-open", d])
        except Exception:
            pass


class _SectionCard(QWidget):
    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"""
            QWidget {{
                background: {PANEL};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title_bar = QWidget()
        title_bar.setStyleSheet(f"""
            background: transparent;
            border-bottom: 1px solid {BORDER};
        """)
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(16, 12, 16, 12)
        lbl = QLabel(title)
        lbl.setStyleSheet(
            f"font-size: 12px; font-weight: 600; color: {TEXT}; background: transparent;"
        )
        tb_layout.addWidget(lbl)
        layout.addWidget(title_bar)

    def layout(self):
        return super().layout()


class _OptionRow(QWidget):
    def __init__(self, label: str, sub: str, checked: bool, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"font-size: 12px; color: {TEXT}; background: transparent;")
        text_col.addWidget(lbl)
        sub_lbl = QLabel(sub)
        sub_lbl.setStyleSheet(
            f"font-size: 10px; color: {TEXT_MUTE}; background: transparent;"
        )
        text_col.addWidget(sub_lbl)
        layout.addLayout(text_col, stretch=1)

        from PySide6.QtWidgets import QCheckBox

        self._cb = QCheckBox()
        self._cb.setChecked(checked)
        self._cb.setStyleSheet(f"""
            QCheckBox::indicator {{
                width: 16px; height: 16px;
                border: 1px solid {BORDER_HI}; border-radius: 4px;
                background: transparent;
            }}
            QCheckBox::indicator:checked {{
                background: {CORAL}; border-color: {CORAL};
            }}
        """)
        layout.addWidget(self._cb)

    def is_checked(self) -> bool:
        return self._cb.isChecked()


class _SummaryCard(QWidget):
    def __init__(self, session, parent=None) -> None:
        super().__init__(parent)
        self._session = session
        self.setStyleSheet(f"""
            QWidget {{
                background: {PANEL};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title_lbl = QLabel("Summary")
        title_lbl.setStyleSheet(
            f"font-size: 12px; font-weight: 600; color: {TEXT}; background: transparent;"
        )
        layout.addWidget(title_lbl)

        self._rows: list[tuple[QLabel, QLabel]] = []
        for label in ["Rallies", "Skipped", "Total duration", "Estimated size"]:
            row = QHBoxLayout()
            key_lbl = QLabel(label)
            key_lbl.setStyleSheet(
                f"font-size: 11px; color: {TEXT_MUTE}; background: transparent;"
            )
            val_lbl = QLabel("—")
            val_lbl.setStyleSheet(
                f"font-family: 'JetBrains Mono'; font-size: 11px; color: {TEXT}; background: transparent;"
            )
            val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row.addWidget(key_lbl)
            row.addWidget(val_lbl)
            layout.addLayout(row)
            self._rows.append((key_lbl, val_lbl))

        self.refresh()

    def refresh(self) -> None:
        if not self._session:
            return
        rallies = self._session.rallies
        kept = [r for r in rallies if not r.fp]
        skipped = [r for r in rallies if r.fp]
        total_dur = sum(r.duration for r in kept)

        m = int(total_dur // 60)
        s = int(total_dur % 60)

        # Rough size estimate at ~2 Mbps
        size_mb = total_dur * 2_000_000 / 8 / 1_048_576

        labels = [
            str(len(kept)),
            str(len(skipped)),
            f"{m}:{s:02d}",
            f"~{size_mb:.0f} MB",
        ]
        for (_, val_lbl), val in zip(self._rows, labels):
            val_lbl.setText(val)


class _ExportWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(
        self,
        source_mp4: str,
        out_dir: str,
        mode: str,
        rallies,
        pre_roll: bool,
        post_roll: bool,
    ) -> None:
        super().__init__()
        self._source = source_mp4
        self._out_dir = out_dir
        self._mode = mode
        self._rallies = rallies
        self._pre = 2.0 if pre_roll else 0.0
        self._post = 2.0 if post_roll else 0.0

    def run(self) -> None:
        try:
            out_path = self._do_export()
            self.finished.emit(out_path)
        except Exception as e:
            self.error.emit(str(e))

    def _do_export(self) -> str:
        out_dir = Path(self._out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(self._source).stem

        if self._mode == "single" or self._mode == "gif":
            out_path = str(out_dir / f"{stem}_export.mp4")
            self._concat_all(out_path)
            return out_path
        else:
            # Per-clip: return directory
            for i, r in enumerate(self._rallies, 1):
                clip_path = str(out_dir / f"{stem}_rally_{i:03d}.mp4")
                self._clip(r.start, r.end, clip_path)
            return str(out_dir)

    def _clip(self, start: float, end: float, out: str) -> None:
        ss = max(0.0, start - self._pre)
        dur = (end + self._post) - ss
        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            str(ss),
            "-i",
            self._source,
            "-t",
            str(dur),
            "-c",
            "copy",
            out,
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.decode()[:200])

    def _concat_all(self, out: str) -> None:
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            for r in self._rallies:
                ss = max(0.0, r.start - self._pre)
                end = r.end + self._post
                f.write(f"file '{self._source}'\n")
                f.write(f"inpoint {ss}\n")
                f.write(f"outpoint {end}\n")
            list_path = f.name
        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                list_path,
                "-c",
                "copy",
                out,
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=600)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.decode()[:200])
        finally:
            os.unlink(list_path)
