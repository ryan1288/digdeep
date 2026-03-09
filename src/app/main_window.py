"""Main application window for DigDeep Rally Extractor."""

from __future__ import annotations

from omegaconf import DictConfig
from PySide6.QtWidgets import (QFileDialog, QHBoxLayout, QLabel, QMainWindow,
                               QMessageBox, QProgressBar, QPushButton,
                               QVBoxLayout, QWidget)

from src.app.worker import PipelineWorker


class MainWindow(QMainWindow):
    """Primary application window.

    Args:
        cfg: Hydra DictConfig loaded from configs/app/app.yaml.
    """

    def __init__(self, cfg: DictConfig) -> None:
        super().__init__()
        self._cfg = cfg
        self._video_path: str = ""
        self._output_dir: str = ""
        self._worker: PipelineWorker | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Input row
        input_row = QHBoxLayout()
        input_row.addWidget(QLabel("Input Video:"))
        self._input_label = QLabel("(none)")
        self._input_label.setWordWrap(True)
        input_row.addWidget(self._input_label, stretch=1)
        browse_input = QPushButton("Browse...")
        browse_input.clicked.connect(self._pick_input)
        input_row.addWidget(browse_input)
        layout.addLayout(input_row)

        # Output row
        output_row = QHBoxLayout()
        output_row.addWidget(QLabel("Output Dir:"))
        self._output_label = QLabel("(none)")
        self._output_label.setWordWrap(True)
        output_row.addWidget(self._output_label, stretch=1)
        browse_output = QPushButton("Browse...")
        browse_output.clicked.connect(self._pick_output_dir)
        output_row.addWidget(browse_output)
        layout.addLayout(output_row)

        # Process button
        self._process_btn = QPushButton("Process")
        self._process_btn.setEnabled(False)
        self._process_btn.clicked.connect(self._start_processing)
        layout.addWidget(self._process_btn)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setValue(0)
        layout.addWidget(self._progress_bar)

        # Status label
        self._status_label = QLabel("Status: Ready")
        layout.addWidget(self._status_label)

    def _pick_input(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Input Video", "", "Video Files (*.mp4)"
        )
        if path:
            self._video_path = path
            self._input_label.setText(path)
            self._check_ready()

    def _pick_output_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self._output_dir = directory
            self._output_label.setText(directory)
            self._check_ready()

    def _check_ready(self) -> None:
        self._process_btn.setEnabled(bool(self._video_path) and bool(self._output_dir))

    def _start_processing(self) -> None:
        self._process_btn.setEnabled(False)
        self._progress_bar.setValue(0)
        self._status_label.setText("Status: Starting...")

        self._worker = PipelineWorker(self._video_path, self._output_dir, self._cfg)
        self._worker.progress.connect(self._on_progress)
        self._worker.stage_changed.connect(self._on_stage)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, frame: int, total: int) -> None:
        if total > 0:
            self._progress_bar.setValue(int(frame / total * 100))

    def _on_stage(self, stage: str) -> None:
        self._status_label.setText(f"Status: {stage}")

    def _on_finished(self, path: str) -> None:
        self._process_btn.setEnabled(True)
        self._progress_bar.setValue(100)
        self._status_label.setText("Status: Done")
        QMessageBox.information(self, "Done", f"Output saved to:\n{path}")

    def _on_error(self, msg: str) -> None:
        self._process_btn.setEnabled(True)
        self._status_label.setText("Status: Error")
        QMessageBox.critical(self, "Error", msg)
