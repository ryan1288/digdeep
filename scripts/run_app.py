"""Entry point for the DigDeep Rally Extractor desktop app."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from omegaconf import OmegaConf
from PySide6.QtWidgets import QApplication

from src.app.main_window import MainWindow


def main() -> None:
    cfg = OmegaConf.load(
        os.path.join(os.path.dirname(__file__), "..", "configs", "app", "app.yaml")
    )
    app = QApplication(sys.argv)
    window = MainWindow(cfg)
    window.setWindowTitle(cfg.title)
    window.resize(cfg.window_width, cfg.window_height)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
