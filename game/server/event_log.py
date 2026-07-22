from __future__ import annotations

from typing import Callable

from messaging.application_events import (
    GameEndedEvent,
    GameMoveAppliedEvent,
    GameStartedEvent,
    JumpStartedEvent,
    MotionStartedEvent,
)
from model.position import Position

Emit = Callable[[str], None]


class EventLog:
    """Subscribes to the ApplicationMessageBus and writes one human-readable
    line per game event - a start, every move (motion started and arrival),
    every jump, and the end. It is the single place that turns application
    events into log text, and it stays free of any logging library: the
    line is handed to an injected emit callback (loguru's logger.info in
    production, a recording list in tests), so the whole formatting is
    unit-testable and the app/messaging layers never learn how logs are
    written. Rest/cooldown events are intentionally skipped as noise - they
    are not moves."""

    def __init__(self, emit: Emit) -> None:
        """emit receives each formatted log line (e.g. loguru's
        logger.info)."""
        self._emit = emit

    def handle(self, event: object) -> None:
        """Bus handler: emit a line for a loggable event, ignore the rest."""
        line = self._format(event)
        if line is not None:
            self._emit(line)

    def _format(self, event: object) -> str | None:
        """The log line for one application event, or None for an event
        type that isn't logged."""
        if isinstance(event, GameStartedEvent):
            return f"game {event.game_id} started - white={event.white_user} black={event.black_user}"

        if isinstance(event, MotionStartedEvent):
            return (
                f"game {event.game_id}: {event.color}{event.kind}#{event.piece_id} "
                f"move {_cell(event.source)}->{_cell(event.destination)} ({event.duration_ms}ms)"
            )

        if isinstance(event, JumpStartedEvent):
            return (
                f"game {event.game_id}: {event.color}{event.kind}#{event.piece_id} "
                f"jump @{_cell(event.position)} ({event.duration_ms}ms)"
            )

        if isinstance(event, GameMoveAppliedEvent):
            captured = f" captured {event.captured_kind}" if event.captured_kind is not None else ""
            return (
                f"game {event.game_id} #{event.sequence}: {event.color}{event.kind} "
                f"arrived {_cell(event.source)}->{_cell(event.destination)}{captured}"
            )

        if isinstance(event, GameEndedEvent):
            return f"game {event.game_id} ended - winner={event.winner}"

        return None


def _cell(position: Position) -> str:
    """A board cell as "(row,col)" for a log line."""
    return f"({position.row},{position.col})"
