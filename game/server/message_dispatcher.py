from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Callable

from application.dto import board_grid
from application.game_service import GameService
from server import schemas
from server.connection_manager import ConnectionManager
from server.schemas import InboundMessage

WHITE = "w"
BLACK = "b"

# Standard starting position in this project's board notation - the layout
# every Phase A quick match begins from.
STANDARD_START_BOARD = "\n".join(
    [
        "bR bN bB bQ bK bB bN bR",
        "bP bP bP bP bP bP bP bP",
        ". . . . . . . .",
        ". . . . . . . .",
        ". . . . . . . .",
        ". . . . . . . .",
        "wP wP wP wP wP wP wP wP",
        "wR wN wB wQ wK wB wN wR",
    ]
)


@dataclass(frozen=True)
class Outgoing:
    """One message to send to one specific connection. The dispatcher
    resolves broadcasts (e.g. both players on game start) into several of
    these, so the gateway just sends each to its connection."""

    connection_id: str
    message: dict


class MessageDispatcher:
    """Turns one parsed inbound message from a connection into the
    messages to send back, calling the application services. Pure and
    synchronous - the async gateway owns the sockets and the event loop;
    this owns none of that, so the whole command vocabulary is unit
    testable. Phase A pairs the first two connections that ask to play
    (first = White, second = Black); real matchmaking is a later phase."""

    def __init__(
        self,
        game_service: GameService,
        connection_manager: ConnectionManager,
        game_id_factory: Callable[[], str] = lambda: uuid.uuid4().hex,
        start_board: str = STANDARD_START_BOARD,
    ) -> None:
        self._game_service = game_service
        self._connections = connection_manager
        self._game_id_factory = game_id_factory
        self._start_board = start_board
        self._waiting_connection: str | None = None

    def dispatch(self, connection_id: str, inbound: InboundMessage) -> list[Outgoing]:
        """Handle one inbound message, returning the direct responses.
        State changes that resolve later in time (a motion arriving) are
        broadcast separately by the Broadcaster, not from here."""
        handlers = {
            "connect": self._connect,
            "join_game": self._join_game,
            "make_move": self._make_move,
            "jump_request": self._jump_request,
            "ping": self._ping,
        }
        handler = handlers.get(inbound.type)
        if handler is None:
            return [Outgoing(connection_id, schemas.error("UNKNOWN_TYPE", f"unknown message type {inbound.type!r}"))]
        return handler(connection_id, inbound)

    def _connect(self, connection_id: str, inbound: InboundMessage) -> list[Outgoing]:
        """Identify a connection by its username (Phase A: no password)."""
        username = inbound.payload.get("username")
        if not isinstance(username, str) or not username:
            return [Outgoing(connection_id, schemas.error("MISSING_FIELD", "connect requires a username"))]
        self._connections.register(connection_id, username)
        return []

    def _join_game(self, connection_id: str, inbound: InboundMessage) -> list[Outgoing]:
        """Enter the quick-match queue. The first caller waits; the second
        is paired with it into a new game (first = White, second = Black),
        and both are sent game_started plus the opening state_snapshot."""
        if self._connections.get(connection_id) is None:
            return [Outgoing(connection_id, schemas.error("NOT_CONNECTED", "connect before joining"))]

        if self._waiting_connection is None or self._waiting_connection == connection_id:
            self._waiting_connection = connection_id
            return []

        white_id = self._waiting_connection
        black_id = connection_id
        self._waiting_connection = None
        return self._start_game(white_id, black_id)

    def _start_game(self, white_id: str, black_id: str) -> list[Outgoing]:
        """Seat two connections as White/Black, create their game, and
        return the game_started + opening-snapshot messages for both."""
        game_id = self._game_id_factory()
        white_user = self._connections.get(white_id).username
        black_user = self._connections.get(black_id).username
        self._connections.assign_to_game(white_id, game_id, WHITE)
        self._connections.assign_to_game(black_id, game_id, BLACK)

        session = self._game_service.create_session(game_id, white_user, black_user, self._start_board)
        started = schemas.game_started(white_user, black_user)
        snapshot = schemas.state_snapshot(board_grid(session.snapshot()), sequence=0, game_over=False)

        return [
            Outgoing(white_id, started),
            Outgoing(black_id, started),
            Outgoing(white_id, snapshot),
            Outgoing(black_id, snapshot),
        ]

    def _make_move(self, connection_id: str, inbound: InboundMessage) -> list[Outgoing]:
        """Apply a "WQe2e5" move on behalf of the connection's color."""
        info = self._connections.get(connection_id)
        if info is None or info.game_id is None:
            return [Outgoing(connection_id, schemas.error("NOT_IN_GAME", "join a game first"))]

        move = inbound.payload.get("move")
        if not isinstance(move, str):
            return [Outgoing(connection_id, schemas.error("MISSING_FIELD", "make_move requires a move string"))]

        result = self._game_service.handle_move(info.game_id, info.color, move)
        if result.is_accepted:
            return [Outgoing(connection_id, schemas.move_accepted(inbound.message_id))]
        return [Outgoing(connection_id, schemas.move_rejected(result.reason, inbound.message_id))]

    def _jump_request(self, connection_id: str, inbound: InboundMessage) -> list[Outgoing]:
        """Make the connection's piece at a cell jump."""
        info = self._connections.get(connection_id)
        if info is None or info.game_id is None:
            return [Outgoing(connection_id, schemas.error("NOT_IN_GAME", "join a game first"))]

        cell = inbound.payload.get("cell")
        if not isinstance(cell, str):
            return [Outgoing(connection_id, schemas.error("MISSING_FIELD", "jump_request requires a cell string"))]

        result = self._game_service.handle_jump(info.game_id, info.color, cell)
        if result.is_accepted:
            return [Outgoing(connection_id, schemas.move_accepted(inbound.message_id))]
        return [Outgoing(connection_id, schemas.move_rejected(result.reason, inbound.message_id))]

    def _ping(self, connection_id: str, inbound: InboundMessage) -> list[Outgoing]:
        """Liveness."""
        return [Outgoing(connection_id, schemas.pong())]
