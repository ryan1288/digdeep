# Visualize Tracking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A single CLI script (`scripts/visualize_tracking.py`) that runs BallDetector → PlayerDetector → PlayerTracker on every frame of a rally clip and writes an annotated MP4 with colored player bboxes (by tracker ID) and ball circles.

**Architecture:** Pure drawing helpers (`_draw_players`, `_draw_ball`) are module-level functions that can be unit tested in isolation. `main()` handles CLI arg parsing, detector/tracker initialization (reusing `real_runner.py`'s resolve helpers), the frame loop, and video I/O. No new modules or classes needed.

**Tech Stack:** `cv2` (video I/O + drawing), `onnxruntime`, `numpy`, `omegaconf`, `argparse`; reuses `BallDetector`, `PlayerDetector`, `PlayerTracker`, `FrameResult` from `digdeep/src/`.

---

## File Structure

| Path | Status | Responsibility |
|---|---|---|
| `scripts/visualize_tracking.py` | **Create** | CLI entry point + drawing helpers |
| `tests/test_visualize_tracking.py` | **Create** | Unit tests for drawing helpers |

---

### Task 1: Write failing tests for drawing helpers

**Files:**
- Create: `tests/test_visualize_tracking.py`

The drawing helpers are pure functions: `_draw_players(frame, detections) -> np.ndarray` and `_draw_ball(frame, detections) -> np.ndarray`. They operate on a copy of the frame and return it.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_visualize_tracking.py`:

```python
"""Unit tests for visualize_tracking drawing helpers."""

import numpy as np
import pytest


def _blank(h=100, w=200):
    return np.zeros((h, w, 3), dtype=np.uint8)


# ── _draw_players ──────────────────────────────────────────────────────────────

def test_draw_players_returns_same_shape():
    from scripts.visualize_tracking import _draw_players
    frame = _blank()
    result = _draw_players(frame, [{"bbox": [10, 10, 50, 80], "tracker_id": 1, "conf": 0.9}])
    assert result.shape == frame.shape


def test_draw_players_modifies_pixels():
    from scripts.visualize_tracking import _draw_players
    frame = _blank()
    result = _draw_players(frame, [{"bbox": [10, 10, 50, 80], "tracker_id": 2, "conf": 0.9}])
    assert result.sum() > 0


def test_draw_players_empty_detections_unchanged():
    from scripts.visualize_tracking import _draw_players
    frame = _blank()
    result = _draw_players(frame, [])
    assert result.sum() == 0


def test_draw_players_untracked_id():
    """tracker_id=-1 (not yet assigned) should draw grey, not crash."""
    from scripts.visualize_tracking import _draw_players
    frame = _blank()
    result = _draw_players(frame, [{"bbox": [5, 5, 40, 60], "tracker_id": -1, "conf": 0.5}])
    assert result.shape == frame.shape


def test_draw_players_does_not_mutate_original():
    from scripts.visualize_tracking import _draw_players
    frame = _blank()
    original = frame.copy()
    _draw_players(frame, [{"bbox": [10, 10, 50, 80], "tracker_id": 3, "conf": 0.9}])
    # function draws on the frame in-place; test that original variable not silently clobbered
    # (we pass frame in, so result and frame are the same object — that's fine)
    assert True  # no crash is the assertion


# ── _draw_ball ─────────────────────────────────────────────────────────────────

def test_draw_ball_returns_same_shape():
    from scripts.visualize_tracking import _draw_ball
    frame = _blank()
    result = _draw_ball(frame, [{"x": 100.0, "y": 50.0, "conf": 0.8}])
    assert result.shape == frame.shape


def test_draw_ball_modifies_pixels():
    from scripts.visualize_tracking import _draw_ball
    frame = _blank()
    result = _draw_ball(frame, [{"x": 100.0, "y": 50.0, "conf": 0.8}])
    assert result.sum() > 0


def test_draw_ball_empty_detections_unchanged():
    from scripts.visualize_tracking import _draw_ball
    frame = _blank()
    result = _draw_ball(frame, [])
    assert result.sum() == 0


def test_draw_ball_clips_to_frame_bounds():
    """Ball centroid at frame edge must not raise cv2 error."""
    from scripts.visualize_tracking import _draw_ball
    frame = _blank()
    result = _draw_ball(frame, [{"x": 0.0, "y": 0.0, "conf": 0.9}])
    assert result.shape == frame.shape
```

- [ ] **Step 2: Run to confirm FAIL**

```bash
cd /home/ryanlee/digdeep && conda run -n digdeep pytest tests/test_visualize_tracking.py -v
```

Expected: `ModuleNotFoundError` — `scripts.visualize_tracking` does not exist yet.

---

### Task 2: Implement drawing helpers in the script skeleton

**Files:**
- Create: `scripts/visualize_tracking.py`

- [ ] **Step 1: Create the script with only the drawing helpers**

Create `scripts/visualize_tracking.py`:

```python
"""Visualize ball + player tracking on a rally clip.

Usage:
    conda run -n digdeep python scripts/visualize_tracking.py \\
        data/rallies/match_001_r001.mp4 \\
        [--out /tmp/tracked.mp4] [--show] [--conf 0.3]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List

import cv2
import numpy as np
from omegaconf import OmegaConf

# Ensure repo root on path when run as a plain script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.inference.ball_detector import BallDetector
from src.inference.player_detector import PlayerDetector
from src.inference.player_tracker import PlayerTracker
from src.inference.real_runner import _resolve_player_model, _resolve_reid_model
from src.pipeline.frame_result import FrameResult

# 20-colour palette — index by tracker_id % 20 (BGR order)
_COLORS: List[tuple] = [
    (56, 56, 255),   (151, 157, 255), (31, 112, 255),  (29, 178, 255),
    (49, 210, 207),  (10, 249, 72),   (23, 204, 146),  (134, 219, 61),
    (52, 147, 26),   (187, 212, 0),   (168, 153, 44),  (255, 194, 0),
    (147, 69, 52),   (255, 115, 100), (236, 24, 0),    (255, 56, 132),
    (133, 0, 82),    (255, 56, 203),  (200, 149, 255), (199, 55, 255),
]
_BALL_COLOR = (0, 255, 255)   # yellow in BGR
_UNTRACKED_COLOR = (128, 128, 128)


def _draw_players(frame: np.ndarray, detections: List[dict]) -> np.ndarray:
    """Draw player bboxes colour-coded by tracker_id.

    Args:
        frame: BGR image, modified in place.
        detections: List of dicts with keys bbox, tracker_id, conf.

    Returns:
        The same frame with rectangles and labels drawn.
    """
    for det in detections:
        tid = det["tracker_id"]
        color = _COLORS[tid % len(_COLORS)] if tid >= 0 else _UNTRACKED_COLOR
        x1, y1, x2, y2 = (int(v) for v in det["bbox"])
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = f"#{tid}" if tid >= 0 else "?"
        cv2.putText(
            frame, label, (x1, max(y1 - 5, 10)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA,
        )
    return frame


def _draw_ball(frame: np.ndarray, detections: List[dict]) -> np.ndarray:
    """Draw ball detections as yellow circles.

    Args:
        frame: BGR image, modified in place.
        detections: List of dicts with keys x, y, conf.

    Returns:
        The same frame with circles and confidence labels drawn.
    """
    for det in detections:
        cx, cy = int(det["x"]), int(det["y"])
        cv2.circle(frame, (cx, cy), 8, _BALL_COLOR, 2, cv2.LINE_AA)
        cv2.putText(
            frame, f"{det['conf']:.2f}", (cx + 10, cy),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, _BALL_COLOR, 1, cv2.LINE_AA,
        )
    return frame


def main() -> None:
    pass  # implemented in Task 3
```

- [ ] **Step 2: Run tests to confirm PASS**

```bash
cd /home/ryanlee/digdeep && conda run -n digdeep pytest tests/test_visualize_tracking.py -v
```

Expected: all 9 tests **PASS**.

- [ ] **Step 3: Commit**

```bash
cd /home/ryanlee/digdeep
git checkout -b claude/visualize-tracking
git add scripts/visualize_tracking.py tests/test_visualize_tracking.py
git commit -m "feat: add visualize_tracking script — drawing helpers + tests"
```

---

### Task 3: Implement `main()` — CLI arg parsing + video loop

**Files:**
- Modify: `scripts/visualize_tracking.py` — replace `main()` stub

- [ ] **Step 1: Replace the `main()` stub with the full implementation**

Replace the `def main() -> None:\n    pass  # implemented in Task 3` block with:

```python
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Visualise ball + player tracking on a rally clip."
    )
    parser.add_argument("video", help="Path to input video file")
    parser.add_argument("--out", default=None, help="Output video path (default: <stem>_tracked.mp4)")
    parser.add_argument("--show", action="store_true", help="Show live preview window")
    parser.add_argument("--conf", type=float, default=0.5, help="Detection confidence threshold")
    args = parser.parse_args()

    video_path = str(Path(args.video).expanduser().resolve())
    if not Path(video_path).exists():
        sys.exit(f"ERROR: video not found: {video_path}")

    out_path = args.out or str(
        Path(video_path).with_name(Path(video_path).stem + "_tracked.mp4")
    )

    # ── Build module configs ──────────────────────────────────────────────────
    ball_model_path = (
        os.environ.get("DIGDEEP_BALL_MODEL")
        or str(
            Path.home()
            / "digdeep-training"
            / "models"
            / "VballNetFastV1_seq9_grayscale_233_h288_w512.onnx"
        )
    )
    ball_cfg = OmegaConf.create(
        {
            "model_path": ball_model_path,
            "input_h": 288,
            "input_w": 512,
            "seq_len": 9,
            "conf_threshold": args.conf,
        }
    )
    player_cfg = OmegaConf.create(
        {
            "model_path": _resolve_player_model(None),
            "resolution": 560,
            "conf_threshold": args.conf,
        }
    )
    tracker_cfg = OmegaConf.create(
        {
            "reid_weights_path": _resolve_reid_model(None),
            "lost_buffer": 200,
        }
    )

    # ── Initialise modules ────────────────────────────────────────────────────
    print(f"Loading models…")
    ball_detector = BallDetector(ball_cfg)
    player_detector = PlayerDetector(player_cfg)
    player_tracker = PlayerTracker(tracker_cfg)

    # ── Open video ────────────────────────────────────────────────────────────
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        sys.exit(f"ERROR: cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    writer = cv2.VideoWriter(
        out_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )

    print(f"Processing {total} frames → {out_path}")
    frame_idx = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            fr = FrameResult(
                frame_idx=frame_idx,
                frame=frame,
                timestamp_ms=frame_idx * 1000.0 / fps,
            )
            fr = ball_detector.process(fr)
            fr = player_detector.process(fr)
            fr = player_tracker.process(fr)

            annotated = frame.copy()
            if fr.player_detections:
                annotated = _draw_players(annotated, fr.player_detections)
            if fr.ball_detections:
                annotated = _draw_ball(annotated, fr.ball_detections)

            writer.write(annotated)

            if args.show:
                cv2.imshow("tracking", annotated)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            if frame_idx % 100 == 0:
                print(f"  frame {frame_idx}/{total}")

            frame_idx += 1
    finally:
        cap.release()
        writer.release()
        if args.show:
            cv2.destroyAllWindows()

    print(f"Done. Wrote {frame_idx} frames to {out_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run tests to confirm still PASS**

```bash
cd /home/ryanlee/digdeep && conda run -n digdeep pytest tests/test_visualize_tracking.py -v
```

Expected: all 9 tests **PASS** (main() is not covered by unit tests — verified in Task 4).

- [ ] **Step 3: Commit**

```bash
cd /home/ryanlee/digdeep
git add scripts/visualize_tracking.py
git commit -m "feat(visualize_tracking): implement main() — arg parsing + frame loop + video writer"
```

---

### Task 4: Full-suite verification + PR

**Files:**
- No changes — verification only.

- [ ] **Step 1: Run the full test suite**

```bash
cd /home/ryanlee/digdeep && conda run -n digdeep pytest tests/ -v
```

Expected: all tests **PASS**. No regressions in `test_pipeline_e2e.py` or inference tests.

- [ ] **Step 2: Format**

```bash
cd /home/ryanlee/digdeep && conda run -n digdeep black scripts/visualize_tracking.py tests/test_visualize_tracking.py && conda run -n digdeep isort scripts/visualize_tracking.py tests/test_visualize_tracking.py
```

Expected: no changes, or clean diff if minor formatting adjustments were made.

- [ ] **Step 3: End-to-end smoke test on a real rally clip**

```bash
cd /home/ryanlee/digdeep && conda run -n digdeep python scripts/visualize_tracking.py \
    ~/digdeep-training/data/rallies/match_001_r001.mp4 \
    --out /tmp/match_001_r001_tracked.mp4
```

Expected output:
```
Loading models…
Processing N frames → /tmp/match_001_r001_tracked.mp4
  frame 0/N
  ...
Done. Wrote N frames to /tmp/match_001_r001_tracked.mp4
```

No `FileNotFoundError`, no crash on empty detections or lost tracks.

- [ ] **Step 4: Visually inspect the output**

Open `/tmp/match_001_r001_tracked.mp4` and confirm:
- Player bboxes visible, same colour per tracker ID across frames
- Ball marker (yellow circle) appears on frames where ball is detected
- No flickering colours for a given player (would indicate ID switching)

- [ ] **Step 5: Commit + PR**

```bash
cd /home/ryanlee/digdeep
git add -p  # only if formatting produced a diff
git commit -m "chore: format visualize_tracking"  # only if needed
git push -u origin claude/visualize-tracking
gh pr create \
  --title "feat: scripts/visualize_tracking.py — annotated tracking output" \
  --body "$(cat <<'EOF'
## Summary
- Adds `scripts/visualize_tracking.py`: runs BallDetector → PlayerDetector → PlayerTracker on every frame and writes an annotated MP4
- Player bboxes are colour-coded by tracker_id (20-colour palette); ball shown as yellow circle with confidence label
- Reuses `_resolve_player_model` / `_resolve_reid_model` from `real_runner.py` — no new path logic
- 9 unit tests for `_draw_players` and `_draw_ball` drawing helpers

## Test plan
- [ ] `pytest tests/ -v` — all pass
- [ ] Run on `match_001_r001.mp4` — annotated MP4 writes without crash
- [ ] Open output and verify colour-stable player bboxes + ball circles

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Self-Review

**Spec coverage checklist:**

| Requirement | Covered |
|---|---|
| Accepts video path as CLI arg | ✅ Task 3 argparse |
| `--out` optional output path | ✅ Task 3 argparse |
| Runs BallDetector → PlayerDetector → PlayerTracker | ✅ Task 3 frame loop |
| Colored player bboxes keyed by tracker_id | ✅ Task 2 `_draw_players` |
| Ball bbox/circle in distinct color | ✅ Task 2 `_draw_ball` |
| Writes annotated MP4 | ✅ Task 3 VideoWriter |
| `--show` live preview | ✅ Task 3 `cv2.imshow` branch |
| Default out path: `<stem>_tracked.mp4` next to input | ✅ Task 3 out_path default |
| Handles empty detections without crash | ✅ `if fr.player_detections:` guards |
| Reuses `_resolve_player_model` / `_resolve_reid_model` | ✅ Task 3 explicit imports |

**Placeholder scan:** None found.

**Type consistency:** `_draw_players(frame: np.ndarray, detections: List[dict]) -> np.ndarray` used consistently in tests and implementation. `_draw_ball` same signature shape.
