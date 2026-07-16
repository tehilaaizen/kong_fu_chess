from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PhysicsConfig:
    """One state's "physics" block from its config.json. Not yet consumed
    by any timing logic - RealTimeArbiter/PieceRules own actual travel/
    jump duration - reserved for the future move of animation-state
    transitions into PieceAnimator, which will read
    next_state_when_finished to know what state follows this one."""

    speed_m_per_sec: float
    next_state_when_finished: str


@dataclass(frozen=True)
class GraphicsConfig:
    """One state's "graphics" block from its config.json - the only part
    AnimationClip currently reads."""

    frames_per_sec: int
    is_loop: bool


@dataclass(frozen=True)
class StateConfig:
    """One piece-state's full, parsed config.json."""

    physics: PhysicsConfig
    graphics: GraphicsConfig
