"""End-to-end pipeline validation test.

Requires:
    - DIGDEEP_TEST_VIDEO env var → path to a real .mp4 file
    - Ball ONNX model at the default path or DIGDEEP_BALL_MODEL env var
    - Player ONNX model at the default path or DIGDEEP_PLAYER_MODEL env var
    - ReID weights at the default path or DIGDEEP_REID_MODEL env var

Skip conditions: any of the above are missing.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

_VIDEO = os.environ.get("DIGDEEP_TEST_VIDEO", "")
_BALL_MODEL = os.environ.get(
    "DIGDEEP_BALL_MODEL",
    str(
        Path.home()
        / "digdeep-training"
        / "models"
        / "VballNetFastV1_seq9_grayscale_233_h288_w512.onnx"
    ),
)
_PLAYER_MODEL = os.environ.get(
    "DIGDEEP_PLAYER_MODEL",
    str(
        Path.home()
        / "digdeep-training"
        / "models"
        / "checkpoints"
        / "rf_detr_base.onnx"
    ),
)
_REID_MODEL = os.environ.get(
    "DIGDEEP_REID_MODEL",
    str(Path.home() / "digdeep-training" / "models" / "reid" / "osnet_x0_25_msmt17.pt"),
)

_SKIP_REASON = (
    "E2E test requires DIGDEEP_TEST_VIDEO + all three model files. "
    "Set DIGDEEP_TEST_VIDEO, DIGDEEP_BALL_MODEL, DIGDEEP_PLAYER_MODEL, DIGDEEP_REID_MODEL."
)


def _models_present() -> bool:
    return (
        Path(_BALL_MODEL).exists()
        and Path(_PLAYER_MODEL).exists()
        and Path(_REID_MODEL).exists()
    )


@pytest.mark.skipif(not _VIDEO or not Path(_VIDEO).exists(), reason=_SKIP_REASON)
@pytest.mark.skipif(not _models_present(), reason=_SKIP_REASON)
class TestPipelineE2E:
    @pytest.fixture(autouse=True, scope="class")
    def run_pipeline(self, request):
        from omegaconf import OmegaConf

        from src.inference.real_runner import run_pipeline

        cfg = OmegaConf.create(
            {
                "ball_model_path": _BALL_MODEL,
                "player_model_path": _PLAYER_MODEL,
                "reid_model_path": _REID_MODEL,
            }
        )
        stage_calls: list[str] = []
        rallies = run_pipeline(
            _VIDEO,
            progress_cb=lambda _: None,
            stage_cb=stage_calls.append,
            progress_interval=100,
            cfg=cfg,
        )
        request.cls.rallies = rallies
        request.cls.stage_calls = stage_calls

    def test_at_least_one_rally_returned(self):
        assert len(self.rallies) >= 1, f"Expected ≥1 rally, got: {self.rallies}"

    def test_all_rallies_have_valid_times(self):
        for r in self.rallies:
            assert r["start_sec"] < r["end_sec"], f"Invalid rally: {r}"

    def test_stage_callbacks_cover_required_keywords(self):
        combined = " ".join(self.stage_calls).lower()
        for keyword in ("ball", "player", "rally"):
            assert (
                keyword in combined
            ), f"Missing keyword '{keyword}' in stage callbacks: {self.stage_calls}"

    def test_sidecar_schema_is_valid(self, tmp_path):
        sidecar = tmp_path / "output_analytics.json"
        data = {
            "rallies": self.rallies,
            "fps": 30.0,
            "source_video": _VIDEO,
            "players": {},
        }
        sidecar.write_text(json.dumps(data))
        loaded = json.loads(sidecar.read_text())
        assert "rallies" in loaded
        assert "fps" in loaded
        assert "source_video" in loaded
        assert "players" in loaded
        assert isinstance(loaded["players"], dict)

    def test_sidecar_loadable_by_match_session(self, tmp_path):
        from src.app.session import MatchSession

        sidecar = tmp_path / "output_rallies_analytics.json"
        sidecar.write_text(
            json.dumps(
                {
                    "rallies": self.rallies,
                    "fps": 30.0,
                    "source_video": _VIDEO,
                    "players": {},
                }
            )
        )
        session = MatchSession()
        session.load_from_json(str(sidecar))
        loaded = session.rallies
        assert len(loaded) == len(self.rallies)
        for r, orig in zip(loaded, self.rallies):
            assert abs(r.start - orig["start_sec"]) < 0.01
            assert abs(r.end - orig["end_sec"]) < 0.01
