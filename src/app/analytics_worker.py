"""AnalyticsPipelineWorker — extends PipelineWorker to write analytics JSON sidecar."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from omegaconf import DictConfig

from src.app.worker import PipelineWorker
from src.inference.real_runner import get_video_frame_count, run_pipeline


class AnalyticsPipelineWorker(PipelineWorker):
    """Runs the inference pipeline and writes an analytics JSON sidecar.

    Behaviour is identical to PipelineWorker except that after writing the
    rally MP4 it also writes a ``<stem>_rallies_analytics.json`` sidecar
    next to the output file.  The ``finished`` signal still emits the output
    MP4 path — callers load the sidecar by replacing ``.mp4`` →
    ``_analytics.json``.
    """

    def run(self) -> None:
        try:
            self.stage_changed.emit("Opening video...")
            total = get_video_frame_count(self._video_path)
            if total <= 0:
                self.error.emit(f"Could not read video: {self._video_path}")
                return

            import cv2

            cap = cv2.VideoCapture(self._video_path)
            fps: float = cap.get(cv2.CAP_PROP_FPS) or 30.0
            cap.release()

            def progress_cb(frame_idx: int) -> None:
                self.progress.emit(frame_idx, total)

            rallies = run_pipeline(
                self._video_path,
                progress_cb=progress_cb,
                stage_cb=self.stage_changed.emit,
                progress_interval=self._cfg.progress_update_interval,
                cfg=self._cfg,
            )
            self.progress.emit(total, total)

            if not rallies:
                self.error.emit("No rallies detected in this video.")
                return

            self.stage_changed.emit(f"Writing {len(rallies)} rally segment(s)...")
            stem = Path(self._video_path).stem
            output_path = str(
                Path(self._output_dir) / f"{stem}{self._cfg.output_suffix}.mp4"
            )
            self._write_rally_video(rallies, output_path)

            # Write analytics JSON sidecar
            sidecar_path = output_path.replace(".mp4", "_analytics.json")
            analytics = {
                "rallies": [
                    {"start_sec": r["start_sec"], "end_sec": r["end_sec"]}
                    for r in rallies
                ],
                "fps": fps,
                "source_video": self._video_path,
                "players": {},
            }
            with open(sidecar_path, "w") as fh:
                json.dump(analytics, fh, indent=2)

            self.finished.emit(output_path)

        except Exception as exc:
            self.error.emit(str(exc))
