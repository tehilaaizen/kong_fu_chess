from __future__ import annotations

from typing import Protocol, runtime_checkable

from engine.game_snapshot import GameSnapshot
from model.board import Board
from model.piece import Piece
from model.position import Position
from pieces.king import King
from realtime.real_time_arbiter import ArrivalEvent, RealTimeArbiter
from rules.rule_engine import OK, RuleEngine

GAME_OVER = "game_over"
MOTION_IN_PROGRESS = "motion_in_progress"
EMPTY_CELL = "empty_cell"
ALREADY_AIRBORNE = "already_airborne"
PIECE_RESTING = "piece_resting"


@runtime_checkable
class ArrivalObserver(Protocol):
    """Notified when a motion (move or jump-defense) logically arrived at
    its destination this tick."""

    def on_arrival(self, event: ArrivalEvent) -> None:
        """Handle the arrival described by event."""
        ...


@runtime_checkable
class MotionStartedObserver(Protocol):
    """Notified when a move was accepted and started travelling."""

    def on_motion_started(self, piece: Piece, source: Position, destination: Position, duration_ms: int) -> None:
        """Handle piece starting to travel; it arrives in duration_ms."""
        ...


@runtime_checkable
class JumpStartedObserver(Protocol):
    """Notified when a jump was accepted and the piece went airborne."""

    def on_jump_started(self, piece: Piece, position: Position, duration_ms: int) -> None:
        """Handle piece going airborne at position for duration_ms."""
        ...


@runtime_checkable
class RestStartedObserver(Protocol):
    """Notified when a piece entered a cooldown."""

    def on_rest_started(self, piece: Piece, duration_ms: int, label: str) -> None:
        """Handle piece resting for duration_ms; label is "long_rest"
        after a move or "short_rest" after a jump."""
        ...


@runtime_checkable
class GameOverObserver(Protocol):
    """Notified when the game ended (a king was captured)."""

    def on_game_over(self, loser_color: str) -> None:
        """Handle the game ending. loser_color is the color of the
        captured king ("w"/"b"); the winner is the other color."""
        ...


