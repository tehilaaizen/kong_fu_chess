from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Callable

from application.auth_service import AuthResult, AuthService
from application.dto import board_placements
from application.game_service import GameService
from persistence.repositories import DEFAULT_RATING
from server import schemas
from server.connection_manager import ConnectionManager
from server.matchmaking import MatchmakingService
from server.room_registry import ROLE_SPECTATOR, RoomRegistry
from server.schemas import InboundMessage

WHITE = "w"
BLACK = "b"
# Rejection reason sent when a spectator tries to play.
SPECTATOR = "spectator"

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
    testable. A connection first authenticates (register or login), then
    joins by room name (delegated to a RoomRegistry): the first into a room
    is White, the second is Black and starts the game, and everyone after
    that is a spectator who watches but cannot play."""

    def __init__(
        self,
        game_service: GameService,
        connection_manager: ConnectionManager,
        auth_service: AuthService,
        game_id_factory: Callable[[], str] = lambda: uuid.uuid4().hex,
        start_board: str = STANDARD_START_BOARD,
        room_registry: RoomRegistry | None = None,
        matchmaking: MatchmakingService | None = None,
    ) -> None:
        self._game_service = game_service
        self._connections = connection_manager
        self._auth = auth_service
        self._game_id_factory = game_id_factory
        self._start_board = start_board
        self._rooms = room_registry if room_registry is not None else RoomRegistry()
        self._matchmaking = matchmaking if matchmaking is not None else MatchmakingService()

    def dispatch(self, connection_id: str, inbound: InboundMessage) -> list[Outgoing]:
        """Handle one inbound message, returning the direct responses.
        State changes that resolve later in time (a motion arriving) are
        broadcast separately by the Broadcaster, not from here."""
        handlers = {
            "register": self._register,
            "login": self._login,
            "join_room": self._join_room,
            "find_match": self._find_match,
            "cancel_match": self._cancel_match,
            "make_move": self._make_move,
            "jump_request": self._jump_request,
            "ping": self._ping,
        }
        handler = handlers.get(inbound.type)
        if handler is None:
            return [Outgoing(connection_id, schemas.error("UNKNOWN_TYPE", f"unknown message type {inbound.type!r}"))]
        return handler(connection_id, inbound)

    def _register(self, connection_id: str, inbound: InboundMessage) -> list[Outgoing]:
        """Create a new account and identify the connection as it."""
        return self._authenticate(connection_id, inbound, self._auth.register)

    def _login(self, connection_id: str, inbound: InboundMessage) -> list[Outgoing]:
        """Authenticate an existing account and identify the connection."""
        return self._authenticate(connection_id, inbound, self._auth.login)

    def _authenticate(
        self, connection_id: str, inbound: InboundMessage, auth_call: Callable[[str, str], AuthResult]
    ) -> list[Outgoing]:
        """Run one register/login attempt: validate the credentials are
        present, call auth_call, and on success identify the connection by
        the authenticated username (replying auth_ok with its rating) or else
        reply auth_failed with the reason."""
        username = inbound.payload.get("username")
        password = inbound.payload.get("password")
        if not isinstance(username, str) or not username or not isinstance(password, str) or not password:
            return [Outgoing(connection_id, schemas.error("MISSING_FIELD", "a username and password are required"))]

        result = auth_call(username, password)
        if not result.is_authenticated:
            return [Outgoing(connection_id, schemas.auth_failed(result.reason, inbound.message_id))]

        self._connections.register(connection_id, result.user.username, result.user.rating)
        return [Outgoing(connection_id, schemas.auth_ok(result.user.username, result.user.rating, inbound.message_id))]

    def _join_room(self, connection_id: str, inbound: InboundMessage) -> list[Outgoing]:
        """Join the room named in the payload. The first connection into a
        room waits as White; the second starts the game (game_started +
        opening snapshot to both); anyone after that is seated as a
        spectator and shown the game already in progress. Re-joining under
        the same connection keeps the existing seat and sends nothing new."""
        if self._connections.get(connection_id) is None:
            return [Outgoing(connection_id, schemas.error("NOT_CONNECTED", "connect before joining"))]

        room = inbound.payload.get("room")
        if not isinstance(room, str) or not room:
            return [Outgoing(connection_id, schemas.error("MISSING_FIELD", "join_room requires a room name"))]

        admission = self._rooms.join(connection_id, room)
        if admission.start_game:
            return self._start_game(admission.white_id, admission.black_id, room)
        if admission.role == ROLE_SPECTATOR:
            return self._seat_spectator(connection_id, admission.game_id)
        return []  # White creator waiting for an opponent, or an idempotent re-join

    def _start_game(self, white_id: str, black_id: str, room: str) -> list[Outgoing]:
        """Room entry point: seat the two players, then remember the game on
        the room so later spectators find it."""
        game_id, outgoing = self._seat_and_start(white_id, black_id)
        self._rooms.set_game_id(room, game_id)
        return outgoing

    def _seat_and_start(self, white_id: str, black_id: str) -> tuple[str, list[Outgoing]]:
        """Seat two connections as White/Black, create their game, and return
        (game_id, the game_started + opening-snapshot messages for both). The
        shared core of both entry points - a named room filling up and a
        matchmaking pairing - so a game starts the same way however it was
        arranged."""
        game_id = self._game_id_factory()
        white = self._connections.get(white_id)
        black = self._connections.get(black_id)
        self._connections.assign_to_game(white_id, game_id, WHITE)
        self._connections.assign_to_game(black_id, game_id, BLACK)

        session = self._game_service.create_session(game_id, white.username, black.username, self._start_board)
        started = schemas.game_started(white.username, black.username, white.rating, black.rating)
        snapshot = self._snapshot_message(session)

        return game_id, [
            Outgoing(white_id, started),
            Outgoing(black_id, started),
            Outgoing(white_id, snapshot),
            Outgoing(black_id, snapshot),
        ]

    def _find_match(self, connection_id: str, inbound: InboundMessage) -> list[Outgoing]:
        """Queue an authenticated connection for an ELO-matched game, or
        start it at once if a suitable opponent is already waiting. While
        waiting, nothing is sent back; the game_started arrives when a match
        is made (or match_timeout if the wait expires)."""
        if self._connections.get(connection_id) is None:
            return [Outgoing(connection_id, schemas.error("NOT_CONNECTED", "authenticate before matchmaking"))]

        pairing = self._matchmaking.request_match(connection_id, self._connections.get(connection_id).rating)
        if pairing is None:
            return []
        return self._seat_and_start(pairing.white_id, pairing.black_id)[1]

    def _cancel_match(self, connection_id: str, inbound: InboundMessage) -> list[Outgoing]:
        """Withdraw a connection from the matchmaking queue (a no-op if it
        was not waiting)."""
        self._matchmaking.cancel(connection_id)
        return []

    def expire_matchmaking(self) -> list[Outgoing]:
        """Time out any player who has waited too long for a match, telling
        each their search expired. Driven by the server's periodic tick."""
        return [Outgoing(cid, schemas.match_timeout()) for cid in self._matchmaking.expire()]

    def _seat_spectator(self, connection_id: str, game_id: str) -> list[Outgoing]:
        """Seat a spectator in game_id (color None, so they receive
        broadcasts but the move handlers reject them) and send them
        game_started plus the current board, so they can render the game
        already under way."""
        self._connections.assign_to_game(connection_id, game_id, None)
        session = self._game_service.session(game_id)
        white_rating, black_rating = self._player_ratings(game_id)
        return [
            Outgoing(
                connection_id,
                schemas.game_started(session.white_user, session.black_user, white_rating, black_rating),
            ),
            Outgoing(connection_id, self._snapshot_message(session)),
        ]

    def _player_ratings(self, game_id: str) -> tuple[int, int]:
        """The (white_rating, black_rating) of the two seated players in
        game_id, read from their live connections - so a spectator's
        game_started can label both players. Falls back to the default rating
        for a color whose player is momentarily missing."""
        by_color: dict[str, int] = {}
        for connection_id in self._connections.connections_in_game(game_id):
            info = self._connections.get(connection_id)
            if info is not None and info.color in (WHITE, BLACK):
                by_color[info.color] = info.rating
        return by_color.get(WHITE, DEFAULT_RATING), by_color.get(BLACK, DEFAULT_RATING)

    def _snapshot_message(self, session) -> dict:
        """A state_snapshot of session's current board (sequence 0 - it is a
        full-state message, not a move delta)."""
        snapshot = session.snapshot()
        return schemas.state_snapshot(
            board_placements(snapshot), snapshot.board_width, snapshot.board_height, sequence=0, game_over=False
        )

    def _make_move(self, connection_id: str, inbound: InboundMessage) -> list[Outgoing]:
        """Apply a "WQe2e5" move on behalf of the connection's color."""
        info = self._connections.get(connection_id)
        if info is None or info.game_id is None:
            return [Outgoing(connection_id, schemas.error("NOT_IN_GAME", "join a game first"))]
        if info.color is None:
            return [Outgoing(connection_id, schemas.move_rejected(SPECTATOR, inbound.message_id))]

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
        if info.color is None:
            return [Outgoing(connection_id, schemas.move_rejected(SPECTATOR, inbound.message_id))]

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

    def disconnect(self, connection_id: str) -> list[Outgoing]:
        """Handle a connection dropping (called by the gateway when a socket
        closes). If it was a player in a game still in progress, the opponent
        wins by abandonment: the session is abandoned, which publishes a
        GameEndedEvent - the Broadcaster turns that into the game_over
        (reason "abandoned") broadcast and the RatingService updates ELO, the
        same path a king capture takes. A spectator or an unseated/unknown
        connection leaving ends nothing. A waiting matchmaking search is
        also dropped. Always removes the connection."""
        info = self._connections.get(connection_id)
        if info is None:
            return []

        self._matchmaking.cancel(connection_id)  # harmless if it was not queued
        if info.game_id is not None and info.color is not None:
            session = self._game_service.session(info.game_id)
            if session is not None and not session.is_over():
                winner = BLACK if info.color == WHITE else WHITE
                session.abandon(winner)

        self._connections.remove(connection_id)
        return []
