"""SettingsView — model management, performance, and about."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QSizePolicy,
                               QVBoxLayout, QWidget)

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

_MODELS = [
    {
        "name": "Ball Detector",
        "desc": "VballNetFastV1 — heatmap regression, ONNX",
        "hf_repo": "digdeep/vballnet-fast-v1",
        "local_name": "VballNetFastV1_seq9_grayscale_233_h288_w512.onnx",
    },
    {
        "name": "Player Detector",
        "desc": "RF-DETR Base — DINOv2 backbone, ONNX",
        "hf_repo": "digdeep/rf-detr-base",
        "local_name": "rf_detr_base.onnx",
    },
    {
        "name": "Action Classifier",
        "desc": "VideoMAE-S fine-tuned — 6 action classes",
        "hf_repo": "digdeep/videomae-small-actions",
        "local_name": "videomae_small_actions.onnx",
    },
]


class SettingsView(QWidget):
    """App settings: model weights, inference performance, about."""

    def __init__(self, cfg=None, parent=None) -> None:
        super().__init__(parent)
        self._cfg = cfg
        self.setStyleSheet(f"background: {BG};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = ScreenHeader("Settings", "Model management and preferences")
        layout.addWidget(header)

        content = QWidget()
        content.setStyleSheet(f"background: {BG};")
        inner = QVBoxLayout(content)
        inner.setContentsMargins(24, 24, 24, 24)
        inner.setSpacing(20)

        # Models card
        models_card = _Card("AI Models")
        models_layout = QVBoxLayout(models_card)
        models_layout.setContentsMargins(0, 0, 0, 0)
        models_layout.setSpacing(0)

        self._model_rows: list[_ModelRow] = []
        for i, model in enumerate(_MODELS):
            row = _ModelRow(model, cfg)
            if i < len(_MODELS) - 1:
                row.setStyleSheet(
                    row.styleSheet() + f" border-bottom: 1px solid {BORDER};"
                )
            models_layout.addWidget(row)
            self._model_rows.append(row)

        check_btn = QPushButton("Check for Updates")
        check_btn.setFixedHeight(34)
        check_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: 1px solid {BORDER_HI};
                border-radius: 6px; padding: 0 14px;
                color: {TEXT}; font-size: 11px; margin: 12px;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,10); }}
        """)
        check_btn.clicked.connect(self._check_all_models)
        models_layout.addWidget(check_btn, alignment=Qt.AlignLeft)
        inner.addWidget(models_card)

        # Performance card
        perf_card = _Card("Performance")
        perf_layout = QVBoxLayout(perf_card)
        perf_layout.setContentsMargins(16, 14, 16, 14)
        perf_layout.setSpacing(8)

        provider_row = QHBoxLayout()
        prov_lbl = QLabel("Inference provider")
        prov_lbl.setStyleSheet(
            f"font-size: 12px; color: {TEXT}; background: transparent;"
        )
        provider_row.addWidget(prov_lbl)
        prov_val = QLabel("ONNX Runtime (CPU)")
        prov_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        prov_val.setStyleSheet(
            f"font-family: 'JetBrains Mono'; font-size: 11px; color: {TEXT_DIM}; background: transparent;"
        )
        provider_row.addWidget(prov_val)
        perf_layout.addLayout(provider_row)

        threads_row = QHBoxLayout()
        threads_lbl = QLabel("Thread count")
        threads_lbl.setStyleSheet(
            f"font-size: 12px; color: {TEXT}; background: transparent;"
        )
        threads_row.addWidget(threads_lbl)
        import os

        cpu_count = os.cpu_count() or 4
        threads_val = QLabel(
            str(cfg.get("num_threads", cpu_count) if cfg else cpu_count)
        )
        threads_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        threads_val.setStyleSheet(
            f"font-family: 'JetBrains Mono'; font-size: 11px; color: {TEXT_DIM}; background: transparent;"
        )
        threads_row.addWidget(threads_val)
        perf_layout.addLayout(threads_row)

        inner.addWidget(perf_card)

        # About card
        about_card = _Card("About")
        about_layout = QVBoxLayout(about_card)
        about_layout.setContentsMargins(16, 14, 16, 14)
        about_layout.setSpacing(6)

        for key, val in [
            ("App", "DigDeep"),
            ("Version", "0.1.0-alpha"),
            ("License", "Apache 2.0"),
            ("Source", "github.com/digdeep"),
        ]:
            row = QHBoxLayout()
            k = QLabel(key)
            k.setStyleSheet(
                f"font-size: 12px; color: {TEXT_MUTE}; background: transparent;"
            )
            v = QLabel(val)
            v.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            v.setStyleSheet(f"font-size: 12px; color: {TEXT}; background: transparent;")
            row.addWidget(k)
            row.addWidget(v)
            about_layout.addLayout(row)

        inner.addWidget(about_card)
        inner.addStretch()

        layout.addWidget(content, stretch=1)

    def _check_all_models(self) -> None:
        for row in self._model_rows:
            row.start_check()


