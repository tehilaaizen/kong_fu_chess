from __future__ import annotations

from abc import ABC, abstractmethod

from model.board import Board
from model.piece import Piece
from model.position import Position

EMPTY_SQUARE = "."


class PieceRules(ABC):
    """Stateless movement-rule strategy for one piece kind (one instance per
    kind, shared by every piece of that kind on the board - not to be
    confused with model.piece.Piece, which is one instance per actual piece
    sitting on the board). A subclass defines the letter used in board
    tokens (e.g. "K") and its movement shape. Adding a new piece type means
    adding a new subclass here - nothing else in the engine changes."""

    letter: str | None = None

    @abstractmethod
    def legal_destinations(self, board: Board, piece: Piece) -> set[Position]:
        """All cells piece (an instance of this kind) can currently move
        to or capture, given board's current occupancy. Enemy-occupied
        destinations may be included (capture-eligible); this never
        mutates board or piece."""

    def on_piece_arrival(self, board: Board, piece: Piece) -> None:
        """Optional hook for piece-specific post-arrival effects (e.g.
        pawn promotion) - mutates piece in place; default is a no-op."""
        return None


def sliding_destinations(
    board: Board, cell: Position, color: str, directions: list[tuple[int, int]]
) -> set[Position]:
    """Shared by any PieceRules.legal_destinations that slides in straight
    lines (rook/bishop/queen): for each direction, walks cell by cell,
    collecting empty squares, then the first enemy-occupied square
    (capture-eligible) before stopping - never crossing any occupied
    square."""
    destinations: set[Position] = set()

    for d_row, d_col in directions:
        position = Position(cell.row + d_row, cell.col + d_col)

        while board.in_bounds(position):
            occupant = board.piece_at(position)

            if occupant is None:
                destinations.add(position)
            elif occupant.color != color:
                destinations.add(position)
                break
            else:
                break

            position = Position(position.row + d_row, position.col + d_col)

    return destinations


def fixed_offset_destinations(
    board: Board, cell: Position, color: str, offsets: list[tuple[int, int]]
) -> set[Position]:
    """Shared by any PieceRules.legal_destinations that only ever considers
    specific relative offsets from its cell, without sliding (knight/king):
    each offset is a legal destination when in bounds and not occupied by a
    friendly piece - blockers in between (if any) are irrelevant."""
    destinations: set[Position] = set()

    for d_row, d_col in offsets:
        position = Position(cell.row + d_row, cell.col + d_col)

        if not board.in_bounds(position):
            continue

        occupant = board.piece_at(position)
        if occupant is None or occupant.color != color:
            destinations.add(position)

    return destinations
