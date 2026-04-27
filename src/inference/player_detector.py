"""Player detector module — RF-DETR ONNX wrapper."""

from __future__ import annotations

from pathlib import Path
from typing import List

import cv2
import numpy as np
import onnxruntime as ort
from omegaconf import DictConfig

from src.pipeline.base import PipelineModule
from src.pipeline.frame_result import FrameResult

_IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


class PlayerDetector(PipelineModule):
    """Detects players using RF-DETR ONNX (opset 17).

    Reads:  frame_result.frame  (H×W×3 BGR)
    Writes: frame_result.player_detections →
            List[{"bbox": [x1,y1,x2,y2], "tracker_id": -1, "conf": float}]

    Config keys:
        model_path (str):       Path to the RF-DETR ONNX file.
        resolution (int):       Square input size used during export (default 560).
        conf_threshold (float): Minimum sigmoid score to keep a detection (default 0.5).
    """

    def __init__(self, cfg: DictConfig) -> None:
        super().__init__(cfg)
        model_path = str(Path(cfg.model_path).expanduser())
        if not Path(model_path).exists():
            raise FileNotFoundError(
                f"Player detector model not found: {model_path}\n"
                "Set DIGDEEP_PLAYER_MODEL env var or player_model_path in configs/app/app.yaml."
            )
        self._resolution: int = int(cfg.get("resolution", 560))
        self._conf_threshold: float = float(cfg.get("conf_threshold", 0.5))
        self._session = ort.InferenceSession(
            model_path,
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
        )
        self._input_name: str = self._session.get_inputs()[0].name

    def process(self, frame_result: FrameResult) -> FrameResult:
        """Run player detection on the current frame.

        Args:
            frame_result: FrameResult with a populated ``frame`` (BGR ndarray).

        Returns:
            frame_result with ``player_detections`` populated.
        """
        orig_h, orig_w = frame_result.frame.shape[:2]
        tensor = self._preprocess(frame_result.frame)
        dets, labels = self._session.run(None, {self._input_name: tensor})
        frame_result.player_detections = self._postprocess(dets, labels, orig_h, orig_w)
        return frame_result

    def _preprocess(self, frame: np.ndarray) -> np.ndarray:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (self._resolution, self._resolution))
        normalized = resized.astype(np.float32) / 255.0
        normalized = (normalized - _IMAGENET_MEAN) / _IMAGENET_STD
        return np.transpose(normalized, (2, 0, 1))[np.newaxis]  # (1, 3, H, W)

    def _postprocess(
        self,
        dets: np.ndarray,
        labels: np.ndarray,
        orig_h: int,
        orig_w: int,
    ) -> List[dict]:
        # Class index 0 = player (RF-DETR exports with player as first class).
        # Clip logits to avoid float32 overflow in exp for extreme values.
        logits = np.clip(labels[0, :, 0], -88.0, 88.0)
        scores = 1.0 / (1.0 + np.exp(-logits))
        mask = scores > self._conf_threshold
        boxes = dets[0][mask]  # (M, 4) cxcywh normalized [0,1]
        confs = scores[mask]

        results: List[dict] = []
        for (cx, cy, bw, bh), conf in zip(boxes, confs):
            x1 = (cx - bw / 2) * orig_w
            y1 = (cy - bh / 2) * orig_h
            x2 = (cx + bw / 2) * orig_w
            y2 = (cy + bh / 2) * orig_h
            results.append(
                {
                    "bbox": [float(x1), float(y1), float(x2), float(y2)],
                    "tracker_id": -1,
                    "conf": float(conf),
                }
            )
        return results
