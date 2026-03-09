# DigDeep UI — Sprint Tracker
# Update at END of every session. This is the first file Claude reads.

## Current State
**Phase**: P1 — Bootstrap
**Last completed**: nothing yet
**Session goal**: Scaffold repo + implement P1.13 basic app

---

## Completed
*(nothing yet)*

---

## Active / Next 3 Tasks
- [ ] P1.13 — Scaffold src/inference/ + src/app/ layout, install deps
- [ ] P1.13 — Basic PySide6 file picker → run pipeline → save rally-only MP4
- [ ] P1.13 — Write analytics JSON sidecar alongside output MP4

---

## Blockers
- Depends on trained model weights being available via HF Hub (not yet uploaded).
  For P1.13, use the local ONNX model from digdeep-training/models/ directly.

---

## Key Paths
```
Repo root:         ~/digdeep/
Source:            src/inference/  src/app/
Models (local):    ~/digdeep-training/models/VballNetFastV1_seq9_grayscale_233_h288_w512.onnx
Training repo:     ~/digdeep-training/
```
