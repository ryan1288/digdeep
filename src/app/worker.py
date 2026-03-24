"""Background QThread worker that runs the pipeline and writes the output MP4."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from omegaconf import DictConfig
from PySide6.QtCore import QThread, Signal

from src.inference.real_runner import get_video_frame_count, run_pipeline


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
            self.finished.emit(output_path)

        except Exception as exc:
            self.error.emit(str(exc))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _write_rally_video(self, rallies: list[dict], output_path: str) -> None:
        """Cut each rally segment and concatenate into a single output MP4.

        Uses ffmpeg stream-copy (no re-encode) for speed. Segments are written
        to a temp directory and cleaned up after concatenation.

        Args:
            rallies: List of {"start_sec": float, "end_sec": float} dicts.
            output_path: Destination path for the combined output MP4.
        """
        with tempfile.TemporaryDirectory(prefix="digdeep_rally_") as tmp:
            tmp_path = Path(tmp)
            segment_paths: list[str] = []

            for i, rally in enumerate(rallies):
                start = rally["start_sec"]
                duration = rally["end_sec"] - rally["start_sec"]
                seg_path = str(tmp_path / f"seg_{i:04d}.mp4")

                result = subprocess.run(
                    [
                        "ffmpeg", "-y",
                        "-ss", f"{start:.3f}",
                        "-t", f"{duration:.3f}",
                        "-i", self._video_path,
                        "-c", "copy",
                        seg_path,
                    ],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    raise RuntimeError(
                        f"ffmpeg failed cutting segment {i}: {result.stderr}"
                    )
                segment_paths.append(seg_path)

            # Write concat file list.
            list_path = str(tmp_path / "filelist.txt")
            with open(list_path, "w") as fh:
                for seg in segment_paths:
                    fh.write(f"file '{seg}'\n")

            result = subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", list_path,
                    "-c", "copy",
                    output_path,
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg concat failed: {result.stderr}")
