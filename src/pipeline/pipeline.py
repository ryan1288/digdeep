"""Pipeline orchestrator: chains PipelineModules sequentially over video frames."""

import logging
from typing import Any, Dict, Iterator, List, Optional

from omegaconf import DictConfig

from src.inference.aggregator import AnalyticsAggregator
from src.pipeline.base import PipelineModule
from src.pipeline.frame_result import FrameResult

logger = logging.getLogger(__name__)


class Pipeline:
    """Runs a sequence of PipelineModules over a stream of FrameResults.

    AnalyticsAggregator is always appended as the final module so that
    ``finalize()`` can be called after the run to obtain the analytics JSON.

    Args:
        modules: Ordered list of pipeline modules to apply per frame.
                 AnalyticsAggregator will be appended automatically as the
                 last step if an ``aggregator`` is provided.
        cfg: Top-level Hydra DictConfig.
        aggregator: Optional AnalyticsAggregator instance. When supplied it is
                    appended to ``modules`` so it runs last on every frame, and
                    its ``finalize()`` method is exposed via ``Pipeline.finalize()``.
    """

    def __init__(
        self,
        modules: List[PipelineModule],
        cfg: DictConfig,
        aggregator: Optional[AnalyticsAggregator] = None,
    ) -> None:
        self._aggregator = aggregator
        if aggregator is not None:
            self.modules: List[PipelineModule] = list(modules) + [aggregator]
        else:
            self.modules = list(modules)
        self.cfg = cfg

    def run(self, frames: Iterator[FrameResult]) -> Iterator[FrameResult]:
        """Process each frame through all modules in order.

        Args:
            frames: Iterable of raw FrameResult objects (frame + metadata).

        Yields:
            Fully annotated FrameResult after all modules have run.
        """
        for frame_result in frames:
            for module in self.modules:
                frame_result = module.process(frame_result)
            yield frame_result

    def finalize(self, frames: List[FrameResult]) -> Dict[str, Any]:
        """Produce the analytics output JSON for the processed video.

        Delegates to the AnalyticsAggregator's ``finalize()`` method.  Must be
        called after all frames have been consumed from ``run()``.

        Args:
            frames: The complete list of FrameResults returned by ``run()``.

        Returns:
            Analytics dict with 'players' and 'rallies' keys.

        Raises:
            RuntimeError: If no aggregator was supplied at construction time.
        """
        if self._aggregator is None:
            raise RuntimeError(
                "Pipeline.finalize() requires an AnalyticsAggregator. "
                "Pass aggregator=... to Pipeline.__init__."
            )
        return self._aggregator.finalize(frames)
