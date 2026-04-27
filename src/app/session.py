"""MatchSession — central state model with QUndoStack for rally editing."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QUndoCommand, QUndoStack


@dataclass
class Rally:
    """A single detected rally segment."""

    id: str
    start: float  # seconds
    end: float  # seconds
    fp: bool = False  # false-positive / "skip" flag

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


# ── Undo commands ──────────────────────────────────────────────────────


class _AddRallyCmd(QUndoCommand):
    def __init__(self, session: "MatchSession", rally: Rally) -> None:
        super().__init__(f"Add rally {rally.id[:8]}")
        self._session = session
        self._rally = rally

    def redo(self) -> None:
        self._session._rallies.append(self._rally)
        self._session._rallies.sort(key=lambda r: r.start)
        self._session._emit_rallies()

    def undo(self) -> None:
        self._session._rallies = [
            r for r in self._session._rallies if r.id != self._rally.id
        ]
        if self._session._selected_id == self._rally.id:
            self._session._selected_id = ""
        self._session._emit_rallies()


class _DeleteRallyCmd(QUndoCommand):
    def __init__(self, session: "MatchSession", rally_id: str) -> None:
        super().__init__(f"Delete rally {rally_id[:8]}")
        self._session = session
        self._rally_id = rally_id
        self._snapshot: Optional[Rally] = None

    def redo(self) -> None:
        for r in self._session._rallies:
            if r.id == self._rally_id:
                self._snapshot = Rally(r.id, r.start, r.end, r.fp)
                break
        self._session._rallies = [
            r for r in self._session._rallies if r.id != self._rally_id
        ]
        if self._session._selected_id == self._rally_id:
            self._session._selected_id = ""
        self._session._emit_rallies()

    def undo(self) -> None:
        if self._snapshot:
            self._session._rallies.append(self._snapshot)
            self._session._rallies.sort(key=lambda r: r.start)
        self._session._emit_rallies()


class _SetInCmd(QUndoCommand):
    def __init__(
        self, session: "MatchSession", rally_id: str, new_start: float
    ) -> None:
        super().__init__("Set in-point")
        self._session = session
        self._rally_id = rally_id
        self._new_start = new_start
        self._old_start: Optional[float] = None

    def redo(self) -> None:
        for r in self._session._rallies:
            if r.id == self._rally_id:
                self._old_start = r.start
                r.start = max(0.0, min(r.end - 0.5, self._new_start))
                break
        self._session._emit_rallies()

    def undo(self) -> None:
        if self._old_start is not None:
            for r in self._session._rallies:
                if r.id == self._rally_id:
                    r.start = self._old_start
                    break
        self._session._emit_rallies()


class _SetOutCmd(QUndoCommand):
    def __init__(self, session: "MatchSession", rally_id: str, new_end: float) -> None:
        super().__init__("Set out-point")
        self._session = session
        self._rally_id = rally_id
        self._new_end = new_end
        self._old_end: Optional[float] = None

    def redo(self) -> None:
        for r in self._session._rallies:
            if r.id == self._rally_id:
                self._old_end = r.end
                r.end = max(r.start + 0.5, min(self._session._duration, self._new_end))
                break
        self._session._emit_rallies()

    def undo(self) -> None:
        if self._old_end is not None:
            for r in self._session._rallies:
                if r.id == self._rally_id:
                    r.end = self._old_end
                    break
        self._session._emit_rallies()


class _MoveRallyCmd(QUndoCommand):
    def __init__(self, session: "MatchSession", rally_id: str, dt: float) -> None:
        super().__init__("Move rally")
        self._session = session
        self._rally_id = rally_id
        self._dt = dt

    def redo(self) -> None:
        dur = self._session._duration
        for r in self._session._rallies:
            if r.id == self._rally_id:
                length = r.end - r.start
                new_start = max(0.0, min(dur - length, r.start + self._dt))
                r.start = new_start
                r.end = new_start + length
                break
        self._session._emit_rallies()

    def undo(self) -> None:
        dur = self._session._duration
        for r in self._session._rallies:
            if r.id == self._rally_id:
                length = r.end - r.start
                new_start = max(0.0, min(dur - length, r.start - self._dt))
                r.start = new_start
                r.end = new_start + length
                break
        self._session._emit_rallies()


class _ToggleSkipCmd(QUndoCommand):
    def __init__(self, session: "MatchSession", rally_id: str) -> None:
        super().__init__("Toggle skip")
        self._session = session
        self._rally_id = rally_id

    def redo(self) -> None:
        for r in self._session._rallies:
            if r.id == self._rally_id:
                r.fp = not r.fp
                break
        self._session._emit_rallies()

    def undo(self) -> None:
        self.redo()  # toggle is its own inverse


# ── MatchSession ───────────────────────────────────────────────────────


class MatchSession(QObject):
    """Central state model for a match editing session.

    All mutations go through QUndoCommand so undo/redo works for every op.
    Non-command setters (_raw_*) are used by the media player / timeline
    scrub to update playhead without polluting the undo stack.
    """

    rallies_changed = Signal()
    rally_selection_changed = Signal(str)
    playhead_changed = Signal(float)
    play_state_changed = Signal(bool)
    can_undo_changed = Signal(bool)
    can_redo_changed = Signal(bool)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._rallies: List[Rally] = []
        self._selected_id: str = ""
        self._playhead: float = 0.0
        self._playing: bool = False
        self._duration: float = 0.0

        self._stack = QUndoStack(self)
        self._stack.canUndoChanged.connect(self.can_undo_changed)
        self._stack.canRedoChanged.connect(self.can_redo_changed)

    # ── Properties ──────────────────────────────────────────────────

    @property
    def rallies(self) -> List[Rally]:
        return list(self._rallies)

    @property
    def selected_id(self) -> str:
        return self._selected_id

    @property
    def playhead(self) -> float:
        return self._playhead

    @property
    def playing(self) -> bool:
        return self._playing

    @property
    def duration(self) -> float:
        return self._duration

    def set_duration(self, seconds: float) -> None:
        self._duration = max(0.0, seconds)

    # ── Mutation methods (push undo commands) ─────────────────────

    def add_rally(self, t: float) -> str:
        dur = 12.0
        r = Rally(
            id=str(uuid.uuid4()),
            start=max(0.0, t - dur / 2),
            end=min(self._duration, t + dur / 2),
        )
        self._stack.push(_AddRallyCmd(self, r))
        return r.id

    def delete_rally(self, rally_id: str) -> None:
        self._stack.push(_DeleteRallyCmd(self, rally_id))

    def set_in(self, rally_id: str, t: float) -> None:
        self._stack.push(_SetInCmd(self, rally_id, t))

    def set_out(self, rally_id: str, t: float) -> None:
        self._stack.push(_SetOutCmd(self, rally_id, t))

    def move_rally(self, rally_id: str, dt: float) -> None:
        self._stack.push(_MoveRallyCmd(self, rally_id, dt))

    def toggle_skip(self, rally_id: str) -> None:
        self._stack.push(_ToggleSkipCmd(self, rally_id))

    def undo(self) -> None:
        self._stack.undo()

    def redo(self) -> None:
        self._stack.redo()

    # ── Non-command setters ────────────────────────────────────────

    def _raw_set_playhead(self, t: float) -> None:
        clamped = max(0.0, min(self._duration, t))
        if abs(clamped - self._playhead) > 0.001:
            self._playhead = clamped
            self.playhead_changed.emit(clamped)

    def _raw_set_selected(self, rally_id: str) -> None:
        if rally_id != self._selected_id:
            self._selected_id = rally_id
            self.rally_selection_changed.emit(rally_id)

    def _raw_set_playing(self, playing: bool) -> None:
        if playing != self._playing:
            self._playing = playing
            self.play_state_changed.emit(playing)

    # ── Persistence ───────────────────────────────────────────────

    def load_from_json(self, path: str) -> None:
        """Load rallies from an analytics JSON sidecar."""
        data = json.loads(Path(path).read_text())
        rallies_data = data.get("rallies", [])
        self._stack.clear()
        self._rallies = []
        for entry in rallies_data:
            r = Rally(
                id=str(uuid.uuid4()),
                start=float(entry.get("start_sec", 0)),
                end=float(entry.get("end_sec", 0)),
            )
            if r.end > r.start:
                self._rallies.append(r)
        self._rallies.sort(key=lambda r: r.start)
        self._selected_id = self._rallies[0].id if self._rallies else ""
        self._playhead = self._rallies[0].start if self._rallies else 0.0
        self._emit_rallies()

    def load_from_list(self, rallies_data: list[dict]) -> None:
        """Load from a list of {start_sec, end_sec} dicts."""
        self._stack.clear()
        self._rallies = []
        for entry in rallies_data:
            r = Rally(
                id=str(uuid.uuid4()),
                start=float(entry.get("start_sec", 0)),
                end=float(entry.get("end_sec", 0)),
            )
            if r.end > r.start:
                self._rallies.append(r)
        self._rallies.sort(key=lambda r: r.start)
        self._selected_id = self._rallies[0].id if self._rallies else ""
        self._playhead = self._rallies[0].start if self._rallies else 0.0
        self._emit_rallies()

    def clear(self) -> None:
        self._stack.clear()
        self._rallies = []
        self._selected_id = ""
        self._playhead = 0.0
        self._duration = 0.0
        self._emit_rallies()

    # ── Internal helpers ──────────────────────────────────────────

    def _emit_rallies(self) -> None:
        self.rallies_changed.emit()
        # Notify undo/redo state
        self.can_undo_changed.emit(self._stack.canUndo())
        self.can_redo_changed.emit(self._stack.canRedo())

    def rally_by_id(self, rally_id: str) -> Optional[Rally]:
        for r in self._rallies:
            if r.id == rally_id:
                return r
        return None

    def rally_at_time(self, t: float) -> Optional[Rally]:
        for r in self._rallies:
            if r.start <= t <= r.end:
                return r
        return None
