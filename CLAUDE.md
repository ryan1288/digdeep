# DigDeep — Claude Context
@/home/ryanlee/digdeep-training/SHARED_CONTEXT.md

---

## This Repo's Role
Public inference app. Loads ONNX weights from HuggingFace Hub, runs the pipeline,
and presents results in a PySide6 desktop UI. No training code lives here.
Source of truth for architecture and decisions: `digdeep-training/SHARED_CONTEXT.md`.

## Tech Stack
```
Python 3.11
onnxruntime     runs all models (no PyTorch at inference time)
opencv-python   frame ops + video I/O
PySide6         desktop UI (LGPL)
huggingface_hub auto-download weights on first launch
hydra-core      config management
pytest + black + isort
```

## Repo Structure
```
src/
  inference/    ONNX Runtime wrappers mirroring the training pipeline modules
  app/          PySide6 UI — file picker, rally list, stats panel, video preview
models/         config YAMLs only (weights downloaded from HF Hub, never committed)
tests/          pytest — mirrors src/ structure
```

## Inference-Specific Conventions
- No PyTorch imports — ONNX Runtime only for all model inference
- Model weights auto-downloaded via `huggingface_hub.hf_hub_download()` on first run
- Module interface mirrors training: `process(frame_result: FrameResult) -> FrameResult`
- FrameResult schema must stay in sync with `digdeep-training/src/pipeline/frame_result.py`
- Analytics JSON schema must stay in sync with `digdeep-training/SHARED_CONTEXT.md`

## Setup
```bash
conda create -n digdeep-app python=3.11
pip install onnxruntime opencv-python PySide6 huggingface_hub hydra-core
pip install pytest black isort
```

## Before Finishing Any Task
```bash
pytest tests/ -v && black src/ && isort src/ && git diff --stat
```
