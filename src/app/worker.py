"""Background QThread worker that runs the pipeline and writes the output MP4."""

from __future__ import annotations

import subprocess
from pathlib import Path

from omegaconf import DictConfig
from PySide6.QtCore import QThread, Signal

from src.inference.stub_runner import get_video_frame_count, run_pipeline


class PipelineWorker(QThread):
    """Runs the inference pipeline in a background thread.

    Signals:
        progress: Emitted with (current_frame, total_frames) periodically.
        stage_changed: Emitted with a human-readable pipeline stage label.
        finished: Emitted with the path to the output MP4 on success.
        error: Emitted with an error message string on failure.
    """

    progress = Signal(int, int)
    stage_changed = Signal(str)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, video_path: str, output_dir: str, cfg: DictConfig) -> None:
        super().__init__()
        self._video_path = video_path
        self._output_dir = output_dir
        self._cfg = cfg

    def run(self) -> None:
        try:
            self.stage_changed.emit("Opening video...")
            total = get_video_frame_count(self._video_path)
            if total <= 0:
                self.error.emit(f"Could not read video: {self._video_path}")
                return

            def progress_cb(frame_idx: int) -> None:
                self.progress.emit(frame_idx, total)

            run_pipeline(
                self._video_path,
                progress_cb=progress_cb,
                stage_cb=self.stage_changed.emit,
                progress_interval=self._cfg.progress_update_interval,
            )
            # Emit 100% after pipeline completes
            self.progress.emit(total, total)

            self.stage_changed.emit("Writing output MP4...")
            stem = Path(self._video_path).stem
            output_path = str(
                Path(self._output_dir) / f"{stem}{self._cfg.output_suffix}.mp4"
            )

            result = subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    self._video_path,
                    "-c:v",
                    "libx264",
                    "-crf",
                    str(self._cfg.ffmpeg_crf),
                    "-preset",
                    self._cfg.ffmpeg_preset,
                    output_path,
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                self.error.emit(result.stderr)
                return

            self.finished.emit(output_path)

        except Exception as exc:
            self.error.emit(str(exc))
