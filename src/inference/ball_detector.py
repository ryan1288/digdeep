"""Ball detector module — VballNetFastV1 / TrackNetV3 (ONNX heatmap regression)."""

from collections import deque
from typing import List, Optional

import cv2
import numpy as np
import onnxruntime as ort
from omegaconf import DictConfig

from src.pipeline.base import PipelineModule
from src.pipeline.frame_result import FrameResult


class BallDetector(PipelineModule):
    """Detects volleyball using a heatmap-regression ONNX model (VballNetFastV1).

    Maintains a rolling buffer of the last ``seq_len`` preprocessed grayscale
    frames and runs the model on each new frame.  Only the heatmap for the
    **current** (last) frame is decoded to produce ball_detections.

    Reads:  frame_result.frame
    Writes: frame_result.ball_detections  →  List[{"x": float, "y": float, "conf": float}]

    Config keys (ball_detector.yaml):
        model_path (str):   Path to the ONNX model file.
        input_h (int):      Model input height in pixels (default 288).
        input_w (int):      Model input width in pixels (default 512).
        seq_len (int):      Number of frames in the temporal stack (default 9).
        conf_threshold (float): Heatmap binarisation threshold (default 0.5).
    """

    def __init__(self, cfg: DictConfig) -> None:
        super().__init__(cfg)

        self._input_h: int = int(cfg.get("input_h", 288))
        self._input_w: int = int(cfg.get("input_w", 512))
        self._seq_len: int = int(cfg.get("seq_len", 9))
        self._conf_threshold: float = float(cfg.get("conf_threshold", 0.5))

        self._session: ort.InferenceSession = ort.InferenceSession(
            cfg.model_path,
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
        )
        input_info = self._session.get_inputs()[0]
        self._input_name: str = input_info.name

        # Rolling buffer of preprocessed (H, W) float32 greyscale frames.
        self._frame_buffer: deque = deque(
            [np.zeros((self._input_h, self._input_w), dtype=np.float32)]
            * self._seq_len,
            maxlen=self._seq_len,
        )

        self.logger.info(
            "BallDetector ready — model=%s  input=(%d×%d)  seq_len=%d  threshold=%.2f",
            cfg.model_path,
            self._input_h,
            self._input_w,
            self._seq_len,
            self._conf_threshold,
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def process(self, frame_result: FrameResult) -> FrameResult:
        """Run ball detection for the current frame.

        Args:
            frame_result: Carrier containing the BGR frame.

        Returns:
            frame_result with ball_detections populated.
        """
        preprocessed = self._preprocess_frame(frame_result.frame)
        self._frame_buffer.append(preprocessed)

        input_tensor = self._build_input_tensor()
        heatmaps = self._run_inference(input_tensor)

        # Decode only the last heatmap (corresponds to the current frame).
        current_heatmap = heatmaps[0, -1, :, :]
        orig_h, orig_w = frame_result.frame.shape[:2]
        detections = self._decode_heatmap(current_heatmap, orig_h, orig_w)

        frame_result.ball_detections = detections
        return frame_result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """Convert a BGR frame to a normalised greyscale float32 model input.

        Args:
            frame: BGR image, shape (H, W, 3).

        Returns:
            Greyscale float32 array of shape (input_h, input_w), values in [0, 1].
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (self._input_w, self._input_h))
        return resized.astype(np.float32) / 255.0

    def _build_input_tensor(self) -> np.ndarray:
        """Stack the frame buffer into the (1, seq_len, H, W) ONNX input tensor.

        Returns:
            float32 array of shape (1, seq_len, input_h, input_w).
        """
        stacked = np.stack(list(self._frame_buffer), axis=0)  # (seq_len, H, W)
        return stacked[np.newaxis].astype(np.float32)  # (1, seq_len, H, W)

    def _run_inference(self, input_tensor: np.ndarray) -> np.ndarray:
        """Execute the ONNX session and return raw heatmaps.

        Args:
            input_tensor: float32 array (1, seq_len, H, W).

        Returns:
            float32 heatmap array (1, seq_len, H, W).
        """
        outputs = self._session.run(None, {self._input_name: input_tensor})
        return outputs[0]

    def _decode_heatmap(
        self,
        heatmap: np.ndarray,
        orig_h: int,
        orig_w: int,
    ) -> List[dict]:
        """Convert a single heatmap to a list of ball detections.

        Binarises the heatmap, finds contours, selects the largest blob, and
        returns its centroid scaled back to the original frame resolution.

        Args:
            heatmap: float32 array (input_h, input_w).
            orig_h:  Original frame height (pixels).
            orig_w:  Original frame width (pixels).

        Returns:
            List of detection dicts [{x, y, conf}], empty if no ball found.
        """
        _, binary = cv2.threshold(heatmap, self._conf_threshold, 1.0, cv2.THRESH_BINARY)
        binary_u8 = (binary * 255).astype(np.uint8)
        contours, _ = cv2.findContours(
            binary_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            return []

        largest = max(contours, key=cv2.contourArea)
        moments = cv2.moments(largest)
        if moments["m00"] == 0:
            return []

        cx_model = moments["m10"] / moments["m00"]
        cy_model = moments["m01"] / moments["m00"]

        # Scale to original frame coordinates.
        x = cx_model * orig_w / self._input_w
        y = cy_model * orig_h / self._input_h

        # Confidence: mean heatmap activation inside the blob's bounding rect.
        x_int, y_int = int(cx_model), int(cy_model)
        conf = float(
            np.clip(heatmap[y_int, x_int], 0.0, 1.0)
            if 0 <= y_int < self._input_h and 0 <= x_int < self._input_w
            else self._conf_threshold
        )

        return [{"x": float(x), "y": float(y), "conf": conf}]
