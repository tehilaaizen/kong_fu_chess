from model.board import Board
from model.position import Position
from realtime.real_time_arbiter import RealTimeArbiter
from rules.rule_engine import RuleEngine

GAME_OVER = "game_over"
MOTION_IN_PROGRESS = "motion_in_progress"


class MoveResult:
    """Outcome of GameEngine.request_move: whether the command was
    accepted, and a stable, machine-readable reason ("ok" when accepted)."""

    def __init__(self, is_accepted: bool, reason: str) -> None:
        self.is_accepted = is_accepted
        self.reason = reason


class GameEngine:
    """Application-service coordinator: the public command boundary used
    by Controller (and, later, TextTestRunner). Does not contain
    piece-specific movement logic, rendering, input parsing, or DSL
    parsing - those stay in their own layers.

    Whether the game has ended is tracked as plain state (_game_over) read
    only through is_game_over() and written only through mark_game_over() -
    so callers never depend on *why* the game ended. A future iteration can
    change what triggers mark_game_over() (e.g. king capture vs. some other
    win condition) without touching request_move at all."""

    def __init__(self, board: Board, rule_engine: RuleEngine, real_time_arbiter: RealTimeArbiter) -> None:
        """board is the single logical board this engine coordinates
        moves against; rule_engine decides whether a requested move is
        legal; real_time_arbiter tracks active motions and simulated time."""
        self._board = board
        self._rule_engine = rule_engine
        self._real_time_arbiter = real_time_arbiter
        self._game_over = False

    def is_game_over(self) -> bool:
        """Whether the game has already ended."""
        return self._game_over

    def mark_game_over(self) -> None:
        """Record that the game has ended. Idempotent."""
        self._game_over = True

    def request_move(self, source: Position, destination: Position) -> MoveResult:
        """Request a move from source to destination. Rejected outright
        with reason game_over if the game already ended, or
        motion_in_progress if another motion is still travelling.
        Otherwise delegated to RuleEngine; a legal move starts a motion
        through RealTimeArbiter (it does not relocate the piece itself -
        that happens only on arrival, once wait() advances time enough)."""
        if self.is_game_over():
            return MoveResult(False, GAME_OVER)

        if self._real_time_arbiter.has_active_motion():
            return MoveResult(False, MOTION_IN_PROGRESS)

        validation = self._rule_engine.validate_move(self._board, source, destination)
        if not validation.is_valid:
            return MoveResult(False, validation.reason)

        piece = self._board.piece_at(source)
        self._real_time_arbiter.start_motion(piece, source, destination)

        return MoveResult(True, validation.reason)

    def wait(self, ms: int) -> None:
        """Advance simulated time by ms, delegating entirely to
        RealTimeArbiter - GameEngine never touches Board motion state
        directly."""
        self._real_time_arbiter.advance_time(ms)
