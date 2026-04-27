"""Timeline widget — custom QWidget with minimap, ruler, track lane, and playhead.

Module-level pure functions are importable without any Qt event loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (QBrush, QColor, QFont, QFontMetrics,
                           QLinearGradient, QPainter, QPainterPath, QPen)
from PySide6.QtWidgets import QSizePolicy, QWidget

from src.app.widgets.rally_block import paint_rally_block

# ── Module-level pure functions ────────────────────────────────────────


def x_to_t(x: float, scroll_x: float, total_w: float, duration: float) -> float:
    """Convert a pixel x position to a time in seconds.

    Args:
        x: Pixel position relative to the left edge of the timeline widget.
        scroll_x: Current horizontal scroll offset in pixels.
        total_w: Total timeline width at current zoom (widget_width * zoom).
        duration: Video duration in seconds.

    Returns:
        Time in seconds, clamped to [0, duration].
    """
    if total_w <= 0 or duration <= 0:
        return 0.0
    return max(0.0, min(duration, (x + scroll_x) / total_w * duration))


def t_to_x(t: float, scroll_x: float, total_w: float, duration: float) -> float:
    """Convert a time in seconds to a pixel x position.

    Args:
        t: Time in seconds.
        scroll_x: Current horizontal scroll offset in pixels.
        total_w: Total timeline width at current zoom (widget_width * zoom).
        duration: Video duration in seconds.

    Returns:
        Pixel x position relative to the left edge of the timeline widget.
    """
    if duration <= 0:
        return 0.0
    return (t / duration) * total_w - scroll_x


def choose_interval(zoom: float, duration: float, width: float) -> float:
    """Choose tick interval in seconds so ~14 ticks are visible.

    Args:
        zoom: Current zoom level (1 = fit-to-width).
        duration: Video duration in seconds.
        width: Widget width in pixels.

    Returns:
        Tick spacing in seconds, chosen from [10, 30, 60, 120, 300, 600].
    """
    if duration <= 0 or width <= 0:
        return 60.0
    px_per_sec = (width * zoom) / duration
    for c in [10, 30, 60, 120, 300, 600]:
        if c * px_per_sec >= width / 14:
            return float(c)
    return 600.0


def fmt_time(s: float) -> str:
    """Format seconds as M:SS or H:MM:SS."""
    if s < 0:
        s = 0
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = int(s % 60)
    if h > 0:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"


# ── Height constants ───────────────────────────────────────────────────

MINI_H = 16  # minimap strip
RULER_H = 22  # ruler row
BLOCK_PAD = 16  # padding above and below the block lane in track area
BLOCK_H = 60  # rally block height
TRACK_H = BLOCK_PAD + BLOCK_H + BLOCK_PAD  # total track area height
TOTAL_H = MINI_H + RULER_H + TRACK_H  # 132 px

# ── Drag state ─────────────────────────────────────────────────────────


@dataclass
class _DragState:
    kind: str  # "scrub" | "start" | "end" | "block"
    rally_id: str = ""
    x0: float = 0.0
    orig_start: float = 0.0
    orig_end: float = 0.0
    scroll_x0: float = 0.0
    committed: bool = False  # True once undo cmd pushed on release


# ── Design tokens ──────────────────────────────────────────────────────

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


class Timeline(QWidget):
    """Full-featured timeline with minimap, ruler, track lane, and playhead.

    Must be connected to a MatchSession via set_session().
    Pure functions x_to_t, t_to_x, choose_interval are available at module
    level so unit tests can import them without a Qt event loop.
    """

    scrub_requested = Signal(float)  # seconds
    rally_drag_finished = Signal()  # emitted after each drag commit

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._session = None
        self._zoom: float = 1.0
        self._scroll_x: float = 0.0
        self._drag: Optional[_DragState] = None
        self._hover_id: str = ""

        # Live override for smooth drag display (no undo spam)
        self._live_start: Optional[float] = None
        self._live_end: Optional[float] = None
        self._live_id: str = ""

        self.setFixedHeight(TOTAL_H + 4)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(f"background: {PANEL};")

    def set_session(self, session) -> None:
        self._session = session
        session.rallies_changed.connect(self.update)
        session.playhead_changed.connect(self._on_playhead_changed)
        session.rally_selection_changed.connect(lambda _: self.update())

    def set_zoom(self, zoom: float) -> None:
        self._zoom = max(1.0, zoom)
        self._clamp_scroll()
        self.update()

    def _on_playhead_changed(self, t: float) -> None:
        if self._session is None:
            return
        # Auto-scroll to keep playhead visible
        w = self.width()
        total_w = w * self._zoom
        duration = self._session.duration
        if duration <= 0:
            return
        px = t_to_x(t, self._scroll_x, total_w, duration)
        if px < 80:
            self._scroll_x = max(0.0, self._scroll_x - 80)
            self._clamp_scroll()
        elif px > w - 80:
            self._scroll_x = min(total_w - w, self._scroll_x + 80)
            self._clamp_scroll()
        self.update()

    # ── paintEvent ─────────────────────────────────────────────────

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        session = self._session
        duration = session.duration if session else 0.0
        total_w = w * self._zoom
        scroll_x = self._scroll_x

        # ── Zone 1: Minimap ──────────────────────────────────────
        p.fillRect(0, 0, w, MINI_H, QColor(PANEL_LO))
        p.setPen(QPen(QColor(BORDER), 1))
        p.drawLine(0, MINI_H - 1, w, MINI_H - 1)

        if session and duration > 0:
            for rally in session.rallies:
                rx = int(rally.start / duration * w)
                rw = max(2, int((rally.end - rally.start) / duration * w))
                if rally.fp:
                    mc = QColor(TEXT_MUTE)
                    mc.setAlphaF(0.3)
                else:
                    mc = QColor(CORAL)
                    mc.setAlphaF(0.85)
                p.fillRect(rx, 2, rw, MINI_H - 4, mc)

            # Viewport rect when zoomed
            if self._zoom > 1.0:
                vp_x = int(scroll_x / total_w * w)
                vp_w = max(4, int(w / total_w * w))
                p.setPen(QPen(QColor(TEXT), 1))
                p.setBrush(QBrush(QColor(255, 255, 255, 15)))
                p.drawRect(vp_x, 0, vp_w, MINI_H)

            # Playhead in minimap
            ph = session.playhead
            ph_mx = int(ph / duration * w)
            p.setPen(QPen(QColor(TEXT), 1.5))
            p.drawLine(ph_mx, 0, ph_mx, MINI_H)

        # ── Zone 2: Ruler ────────────────────────────────────────
        ruler_y = MINI_H
        p.fillRect(0, ruler_y, w, RULER_H, QColor(PANEL_LO))
        p.setPen(QPen(QColor(BORDER), 1))
        p.drawLine(0, ruler_y + RULER_H - 1, w, ruler_y + RULER_H - 1)

        if duration > 0:
            interval = choose_interval(self._zoom, duration, w)
            tick_font = QFont("JetBrains Mono", 10)
            p.setFont(tick_font)
            p.setPen(QColor(TEXT_MUTE))

            s = 0.0
            while s <= duration:
                tx = t_to_x(s, scroll_x, total_w, duration)
                if -2 <= tx <= w + 2:
                    itx = int(tx)
                    p.setPen(QPen(QColor(BORDER), 1))
                    p.drawLine(itx, ruler_y, itx, ruler_y + RULER_H - 6)
                    p.setPen(QColor(TEXT_MUTE))
                    label = fmt_time(s)
                    p.drawText(itx + 4, ruler_y + RULER_H - 5, label)
                s += interval

        # ── Zone 3: Track lane ───────────────────────────────────
        track_y = ruler_y + RULER_H
        block_top = track_y + BLOCK_PAD
        p.fillRect(0, track_y, w, TRACK_H, QColor(BG))

        # Inner lane band
        p.fillRect(0, block_top, w, BLOCK_H, QColor(PANEL_LO))
        p.setPen(QPen(QColor(BORDER), 1))
        p.drawLine(0, block_top, w, block_top)
        p.drawLine(0, block_top + BLOCK_H, w, block_top + BLOCK_H)

        # Faint grid lines
        if duration > 0:
            interval = choose_interval(self._zoom, duration, w)
            s = 0.0
            while s <= duration:
                tx = t_to_x(s, scroll_x, total_w, duration)
                if 0 <= tx <= w:
                    grid_color = QColor(BORDER)
                    grid_color.setAlphaF(0.4)
                    p.setPen(QPen(grid_color, 1))
                    p.drawLine(int(tx), track_y, int(tx), h)
                s += interval

        # Rally blocks
        if session and duration > 0:
            rallies = session.rallies
            sel_id = session.selected_id
            for i, rally in enumerate(rallies):
                # Use live override during drag for this rally
                r_start = rally.start
                r_end = rally.end
                if self._live_id == rally.id and self._live_start is not None:
                    r_start = self._live_start
                    r_end = self._live_end

                bx = t_to_x(r_start, scroll_x, total_w, duration)
                bw = t_to_x(r_end, scroll_x, total_w, duration) - bx
                if bx + bw < -20 or bx > w + 20:
                    continue  # off-screen cull
                paint_rally_block(
                    p,
                    r_start,
                    r_end,
                    rally.fp,
                    bx,
                    max(8.0, bw),
                    block_top,
                    BLOCK_H,
                    selected=(rally.id == sel_id),
                    hovered=(rally.id == self._hover_id),
                    index=i + 1,
                )

        # ── Playhead (spans ruler + track) ───────────────────────
        if session and duration > 0:
            ph = session.playhead
            ph_x = t_to_x(ph, scroll_x, total_w, duration)
            if -4 <= ph_x <= w + 4:
                iph = int(ph_x)
                # Glow shadow
                glow = QPen(QColor(255, 255, 255, 50), 6)
                p.setPen(glow)
                p.drawLine(iph, ruler_y, iph, h)

                # White line
                p.setPen(QPen(QColor(TEXT), 2))
                p.drawLine(iph, ruler_y, iph, h)

                # Triangle handle
                tri = QPainterPath()
                tri.moveTo(iph - 7, ruler_y)
                tri.lineTo(iph + 7, ruler_y)
                tri.lineTo(iph, ruler_y + 12)
                tri.closeSubpath()
                p.setBrush(QBrush(QColor(TEXT)))
                p.setPen(Qt.NoPen)
                p.drawPath(tri)

        p.end()

    # ── Mouse events ───────────────────────────────────────────────

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.LeftButton:
            return
        if self._session is None:
            return

        x = event.position().x()
        y = event.position().y()
        w = self.width()
        total_w = w * self._zoom
        duration = self._session.duration
        scroll_x = self._scroll_x

        # Minimap click — jump to time
        if y < MINI_H:
            if duration > 0:
                t = x / w * duration
                self._session._raw_set_playhead(t)
            return

        # Ruler area — scrub
        ruler_y = MINI_H
        if ruler_y <= y < ruler_y + RULER_H:
            t = x_to_t(x, scroll_x, total_w, duration)
            self._session._raw_set_playhead(t)
            self._drag = _DragState("scrub", x0=x, scroll_x0=scroll_x)
            return

        # Track area — hit-test rally blocks
        block_top = MINI_H + RULER_H + BLOCK_PAD
        block_bot = block_top + BLOCK_H
        if block_top <= y <= block_bot and duration > 0:
            for rally in reversed(self._session.rallies):
                r_start = rally.start
                r_end = rally.end
                bx = t_to_x(r_start, scroll_x, total_w, duration)
                bw = t_to_x(r_end, scroll_x, total_w, duration) - bx
                bw = max(8.0, bw)
                if bx <= x <= bx + bw:
                    self._session._raw_set_selected(rally.id)
                    if x <= bx + 8:
                        self._drag = _DragState(
                            "start", rally.id, x, rally.start, rally.end, scroll_x
                        )
                    elif x >= bx + bw - 8:
                        self._drag = _DragState(
                            "end", rally.id, x, rally.start, rally.end, scroll_x
                        )
                    else:
                        self._drag = _DragState(
                            "block", rally.id, x, rally.start, rally.end, scroll_x
                        )
                    self._live_id = rally.id
                    self._live_start = rally.start
                    self._live_end = rally.end
                    return

        # Empty track area — scrub
        t = x_to_t(x, scroll_x, total_w, duration)
        self._session._raw_set_playhead(t)
        self._drag = _DragState("scrub", x0=x, scroll_x0=scroll_x)

    def mouseMoveEvent(self, event) -> None:
        if self._session is None:
            return
        x = event.position().x()
        y = event.position().y()
        w = self.width()
        total_w = w * self._zoom
        duration = self._session.duration
        scroll_x = self._scroll_x

        # Hover detection (no drag)
        if self._drag is None:
            block_top = MINI_H + RULER_H + BLOCK_PAD
            block_bot = block_top + BLOCK_H
            if block_top <= y <= block_bot and duration > 0:
                for rally in reversed(self._session.rallies):
                    bx = t_to_x(rally.start, scroll_x, total_w, duration)
                    bw = t_to_x(rally.end, scroll_x, total_w, duration) - bx
                    bw = max(8.0, bw)
                    if bx <= x <= bx + bw:
                        if rally.id != self._hover_id:
                            self._hover_id = rally.id
                            self.update()
                        return
            if self._hover_id:
                self._hover_id = ""
                self.update()
            return

        drag = self._drag
        dx = x - drag.x0
        dt = (dx / total_w) * duration if total_w > 0 else 0.0

        if drag.kind == "scrub":
            t = x_to_t(x, drag.scroll_x0, total_w, duration)
            self._session._raw_set_playhead(t)

        elif drag.kind == "start":
            new_start = max(0.0, min(drag.orig_end - 0.5, drag.orig_start + dt))
            self._live_start = new_start
            self._live_end = drag.orig_end
            self.update()

        elif drag.kind == "end":
            new_end = max(drag.orig_start + 0.5, min(duration, drag.orig_end + dt))
            self._live_start = drag.orig_start
            self._live_end = new_end
            self.update()

        elif drag.kind == "block":
            dur = drag.orig_end - drag.orig_start
            new_start = max(0.0, min(duration - dur, drag.orig_start + dt))
            self._live_start = new_start
            self._live_end = new_start + dur
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() != Qt.LeftButton:
            return
        if self._drag is None:
            return

        drag = self._drag
        session = self._session
        duration = session.duration if session else 0.0
        w = self.width()
        total_w = w * self._zoom

        if drag.kind in ("start", "end", "block") and session and duration > 0:
            x = event.position().x()
            dx = x - drag.x0
            dt = (dx / total_w) * duration if total_w > 0 else 0.0

            if drag.kind == "start":
                new_start = max(0.0, min(drag.orig_end - 0.5, drag.orig_start + dt))
                if abs(new_start - drag.orig_start) > 0.01:
                    session.set_in(drag.rally_id, new_start)
            elif drag.kind == "end":
                new_end = max(drag.orig_start + 0.5, min(duration, drag.orig_end + dt))
                if abs(new_end - drag.orig_end) > 0.01:
                    session.set_out(drag.rally_id, new_end)
            elif drag.kind == "block":
                dur = drag.orig_end - drag.orig_start
                new_start = max(0.0, min(duration - dur, drag.orig_start + dt))
                if abs(new_start - drag.orig_start) > 0.01:
                    session.move_rally(drag.rally_id, new_start - drag.orig_start)

        # Clear live override
        self._live_id = ""
        self._live_start = None
        self._live_end = None
        self._drag = None
        self.update()

    def wheelEvent(self, event) -> None:
        if self._zoom > 1.0:
            delta = event.angleDelta().x() or event.angleDelta().y()
            w = self.width()
            total_w = w * self._zoom
            self._scroll_x += delta * 0.5
            self._clamp_scroll()
            self.update()
        event.accept()

    # ── Helpers ────────────────────────────────────────────────────

    def _clamp_scroll(self) -> None:
        w = self.width()
        total_w = w * self._zoom
        max_scroll = max(0.0, total_w - w)
        self._scroll_x = max(0.0, min(max_scroll, self._scroll_x))
