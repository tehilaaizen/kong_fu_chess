from __future__ import annotations

from typing import Protocol

from engine.game_engine import MoveResult
from engine.game_snapshot import GameSnapshot
from model.board import Board
from model.position import Position
from realtime.real_time_arbiter import ArrivalEvent
from messaging.application_events import GameEndedEvent, GameMoveAppliedEvent
from text_io.move_notation import ParsedMove

# Application-level rejection reasons, distinct from the engine's own
# (game_over/motion_in_progress/...) - these are ownership/identity checks
# the engine has no concept of.
NOT_YOUR_PIECE = "not_your_piece"
PIECE_MISMATCH = "piece_mismatch"
EMPTY_SOURCE = "empty_source"

WHITE = "w"
BLACK = "b"


class Publisher(Protocol):
    """Anything a session can publish application events onto - the real
    ApplicationMessageBus in production, a recording fake in tests. Kept
    as a Protocol so game_session doesn't depend on the concrete bus."""

    def publish(self, event: object) -> None:
        ...


class GameSession:
    """Owns one running game: its Board, GameEngine, the two players'
    identities, and a monotonic sequence number. Registers itself as the
    engine's observer, so every arrival/game-over is translated into an
    application event published (tagged with this game's id) on the
    injected Publisher. Every engine call for this game goes through here,
    behind ownership checks the engine itself has no concept of."""

    def __init__(
        self,
        game_id: str,
        board: Board,
        engine: "_Engine",
        white_user: str,
        black_user: str,
        publisher: Publisher,
    ) -> None:
        """board and engine are this game's own instances; white_user /
        black_user are the players' display identities; publisher receives
        the translated application events. Registers self as the engine's
        observer (for on_arrival / on_game_over)."""
        self._game_id = game_id
        self._board = board
        self._engine = engine
        self._white_user = white_user
        self._black_user = black_user
        self._publisher = publisher
        self._sequence = 0
        engine.add_observer(self)

    @property
    def game_id(self) -> str:
        """This game's stable id."""
        return self._game_id

    @property
    def board_height(self) -> int:
        """The board's height in cells - needed to parse algebraic move
        notation against this game."""
        return self._board.height

    def request_move(self, parsed: ParsedMove, requesting_color: str) -> MoveResult:
        """Apply a parsed move on behalf of the player playing
        requesting_color: rejected (before the engine) if the move is for
        the other color, if the source is empty, or if the piece there
        doesn't match the move's stated color/kind; otherwise delegated to
        the engine's own validation and motion start."""
        if parsed.color != requesting_color:
            return MoveResult(False, NOT_YOUR_PIECE)

        piece = self._board.piece_at(parsed.source)
        if piece is None:
            return MoveResult(False, EMPTY_SOURCE)
        if piece.color != parsed.color or piece.kind != parsed.kind:
            return MoveResult(False, PIECE_MISMATCH)

        return self._engine.request_move(parsed.source, parsed.destination)

    def request_jump(self, cell: Position, requesting_color: str) -> MoveResult:
        """Make the piece at cell jump on behalf of requesting_color -
        rejected if the cell is empty or holds an opponent's piece,
        otherwise delegated to the engine."""
        piece = self._board.piece_at(cell)
        if piece is None:
            return MoveResult(False, EMPTY_SOURCE)
        if piece.color != requesting_color:
            return MoveResult(False, NOT_YOUR_PIECE)

        return self._engine.request_jump(cell)

    def tick(self, elapsed_ms: int) -> None:
        """Advance this game's simulated time by elapsed_ms (driven by the
        server's clock), resolving any motion that arrives - which fires
        on_arrival / on_game_over back into this session."""
        self._engine.wait(elapsed_ms)

    def snapshot(self) -> GameSnapshot:
        """The current board state to broadcast to this game's clients."""
        return self._engine.snapshot()

    def on_arrival(self, event: ArrivalEvent) -> None:
        """Engine observer hook: a motion arrived - bump the sequence and
        publish it as a GameMoveAppliedEvent tagged with this game's id."""
        self._sequence += 1
        captured_kind = event.captured_piece.kind if event.captured_piece is not None else None
        self._publisher.publish(
            GameMoveAppliedEvent(
                game_id=self._game_id,
                sequence=self._sequence,
                source=event.source,
                destination=event.destination,
                color=event.piece.color,
                kind=event.piece.kind,
                captured_kind=captured_kind,
            )
        )

    def on_game_over(self, loser_color: str) -> None:
        """Engine observer hook: a king was captured - publish the winner
        (the other color) as a GameEndedEvent."""
        winner = WHITE if loser_color == BLACK else BLACK
        self._publisher.publish(GameEndedEvent(game_id=self._game_id, winner=winner))


class _Engine(Protocol):
    """The slice of GameEngine a session drives - lets tests inject a
    lightweight fake, and documents exactly what a session depends on."""

    def add_observer(self, observer: object) -> None:
        ...

    def request_move(self, source: Position, destination: Position) -> MoveResult:
        ...

    def request_jump(self, position: Position) -> MoveResult:
        ...

    def wait(self, ms: int) -> None:
        ...

    def snapshot(self) -> GameSnapshot:
        ...
