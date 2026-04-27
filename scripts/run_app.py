"""Entry point for the DigDeep Rally Extractor desktop app."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from omegaconf import OmegaConf
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

from src.app.main_window import MainWindow


def _load_fonts(app_root: Path) -> None:
    fonts_dir = app_root / "assets" / "fonts"
    for ttf in sorted(fonts_dir.glob("*.ttf")):
        fid = QFontDatabase.addApplicationFont(str(ttf))
        if fid < 0:
            print(f"Warning: could not load font {ttf.name}", file=sys.stderr)


def _load_stylesheet(app_root: Path) -> str:
    qss_path = app_root / "src" / "app" / "style.qss"
    if qss_path.exists():
        return qss_path.read_text()
    return ""


def main() -> None:
    app = QApplication(sys.argv)

    app_root = Path(__file__).parent.parent
    _load_fonts(app_root)

    stylesheet = _load_stylesheet(app_root)
    if stylesheet:
        app.setStyleSheet(stylesheet)

    cfg = OmegaConf.load(app_root / "configs" / "app" / "app.yaml")

    window = MainWindow(cfg)
    window.setWindowTitle(cfg.title)
    window.resize(cfg.window_width, cfg.window_height)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
