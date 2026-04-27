"""StatsView — per-player analytics (Coming Soon overlay)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout,
                               QWidget)

from src.app.widgets.cards import ScreenHeader
from src.app.widgets.court_heatmap import CourtHeatmap

BG = "#1d1f24"
PANEL = "#272a30"
PANEL_LO = "#22252a"
BORDER = "#3f434b"
TEXT = "#f1f2f4"
TEXT_DIM = "#a8acb3"
TEXT_MUTE = "#74797f"
CORAL = "#ec8a5e"
GREEN = "#5cd0a5"


class StatsView(QWidget):
    """Player analytics screen with 'Coming Soon' overlay."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"background: {BG};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = ScreenHeader(
            "Player Analytics",
            "Per-player action counts and court positioning",
        )
        layout.addWidget(header)

        # Content area (blurred/dimmed in prod; here just a coming soon state)
        content = QWidget()
        content.setStyleSheet(f"background: {BG};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(20)

        # Two-column layout: heatmap left, table right
        columns = QHBoxLayout()
        columns.setSpacing(20)

        # Heatmap card
        heatmap_card = _Card("Ball Contact Heatmap")
        heatmap_layout = QVBoxLayout(heatmap_card)
        heatmap_layout.setContentsMargins(16, 16, 16, 16)
        self._heatmap = CourtHeatmap()
        self._heatmap.setMinimumHeight(220)
        # Seed with placeholder data
        self._heatmap.set_points(
            [
                (0.25, 0.25),
                (0.5, 0.15),
                (0.75, 0.3),
                (0.3, 0.6),
                (0.7, 0.7),
                (0.5, 0.85),
            ]
        )
        heatmap_layout.addWidget(self._heatmap)
        columns.addWidget(heatmap_card, stretch=1)

        # Stats table card (placeholder)
        table_card = _Card("Action Counts by Player")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(16, 16, 16, 16)
        table_layout.setSpacing(0)

        header_row = _TableRow(
            ["Player", "Serve", "Receive", "Set", "Attack", "Block"],
            header=True,
        )
        table_layout.addWidget(header_row)

        placeholder_data = [
            ["Track #1", "4", "8", "12", "6", "3"],
            ["Track #2", "5", "7", "9", "11", "4"],
            ["Track #3", "3", "9", "7", "5", "6"],
            ["Track #4", "6", "6", "4", "8", "2"],
        ]
        for row_data in placeholder_data:
            table_layout.addWidget(_TableRow(row_data))

        table_layout.addStretch()
        columns.addWidget(table_card, stretch=2)

        content_layout.addLayout(columns)
        content_layout.addStretch()
        layout.addWidget(content, stretch=1)

        # Coming Soon overlay
        overlay = _ComingSoonOverlay(content)
        overlay.setGeometry(content.rect())
        content.resizeEvent = lambda e: overlay.setGeometry(content.rect())


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

        title_bar = QWidget()
        title_bar.setStyleSheet(f"""
            background: transparent;
            border-bottom: 1px solid {BORDER};
            border-radius: 0;
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(16, 12, 16, 12)
        lbl = QLabel(title)
        lbl.setStyleSheet(
            f"font-size: 12px; font-weight: 600; color: {TEXT}; background: transparent;"
        )
        title_layout.addWidget(lbl)
        layout.addWidget(title_bar)


class _TableRow(QWidget):
    def __init__(self, cells: list, header: bool = False, parent=None) -> None:
        super().__init__(parent)
        color = TEXT_DIM if header else TEXT
        bg = PANEL_LO if header else "transparent"
        self.setStyleSheet(f"background: {bg}; border-bottom: 1px solid {BORDER};")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(0)
        for i, cell in enumerate(cells):
            lbl = QLabel(cell)
            lbl.setStyleSheet(
                f"font-size: 11px; color: {color}; background: transparent; "
                f"font-weight: {'600' if header else '400'};"
            )
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            layout.addWidget(lbl, stretch=(3 if i == 0 else 1))


class _ComingSoonOverlay(QWidget):
    """Semi-transparent frosted overlay with 'Coming Soon' pill."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setStyleSheet("background: rgba(29, 31, 36, 0.75);")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        pill = QLabel("Coming Soon")
        pill.setAlignment(Qt.AlignCenter)
        pill.setStyleSheet(f"""
            background: {PANEL};
            border: 1px solid {CORAL};
            border-radius: 999px;
            color: {CORAL};
            font-size: 13px;
            font-weight: 600;
            padding: 8px 20px;
            letter-spacing: 1px;
        """)
        layout.addWidget(pill, alignment=Qt.AlignCenter)

        desc = QLabel(
            "Player analytics will be available after\nPhase 2 model training completes."
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet(
            f"font-size: 12px; color: {TEXT_DIM}; background: transparent;"
        )
        layout.addWidget(desc, alignment=Qt.AlignCenter)