class _Card(QWidget):
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

        header_bar = QWidget()
        header_bar.setStyleSheet(
            f"background: transparent; border-bottom: 1px solid {BORDER};"
        )
        hb_layout = QHBoxLayout(header_bar)
        hb_layout.setContentsMargins(16, 12, 16, 12)
        lbl = QLabel(title)
        lbl.setStyleSheet(
            f"font-size: 12px; font-weight: 600; color: {TEXT}; background: transparent;"
        )
        hb_layout.addWidget(lbl)
        layout.addWidget(header_bar)


class _ModelRow(QWidget):
    def __init__(self, model: dict, cfg=None, parent=None) -> None:
        super().__init__(parent)
        self._model = model
        self._cfg = cfg
        self._worker: "_ModelCheckWorker | None" = None
        self.setStyleSheet("background: transparent;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        name_lbl = QLabel(model["name"])
        name_lbl.setStyleSheet(
            f"font-size: 12px; font-weight: 500; color: {TEXT}; background: transparent;"
        )
        text_col.addWidget(name_lbl)
        desc_lbl = QLabel(model["desc"])
        desc_lbl.setStyleSheet(
            f"font-size: 10px; color: {TEXT_MUTE}; background: transparent;"
        )
        text_col.addWidget(desc_lbl)
        layout.addLayout(text_col, stretch=1)

        self._status_lbl = QLabel("Checking…")
        self._status_lbl.setStyleSheet(
            f"font-family: 'JetBrains Mono'; font-size: 10px; color: {TEXT_MUTE}; background: transparent;"
        )
        self._status_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self._status_lbl)

        self._dl_btn = QPushButton("Download")
        self._dl_btn.setFixedHeight(28)
        self._dl_btn.hide()
        self._dl_btn.setStyleSheet(f"""
            QPushButton {{
                background: {CORAL}; color: white; border: none;
                border-radius: 5px; padding: 0 10px; font-size: 11px;
            }}
            QPushButton:hover {{ background: #f09870; }}
        """)
        self._dl_btn.clicked.connect(self.start_check)
        layout.addWidget(self._dl_btn)

        self.start_check()

    def start_check(self) -> None:
        self._status_lbl.setText("Checking…")
        self._status_lbl.setStyleSheet(
            f"font-family: 'JetBrains Mono'; font-size: 10px; color: {TEXT_MUTE}; background: transparent;"
        )
        self._dl_btn.hide()

        # Check local path first
        cfg_models_dir = None
        if self._cfg:
            try:
                cfg_models_dir = self._cfg.get("models_dir", None)
            except Exception:
                pass

        model_dirs = [
            Path.home() / ".cache" / "digdeep" / "models",
        ]
        if cfg_models_dir:
            model_dirs.insert(0, Path(cfg_models_dir))

        for d in model_dirs:
            candidate = d / self._model["local_name"]
            if candidate.exists():
                self._set_installed()
                return

        # Not found locally — show download button
        self._set_not_installed()

    def _set_installed(self) -> None:
        self._status_lbl.setText("● Installed")
        self._status_lbl.setStyleSheet(
            f"font-family: 'JetBrains Mono'; font-size: 10px; color: {GREEN}; background: transparent;"
        )
        self._dl_btn.hide()

    def _set_not_installed(self) -> None:
        self._status_lbl.setText("Not installed")
        self._status_lbl.setStyleSheet(
            f"font-family: 'JetBrains Mono'; font-size: 10px; color: {TEXT_MUTE}; background: transparent;"
        )
        self._dl_btn.show()


class _ModelCheckWorker(QThread):
    """Downloads a model from HuggingFace Hub."""

    done = Signal(str)  # local path
    error = Signal(str)

    def __init__(self, repo_id: str, filename: str) -> None:
        super().__init__()
        self._repo_id = repo_id
        self._filename = filename

    def run(self) -> None:
        try:
            from huggingface_hub import hf_hub_download

            path = hf_hub_download(repo_id=self._repo_id, filename=self._filename)
            self.done.emit(path)
        except Exception as e:
            self.error.emit(str(e))
