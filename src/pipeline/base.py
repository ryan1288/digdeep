"""PipelineModule abstract base class for all inference pipeline stages."""

import logging
from abc import ABC, abstractmethod

from omegaconf import DictConfig

from src.pipeline.frame_result import FrameResult


class PipelineModule(ABC):
    """Abstract base class for all pipeline modules.

    Subclasses implement process() to read from and write to FrameResult.
    Config is passed via Hydra DictConfig; no hardcoded paths or values.
    """

    logger = logging.getLogger(__name__)

    def __init__(self, cfg: DictConfig) -> None:
        """Initialize with Hydra config.

        Args:
            cfg: Hydra DictConfig containing module-specific settings.
        """
        self.cfg = cfg

    @abstractmethod
    def process(self, frame_result: FrameResult) -> FrameResult:
        """Process a single frame, reading and writing FrameResult fields.

        Args:
            frame_result: Mutable data carrier for this frame.

        Returns:
            Updated FrameResult with this module's outputs populated.
        """
