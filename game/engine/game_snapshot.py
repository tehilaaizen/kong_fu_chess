from __future__ import annotations

from typing import Protocol

from model.board import Board
from model.piece import Piece
from model.position import Position

IDLE = "idle"


class MotionAndRestQueries(Protocol):
    """The only capability GameSnapshot.from_engine needs from a
    real-time arbiter - lets tests inject a lightweight fake instead of
    the real RealTimeArbiter."""

    def is_moving(self, piece: Piece) -> bool:
        ...

    def resting_label(self, piece: Piece) -> str | None:
        ...


class PiecePlacement:
    """A read-only description of one piece's identity, kind, color,
    cell and current animation state - everything a Renderer needs to
    draw a piece, without exposing the live model.Piece object it came
    from."""

    def __init__(self, id: int, kind: str, color: str, cell: Position, state: str) -> None:
        self.id = id
        self.kind = kind
        self.color = color
        self.cell = cell
        self.state = state


class GameSnapshot:
    """Read-only view model for the view layer: board dimensions plus
    where every piece currently sits. Renderer must only ever see this,
    never a live Board/Piece, so the view layer can't accidentally
    mutate game state."""

    def __init__(self, board_width: int, board_height: int, pieces: list[PiecePlacement]) -> None:
        self.board_width = board_width
        self.board_height = board_height
        self.pieces = pieces

    @staticmethod
    def from_board(board: Board) -> "GameSnapshot":
        """Build a snapshot straight from board, with every piece's state
        defaulting to idle - no RealTimeArbiter is consulted, so this
        can't know about active motions/cooldowns. Used by static demos
        and tests with no engine attached; from_engine is the
        state-aware counterpart used once a real GameEngine is running."""
        pieces = [PiecePlacement(piece.id, piece.kind, piece.color, piece.cell, IDLE) for piece in board.pieces()]
        return GameSnapshot(board.width, board.height, pieces)

    @staticmethod
    def from_engine(board: Board, real_time_arbiter: MotionAndRestQueries) -> "GameSnapshot":
        """Build a snapshot from board plus real_time_arbiter, giving
        each piece its true current animation state: "move" while
        travelling, its resting label ("short_rest"/"long_rest") while in
        cooldown, otherwise "idle"."""
        pieces = []
        for piece in board.pieces():
            if real_time_arbiter.is_moving(piece):
                state = "move"
            else:
                state = real_time_arbiter.resting_label(piece) or IDLE
            pieces.append(PiecePlacement(piece.id, piece.kind, piece.color, piece.cell, state))
        return GameSnapshot(board.width, board.height, pieces)
