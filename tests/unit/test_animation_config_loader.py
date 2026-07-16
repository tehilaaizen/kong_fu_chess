import json
from pathlib import Path

import pytest

from view.animation.animation_config_loader import AnimationConfigLoader
from view.config import ANIMATION_STATES
from view.pieces.piece_loader import PieceLoader


def _setup_piece(piece_dir: Path, next_state_by_state: dict) -> None:
    for state, next_state in next_state_by_state.items():
        state_dir = piece_dir / "states" / state
        state_dir.mkdir(parents=True)
        config = {
            "physics": {"speed_m_per_sec": 1.5, "next_state_when_finished": next_state},
            "graphics": {"frames_per_sec": 5, "is_loop": True},
        }
        (state_dir / "config.json").write_text(json.dumps(config), encoding="utf-8")


def _piece_loader_at(assets_root: Path) -> PieceLoader:
    return PieceLoader(assets_root=assets_root)


def test_load_reads_every_states_config(tmp_path):
    _setup_piece(tmp_path / "PW", {state: "idle" for state in ANIMATION_STATES})

    configs = AnimationConfigLoader(_piece_loader_at(tmp_path)).load("P", "w")

    assert set(configs.keys()) == set(ANIMATION_STATES)
    assert configs["move"].graphics.frames_per_sec == 5
    assert configs["move"].physics.next_state_when_finished == "idle"


def test_load_raises_when_a_next_state_when_finished_is_unknown(tmp_path):
    next_state_by_state = {state: "idle" for state in ANIMATION_STATES}
    next_state_by_state["move"] = "nonexistent"
    _setup_piece(tmp_path / "PW", next_state_by_state)

    with pytest.raises(ValueError):
        AnimationConfigLoader(_piece_loader_at(tmp_path)).load("P", "w")


def test_load_reads_the_real_project_assets():
    configs = AnimationConfigLoader(PieceLoader()).load("P", "w")

    assert set(configs.keys()) == set(ANIMATION_STATES)
