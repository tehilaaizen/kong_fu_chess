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
class MotionStartedEvent:
    """Published when a move was accepted and the piece started travelling
    (translated from the engine's on_motion_started). Carries the moving
    piece's stable id/color/kind, its source and destination cells, and how
    long the slide takes - everything a client needs to reconstruct the
    engine's on_motion_started call and drive the same slide animation."""

    game_id: str
    piece_id: int
    color: str
    kind: str
    source: Position
    destination: Position
    duration_ms: int


@dataclass(frozen=True)
class JumpStartedEvent:
    """Published when a jump was accepted and the piece went airborne
    (translated from the engine's on_jump_started). Carries the piece's
    stable id/color/kind, the cell it jumps in place on, and the jump's
    duration."""

    game_id: str
    piece_id: int
    color: str
    kind: str
    position: Position
    duration_ms: int


@dataclass(frozen=True)
class RestStartedEvent:
    """Published when a piece entered a cooldown (translated from the
    engine's on_rest_started). Carries the piece's stable id/color/kind,
    the cooldown duration, and its label ("long_rest" after a move,
    "short_rest" after a jump) so a client can drive the draining rest
    overlay."""

    game_id: str
    piece_id: int
    color: str
    kind: str
    duration_ms: int
    label: str


@dataclass(frozen=True)
class GameMoveAppliedEvent:
    """Published when a motion logically arrived (translated from the
    engine's on_arrival). Carries the move's cells and piece identity
    (including the arriving piece's stable id, so a client can key its
    per-piece animator) plus the captured piece's kind (None if nothing
    was captured), and the game's monotonic sequence number for ordering
    client updates."""

    game_id: str
    sequence: int
    piece_id: int
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
