"""Main application window — shell with sidebar + QStackedWidget."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from omegaconf import DictConfig
from PySide6.QtCore import Qt, Slot
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QStackedWidget, QWidget

from src.app.session import MatchSession
from src.app.widgets.sidebar import Sidebar

# View indices (must match _stack insertion order)
IDX_LIBRARY = 0
IDX_UPLOAD = 1
IDX_PROCESSING = 2
IDX_EDITOR = 3
IDX_STATS = 4
IDX_EXPORT = 5
IDX_SETTINGS = 6

_VIEW_TO_IDX = {
    "library": IDX_LIBRARY,
    "upload": IDX_UPLOAD,
    "processing": IDX_PROCESSING,
    "editor": IDX_EDITOR,
    "stats": IDX_STATS,
    "export": IDX_EXPORT,
    "settings": IDX_SETTINGS,
}


class MainWindow(QMainWindow):
    """Primary application window.

    Args:
        cfg: Hydra DictConfig loaded from configs/app/app.yaml.
    """

    def __init__(self, cfg: DictConfig) -> None:
        super().__init__()
        self._cfg = cfg
        self._source_video_path: str = ""
        self._processed_output_path: str = ""
        self._worker = None

        # Central state
        self._session = MatchSession()
        self._media_player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._media_player.setAudioOutput(self._audio_output)

        self.setMinimumSize(
            cfg.get("window_min_width", 1100),
            cfg.get("window_min_height", 700),
        )

        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._sidebar = Sidebar()
        self._sidebar.navigate.connect(self._on_navigate)
        root.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        root.addWidget(self._stack, stretch=1)

        # Import views lazily to keep startup fast
        from src.app.views.editor_view import EditorView
        from src.app.views.export_view import ExportView
        from src.app.views.library_view import LibraryView
        from src.app.views.processing_view import ProcessingView
        from src.app.views.settings_view import SettingsView
        from src.app.views.stats_view import StatsView
        from src.app.views.upload_view import UploadView

        self._library_view = LibraryView()
        self._library_view.new_match.connect(self._go_upload)
        self._library_view.open_project.connect(self._on_open_project)
        self._stack.addWidget(self._library_view)  # 0

        self._upload_view = UploadView()
        self._upload_view.process_requested.connect(self._start_processing)
        self._upload_view.cancelled.connect(lambda: self._go("library"))
        self._stack.addWidget(self._upload_view)  # 1

        self._processing_view = ProcessingView()
        self._processing_view.processing_done.connect(self._on_processing_finished)
        self._processing_view.cancelled.connect(lambda: self._go("library"))
        self._stack.addWidget(self._processing_view)  # 2

        self._editor_view = EditorView(self._session, self._media_player)
        self._editor_view.export_requested.connect(lambda: self._go("export"))
        self._stack.addWidget(self._editor_view)  # 3

        self._stats_view = StatsView()
        self._stack.addWidget(self._stats_view)  # 4

        self._export_view = ExportView(self._session)
        self._stack.addWidget(self._export_view)  # 5

        self._settings_view = SettingsView(self._cfg)
        self._stack.addWidget(self._settings_view)  # 6

        self._stack.setCurrentIndex(IDX_LIBRARY)

    @Slot(str)
    def _on_navigate(self, view: str) -> None:
        self._go(view)

    def _go(self, view: str) -> None:
        idx = _VIEW_TO_IDX.get(view)
        if idx is None:
            return
        self._stack.setCurrentIndex(idx)
        self._sidebar.set_view(view)

    def _go_upload(self) -> None:
        self._go("upload")

    @Slot(str)
    def _start_processing(self, video_path: str) -> None:
        from src.app.analytics_worker import AnalyticsPipelineWorker

        self._source_video_path = video_path
        output_dir = str(Path(video_path).parent)

        self._worker = AnalyticsPipelineWorker(video_path, output_dir, self._cfg)
        self._processing_view.set_worker(self._worker)
        self._worker.start()

        self._go("processing")

    @Slot(str)
    def _on_processing_finished(self, output_path: str) -> None:
        self._processed_output_path = output_path

        # Load analytics JSON sidecar
        sidecar = output_path.replace(".mp4", "_analytics.json")
        if Path(sidecar).exists():
            self._session.load_from_json(sidecar)
        else:
            # Fallback: build minimal session from output path metadata
            pass

        # Wire media player to processed output
        from PySide6.QtCore import QUrl

        self._media_player.setSource(QUrl.fromLocalFile(output_path))

        # Update export view context
        self._export_view.set_export_context(
            self._source_video_path,
            output_path,
        )

        # Save to library
        self._library_view.add_project_from_session(
            self._session,
            output_path,
            self._source_video_path,
        )

        self._sidebar.set_project_active(True)
        self._go("editor")

    @Slot(dict)
    def _on_open_project(self, project: dict) -> None:
        sidecar = project.get("analytics_path", "")
        output_path = project.get("output_path", "")

        if sidecar and Path(sidecar).exists():
            self._session.load_from_json(sidecar)

        if output_path and Path(output_path).exists():
            from PySide6.QtCore import QUrl

            self._processed_output_path = output_path
            self._media_player.setSource(QUrl.fromLocalFile(output_path))
            self._export_view.set_export_context(
                project.get("source_path", ""), output_path
            )

        self._sidebar.set_project_active(True)
        self._go("editor")
