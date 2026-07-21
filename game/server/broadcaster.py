from __future__ import annotations

from typing import Callable

from application.dto import board_grid
from application.game_service import GameService
from messaging.application_events import GameEndedEvent, GameMoveAppliedEvent
from server import schemas
from server.connection_manager import ConnectionManager
from server.message_dispatcher import Outgoing

Sink = Callable[[Outgoing], None]


class Broadcaster:
    """Subscribes to the ApplicationMessageBus and turns each game's
    application events into per-game broadcasts, pushed to a sink the
    async gateway drains. Handles the time-driven state changes (a motion
    arriving, a game ending) that no single client command produced -
    direct command replies come from the MessageDispatcher instead.

    handle() is the bus subscription; it and the translation it delegates
    to are synchronous and unit-testable with a fake sink."""

    def __init__(self, game_service: GameService, connection_manager: ConnectionManager, sink: Sink) -> None:
        self._game_service = game_service
        self._connections = connection_manager
        self._sink = sink

    def handle(self, event: object) -> None:
        """Bus handler: push every resulting broadcast to the sink."""
        for outgoing in self._translate(event):
            self._sink(outgoing)

    def _translate(self, event: object) -> list[Outgoing]:
        """The broadcasts one application event produces, one Outgoing per
        connection in that game (players and spectators)."""
        if isinstance(event, GameMoveAppliedEvent):
            session = self._game_service.session(event.game_id)
            if session is None:
                return []
            message = schemas.state_snapshot(board_grid(session.snapshot()), event.sequence, game_over=False)
            return self._to_everyone_in(event.game_id, message)

        if isinstance(event, GameEndedEvent):
            return self._to_everyone_in(event.game_id, schemas.game_over(event.winner))

        return []

    def _to_everyone_in(self, game_id: str, message: dict) -> list[Outgoing]:
        """message addressed to every connection seated in game_id."""
        return [Outgoing(cid, message) for cid in self._connections.connections_in_game(game_id)]
