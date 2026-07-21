from __future__ import annotations

from dataclasses import dataclass

from model.position import Position


@dataclass(frozen=True)
class GameStartedEvent:
    """Published when a GameSession is created for two players - the
    server turns this into a game_started network message (for start
    animation/sound). GameEngine has no "not started" state, so this is an
    application-level event, not a domain one."""

    game_id: str
    white_user: str
    black_user: str


@dataclass(frozen=True)
class GameMoveAppliedEvent:
    """Published when a motion logically arrived (translated from the
    engine's on_arrival). Carries the move's cells and piece identity plus
    the captured piece's kind (None if nothing was captured), and the
    game's monotonic sequence number for ordering client updates."""

    game_id: str
    sequence: int
    source: Position
    destination: Position
    color: str
    kind: str
    captured_kind: str | None


@dataclass(frozen=True)
class GameEndedEvent:
    """Published when a king was captured (translated from the engine's
    on_game_over). winner is the color of the side still standing."""

    game_id: str
    winner: str