# Anything GameEngine can notify: an observer implements one narrow
# protocol per event it cares about, rather than a single wide one that
# forces empty no-op hooks for the events it ignores. add_observer works
# out which of these an object satisfies and subscribes it to exactly
# those - so ScoreData declares only on_arrival, while
# PieceAnimatorRegistry declares the four hooks it actually reacts to.
GameObserver = (
    ArrivalObserver | MotionStartedObserver | JumpStartedObserver | RestStartedObserver | GameOverObserver
)


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
        self._arrival_observers: list[ArrivalObserver] = []
        self._motion_started_observers: list[MotionStartedObserver] = []
        self._jump_started_observers: list[JumpStartedObserver] = []
        self._rest_started_observers: list[RestStartedObserver] = []
        self._game_over_observers: list[GameOverObserver] = []

    def is_game_over(self) -> bool:
        """Whether the game has already ended."""
        return self._game_over

    def mark_game_over(self) -> None:
        """Record that the game has ended. Idempotent."""
        self._game_over = True

    def add_observer(self, observer: GameObserver) -> None:
        """Subscribe observer to exactly those events it declares a hook
        for, so it never has to write empty no-op methods for the ones it
        ignores. Rejects an observer with no hooks at all, which would
        otherwise be silently subscribed to nothing - the likely cause is
        a misspelled hook name."""
        subscriptions = (
            (ArrivalObserver, self._arrival_observers),
            (MotionStartedObserver, self._motion_started_observers),
            (JumpStartedObserver, self._jump_started_observers),
            (RestStartedObserver, self._rest_started_observers),
            (GameOverObserver, self._game_over_observers),
        )

        matched = [observers for protocol, observers in subscriptions if isinstance(observer, protocol)]
        if not matched:
            raise ValueError(f"{type(observer).__name__} implements no observer hook")

        for observers in matched:
            observers.append(observer)

    def snapshot(self) -> GameSnapshot:
        """A read-only view of the current game state: every piece's
        identity, kind, color and cell. Animation state is not part of
        this - the view layer tracks it itself, driven by
        on_motion_started/on_jump_started/on_rest_started."""
        return GameSnapshot.from_board(self._board)

    def legal_destinations(self, source: Position) -> set[Position]:
        """Every cell the piece at source can currently move to or
        capture (empty if source is empty) - a read-only query the view
        uses to highlight a selected piece's options. Delegates to
        RuleEngine; never mutates state or starts a motion."""
        return self._rule_engine.legal_destinations(self._board, source)

    def _notify_arrival(self, event: ArrivalEvent) -> None:
        """Tell every arrival observer that event just arrived."""
        for observer in self._arrival_observers:
            observer.on_arrival(event)

    def _notify_motion_started(self, piece: Piece, source: Position, destination: Position, duration_ms: int) -> None:
        """Tell every motion-started observer that piece started moving."""
        for observer in self._motion_started_observers:
            observer.on_motion_started(piece, source, destination, duration_ms)

    def _notify_jump_started(self, piece: Piece, position: Position, duration_ms: int) -> None:
        """Tell every jump-started observer that piece started a jump."""
        for observer in self._jump_started_observers:
            observer.on_jump_started(piece, position, duration_ms)

    def _notify_rest_started(self, piece: Piece, duration_ms: int, label: str) -> None:
        """Tell every rest-started observer that piece started a
        cooldown."""
        for observer in self._rest_started_observers:
            observer.on_rest_started(piece, duration_ms, label)

    def _notify_game_over(self, loser_color: str) -> None:
        """Tell every game-over observer that the game just ended, passing
        the captured king's color so consumers can work out the winner."""
        for observer in self._game_over_observers:
            observer.on_game_over(loser_color)

    def request_move(self, source: Position, destination: Position) -> MoveResult:
        """Request a move from source to destination. Rejected outright
        with reason game_over if the game already ended, motion_in_progress
        if the source piece is itself still travelling from a previous
        move, or piece_resting if it's still in cooldown from its last
        move/jump. Other pieces moving at the same time are fine - this is
        real-time chess, so the guard is per-piece, not global. Otherwise
        delegated to RuleEngine; a legal move starts a motion through
        RealTimeArbiter (it does not relocate the piece itself - that
        happens only on arrival, once wait() advances time enough)."""
        if self.is_game_over():
            return MoveResult(False, GAME_OVER)

        piece = self._board.piece_at(source)
        if piece is not None and self._real_time_arbiter.is_moving(piece):
            return MoveResult(False, MOTION_IN_PROGRESS)

        if piece is not None and self._real_time_arbiter.is_resting(piece):
            return MoveResult(False, PIECE_RESTING)

        validation = self._rule_engine.validate_move(self._board, source, destination)
        if not validation.is_valid:
            return MoveResult(False, validation.reason)

        duration_ms = self._real_time_arbiter.start_motion(piece, source, destination)
        self._notify_motion_started(piece, source, destination, duration_ms)

        return MoveResult(True, validation.reason)

    def request_jump(self, position: Position) -> MoveResult:
        """Request the piece at position to jump (become briefly
        airborne): while airborne, an attacker arriving there is
        destroyed instead of capturing it. Unlike request_move, this
        never consults RuleEngine - a jump isn't a chess move, so there's
        no destination-legality question, only the same application-level
        guards (game_over, motion_in_progress, piece_resting) plus
        jump-specific ones (empty_cell, already_airborne). The
        motion_in_progress guard is per-piece: other pieces may be moving
        at the same time (real-time chess)."""
        if self.is_game_over():
            return MoveResult(False, GAME_OVER)

        piece = self._board.piece_at(position)
        if piece is None:
            return MoveResult(False, EMPTY_CELL)

        if self._real_time_arbiter.is_moving(piece):
            return MoveResult(False, MOTION_IN_PROGRESS)

        if self._real_time_arbiter.is_resting(piece):
            return MoveResult(False, PIECE_RESTING)

        if self._real_time_arbiter.is_airborne(position):
            return MoveResult(False, ALREADY_AIRBORNE)

        duration_ms = self._real_time_arbiter.start_jump(piece, position)
        self._notify_jump_started(piece, position, duration_ms)

        return MoveResult(True, OK)

    def wait(self, ms: int) -> None:
        """Advance simulated time by ms, delegating entirely to
        RealTimeArbiter - GameEngine never touches Board motion state
        directly. Notifies observers of each arrival and each cooldown
        that started this tick, and ends the game (notifying observers
        of that too) if any arrival captured a king."""
        events = self._real_time_arbiter.advance_time(ms)

        for event in events:
            self._notify_arrival(event)

            if not self.is_game_over() and self._ends_the_game(event.captured_piece):
                self.mark_game_over()
                self._notify_game_over(event.captured_piece.color)

        for rest_start in self._real_time_arbiter.take_rest_starts():
            self._notify_rest_started(rest_start.piece, rest_start.duration_ms, rest_start.label)

    def _ends_the_game(self, captured_piece: Piece | None) -> bool:
        """Whether capturing captured_piece ends the game. Only the king
        does today; kept as its own method (rather than an inline check
        scattered where captures are handled) so a different win
        condition can replace just this method later."""
        return captured_piece is not None and captured_piece.kind == King.letter
