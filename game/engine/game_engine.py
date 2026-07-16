from __future__ import annotations

from typing import Protocol

from engine.game_snapshot import GameSnapshot
from model.board import Board
from model.piece import Piece
from model.position import Position
from pieces.king import King
from realtime.real_time_arbiter import RealTimeArbiter
from rules.rule_engine import OK, RuleEngine

GAME_OVER = "game_over"
MOTION_IN_PROGRESS = "motion_in_progress"
EMPTY_CELL = "empty_cell"
ALREADY_AIRBORNE = "already_airborne"
PIECE_RESTING = "piece_resting"


class GameObserver(Protocol):
    """The only capability GameEngine needs from something that wants to
    be notified of state changes - lets tests inject a lightweight fake
    instead of a real view-layer object."""

    def on_snapshot(self, snapshot: GameSnapshot) -> None:
        ...


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
        self._observers: list[GameObserver] = []

    def is_game_over(self) -> bool:
        """Whether the game has already ended."""
        return self._game_over

    def mark_game_over(self) -> None:
        """Record that the game has ended. Idempotent."""
        self._game_over = True

    def add_observer(self, observer: GameObserver) -> None:
        """Register observer to be notified with a fresh snapshot every
        time wait() advances time - see _notify_observers."""
        self._observers.append(observer)

    def snapshot(self) -> GameSnapshot:
        """A read-only view of the current game state, including each
        piece's true animation state (move/resting/idle) from
        RealTimeArbiter."""
        return GameSnapshot.from_engine(self._board, self._real_time_arbiter)

    def _notify_observers(self) -> None:
        """Push a fresh snapshot to every registered observer. Called
        only from wait() - the only point where Board state can actually
        have changed (an arrival); a click that merely selects or starts
        a motion doesn't change Board, so it doesn't need its own notify.
        No-ops (skipping the snapshot build too) when nothing is
        registered - most tests never register an observer at all."""
        if not self._observers:
            return

        snapshot = self.snapshot()
        for observer in self._observers:
            observer.on_snapshot(snapshot)

    def request_move(self, source: Position, destination: Position) -> MoveResult:
        """Request a move from source to destination. Rejected outright
        with reason game_over if the game already ended, motion_in_progress
        if another motion is still travelling, or piece_resting if the
        source piece is still in cooldown from its last move/jump.
        Otherwise delegated to RuleEngine; a legal move starts a motion
        through RealTimeArbiter (it does not relocate the piece itself -
        that happens only on arrival, once wait() advances time enough)."""
        if self.is_game_over():
            return MoveResult(False, GAME_OVER)

        if self._real_time_arbiter.has_active_motion():
            return MoveResult(False, MOTION_IN_PROGRESS)

        piece = self._board.piece_at(source)
        if piece is not None and self._real_time_arbiter.is_resting(piece):
            return MoveResult(False, PIECE_RESTING)

        validation = self._rule_engine.validate_move(self._board, source, destination)
        if not validation.is_valid:
            return MoveResult(False, validation.reason)

        self._real_time_arbiter.start_motion(piece, source, destination)

        return MoveResult(True, validation.reason)

    def request_jump(self, position: Position) -> MoveResult:
        """Request the piece at position to jump (become briefly
        airborne): while airborne, an attacker arriving there is
        destroyed instead of capturing it. Unlike request_move, this
        never consults RuleEngine - a jump isn't a chess move, so there's
        no destination-legality question, only the same application-level
        guards (game_over, motion_in_progress, piece_resting) plus
        jump-specific ones (empty_cell, already_airborne)."""
        if self.is_game_over():
            return MoveResult(False, GAME_OVER)

        if self._real_time_arbiter.has_active_motion():
            return MoveResult(False, MOTION_IN_PROGRESS)

        piece = self._board.piece_at(position)
        if piece is None:
            return MoveResult(False, EMPTY_CELL)

        if self._real_time_arbiter.is_resting(piece):
            return MoveResult(False, PIECE_RESTING)

        if self._real_time_arbiter.is_airborne(position):
            return MoveResult(False, ALREADY_AIRBORNE)

        self._real_time_arbiter.start_jump(piece, position)

        return MoveResult(True, OK)

    def wait(self, ms: int) -> None:
        """Advance simulated time by ms, delegating entirely to
        RealTimeArbiter - GameEngine never touches Board motion state
        directly. Ends the game if any arrival captured a king, then
        notifies observers with a fresh snapshot."""
        events = self._real_time_arbiter.advance_time(ms)

        for event in events:
            if self._ends_the_game(event.captured_piece):
                self.mark_game_over()

        self._notify_observers()

    def _ends_the_game(self, captured_piece: Piece | None) -> bool:
        """Whether capturing captured_piece ends the game. Only the king
        does today; kept as its own method (rather than an inline check
        scattered where captures are handled) so a different win
        condition can replace just this method later."""
        return captured_piece is not None and captured_piece.kind == King.letter
