"""Tests for MatchSession mutations and undo stack.

Uses QCoreApplication (headless) — no display required.
"""

from __future__ import annotations

import sys

import pytest
# Must create QCoreApplication before any QObject/Signal usage
from PySide6.QtCore import QCoreApplication

_app = QCoreApplication.instance() or QCoreApplication(sys.argv)


from src.app.session import MatchSession, Rally


@pytest.fixture
def session():
    s = MatchSession()
    s.set_duration(3600.0)
    return s


def test_add_rally(session):
    rid = session.add_rally(100.0)
    rallies = session.rallies
    assert len(rallies) == 1
    assert rallies[0].id == rid
    assert rallies[0].start == pytest.approx(94.0)
    assert rallies[0].end == pytest.approx(106.0)


def test_delete_rally(session):
    rid = session.add_rally(100.0)
    assert len(session.rallies) == 1
    session.delete_rally(rid)
    assert len(session.rallies) == 0


def test_set_in_clamp(session):
    rid = session.add_rally(100.0)
    r = session.rally_by_id(rid)
    orig_end = r.end
    # Clamping: new start must not exceed end - 0.5
    session.set_in(rid, orig_end + 10.0)
    updated = session.rally_by_id(rid)
    assert updated.start <= updated.end - 0.5


def test_set_out_clamp(session):
    rid = session.add_rally(100.0)
    r = session.rally_by_id(rid)
    orig_start = r.start
    # Clamping: new end must not be less than start + 0.5
    session.set_out(rid, orig_start - 10.0)
    updated = session.rally_by_id(rid)
    assert updated.end >= updated.start + 0.5


def test_move_rally(session):
    rid = session.add_rally(100.0)
    r = session.rally_by_id(rid)
    orig_start, orig_end = r.start, r.end
    duration = orig_end - orig_start

    session.move_rally(rid, 50.0)
    moved = session.rally_by_id(rid)
    assert moved.start == pytest.approx(orig_start + 50.0, abs=0.1)
    assert moved.end - moved.start == pytest.approx(duration, abs=0.001)


def test_undo_add(session):
    session.add_rally(100.0)
    assert len(session.rallies) == 1
    session.undo()
    assert len(session.rallies) == 0


def test_undo_delete(session):
    rid = session.add_rally(100.0)
    session.delete_rally(rid)
    assert len(session.rallies) == 0
    session.undo()  # undo delete
    assert len(session.rallies) == 1


def test_undo_move(session):
    rid = session.add_rally(100.0)
    r_before = session.rally_by_id(rid)
    orig_start = r_before.start

    session.move_rally(rid, 50.0)
    session.undo()  # undo move

    r_after = session.rally_by_id(rid)
    assert r_after.start == pytest.approx(orig_start, abs=0.1)


def test_redo(session):
    rid = session.add_rally(100.0)
    r = session.rally_by_id(rid)
    orig_start = r.start

    session.move_rally(rid, 50.0)
    session.undo()
    session.redo()

    r_final = session.rally_by_id(rid)
    assert r_final.start == pytest.approx(orig_start + 50.0, abs=0.1)


def test_toggle_skip(session):
    rid = session.add_rally(100.0)
    assert not session.rally_by_id(rid).fp
    session.toggle_skip(rid)
    assert session.rally_by_id(rid).fp
    session.toggle_skip(rid)
    assert not session.rally_by_id(rid).fp


def test_undo_toggle(session):
    rid = session.add_rally(100.0)
    session.toggle_skip(rid)
    assert session.rally_by_id(rid).fp
    session.undo()
    assert not session.rally_by_id(rid).fp


def test_multiple_rallies_sorted(session):
    r2 = session.add_rally(200.0)
    r1 = session.add_rally(100.0)
    rallies = session.rallies
    # Should be sorted by start time
    assert rallies[0].start < rallies[1].start


def test_set_in_normal(session):
    rid = session.add_rally(100.0)
    r = session.rally_by_id(rid)
    new_start = r.start + 2.0
    session.set_in(rid, new_start)
    assert session.rally_by_id(rid).start == pytest.approx(new_start, abs=0.001)


def test_set_out_normal(session):
    rid = session.add_rally(100.0)
    r = session.rally_by_id(rid)
    new_end = r.end + 3.0
    session.set_out(rid, new_end)
    assert session.rally_by_id(rid).end == pytest.approx(new_end, abs=0.001)
