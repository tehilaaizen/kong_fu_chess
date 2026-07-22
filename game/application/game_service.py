from __future__ import annotations

from application.game_session import GameSession, Publisher
from engine.game_engine import GameEngine, MoveResult
from messaging.application_events import GameStartedEvent
from realtime.real_time_arbiter import RealTimeArbiter
from rules.rule_engine import RuleEngine
from text_io.board_parser import BoardParser
from text_io.move_notation import InvalidMoveNotation, MoveNotation

NO_SUCH_GAME = "no_such_game"
INVALID_NOTATION = "invalid_notation"
# Rejection reason while a game is frozen waiting for a player to reconnect.
PAUSED = "paused"


class GameService:
    """Routes network game commands to the right GameSession and creates
    sessions - the single place a "WQe2e5" string becomes a validated
    engine move. Holds the registry of live sessions by game_id, and
    builds each session's own Board/GameEngine stack so the server layer
    never touches the engine directly."""

    def __init__(self, publisher: Publisher) -> None:
        """publisher is handed to every session it creates (and used for
        its own GameStartedEvent)."""
        self._publisher = publisher
        self._sessions: dict[str, GameSession] = {}
        self._paused: set[str] = set()

    def create_session(self, game_id: str, white_user: str, black_user: str, board_text: str) -> GameSession:
        """Build a fresh game from board_text (this project's board
        notation): a Board, a GameEngine over it, and a GameSession
        wrapping both. Registers it under game_id and publishes a
        GameStartedEvent."""
        board = BoardParser.parse(board_text)
        engine = GameEngine(board, RuleEngine(), RealTimeArbiter(board))
        session = GameSession(game_id, board, engine, white_user, black_user, self._publisher)
        self._sessions[game_id] = session
        self._publisher.publish(GameStartedEvent(game_id, white_user, black_user))
        return session

    def handle_move(self, game_id: str, requesting_color: str, move: str) -> MoveResult:
        """Parse a "WQe2e5" move for game_id and apply it on behalf of
        requesting_color. Rejects an unknown game or malformed notation
        before touching any session."""
        session = self._sessions.get(game_id)
        if session is None:
            return MoveResult(False, NO_SUCH_GAME)
        if self.is_paused(game_id):
            return MoveResult(False, PAUSED)

        try:
            parsed = MoveNotation.parse(move, session.board_height)
        except InvalidMoveNotation:
            return MoveResult(False, INVALID_NOTATION)

        return session.request_move(parsed, requesting_color)

    def handle_jump(self, game_id: str, requesting_color: str, cell: str) -> MoveResult:
        """Parse an algebraic cell like "e2" for game_id and make that
        piece jump on behalf of requesting_color."""
        session = self._sessions.get(game_id)
        if session is None:
            return MoveResult(False, NO_SUCH_GAME)
        if self.is_paused(game_id):
            return MoveResult(False, PAUSED)

        try:
            position = MoveNotation.parse_cell(cell, session.board_height)
        except InvalidMoveNotation:
            return MoveResult(False, INVALID_NOTATION)

        return session.request_jump(position, requesting_color)

    def tick(self, game_id: str, elapsed_ms: int) -> None:
        """Advance one game's simulated time (driven by the server clock);
        a no-op for an unknown game_id."""
        session = self._sessions.get(game_id)
        if session is not None:
            session.tick(elapsed_ms)

    def tick_all(self, elapsed_ms: int) -> None:
        """Advance every live game's time by elapsed_ms - the server's
        periodic tick, so in-flight motions resolve into arrivals (and
        broadcasts) even when no client is sending commands. A paused game
        (a player is mid-reconnect) is frozen: its time does not advance."""
        for game_id, session in list(self._sessions.items()):
            if game_id not in self._paused:
                session.tick(elapsed_ms)

    def pause(self, game_id: str) -> None:
        """Freeze game_id's time and reject its moves, while a player who
        left is within their reconnect window."""
        self._paused.add(game_id)

    def resume(self, game_id: str) -> None:
        """Unfreeze game_id (the player reconnected, or the game ended)."""
        self._paused.discard(game_id)

    def is_paused(self, game_id: str) -> bool:
        """Whether game_id is currently frozen for a reconnect."""
        return game_id in self._paused

    def session(self, game_id: str) -> GameSession | None:
        """The live session for game_id, or None - used by the state-sync
        path to read a snapshot for broadcasting."""
        return self._sessions.get(game_id)
