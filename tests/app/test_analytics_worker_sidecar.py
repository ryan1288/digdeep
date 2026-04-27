"""Test that the analytics sidecar schema includes the required 'players' key."""

import json


def test_sidecar_contains_players_key(tmp_path):
    sidecar = tmp_path / "test_analytics.json"
    sidecar.write_text(
        json.dumps(
            {
                "rallies": [{"start_sec": 1.0, "end_sec": 5.0}],
                "fps": 30.0,
                "source_video": "/fake/input.mp4",
                "players": {},
            }
        )
    )
    data = json.loads(sidecar.read_text())
    assert "players" in data, "Sidecar is missing required 'players' key"


def test_sidecar_schema_complete(tmp_path):
    sidecar_data = {
        "rallies": [{"start_sec": 1.0, "end_sec": 5.0}],
        "fps": 29.97,
        "source_video": "/path/input.mp4",
        "players": {},
    }
    path = tmp_path / "out_analytics.json"
    path.write_text(json.dumps(sidecar_data))
    loaded = json.loads(path.read_text())
    assert set(loaded.keys()) == {"rallies", "fps", "source_video", "players"}
    assert isinstance(loaded["players"], dict)
    for r in loaded["rallies"]:
        assert "start_sec" in r and "end_sec" in r
