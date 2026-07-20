from __future__ import annotations

import json

from view.animation.state_config import GraphicsConfig, PhysicsConfig, StateConfig
from view.consts import ANIMATION_STATES
from view.pieces.piece_loader import PieceLoader


class AnimationConfigLoader:
    """Loads every state's config.json for one piece kind/color
    combination, and validates that every next_state_when_finished
    points to one of the known states - a config.json typo fails fast
    here, at load time, instead of surfacing as a silently stuck
    animation at runtime."""

    def __init__(self, piece_loader: PieceLoader, states: tuple[str, ...] = ANIMATION_STATES) -> None:
        self._piece_loader = piece_loader
        self._states = states

    def load(self, kind: str, color: str) -> dict[str, StateConfig]:
        """Every state's StateConfig for kind/color, keyed by state name."""
        configs = {state: self._load_one(kind, color, state) for state in self._states}
        self._validate_transitions(configs)
        return configs

    def _load_one(self, kind: str, color: str, state: str) -> StateConfig:
        """Read and parse one state's config.json."""
        state_dir = self._piece_loader.state_dir(kind, color, state)
        with open(state_dir / "config.json", encoding="utf-8") as config_file:
            raw = json.load(config_file)

        physics = PhysicsConfig(
            speed_m_per_sec=raw["physics"]["speed_m_per_sec"],
            next_state_when_finished=raw["physics"]["next_state_when_finished"],
        )
        graphics = GraphicsConfig(
            frames_per_sec=raw["graphics"]["frames_per_sec"],
            is_loop=raw["graphics"]["is_loop"],
        )
        return StateConfig(physics=physics, graphics=graphics)

    def _validate_transitions(self, configs: dict[str, StateConfig]) -> None:
        """Raise if any state's next_state_when_finished is not itself a
        known state."""
        for state, state_config in configs.items():
            next_state = state_config.physics.next_state_when_finished
            if next_state not in configs:
                raise ValueError(
                    f"state {state!r} has next_state_when_finished={next_state!r}, which is not a known state"
                )
