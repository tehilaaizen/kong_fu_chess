from abc import ABC, abstractmethod
from typing import Protocol

from model.board import Board
from model.position import Position

EMPTY_SQUARE = "."


class TokenBoard(Protocol):
    """The subset of the legacy (session.py-era) board interface that
    PieceRules' older, token-based hooks (can_move/is_path_clear/
    on_arrival/travel_time) still rely on. Kept separate from
    model.board.Board, which the newer legal_destinations hook (see Rook)
    uses instead."""

    height: int
    width: int

    def token_at(self, row: int, col: int) -> str:
        ...


class PieceRules(ABC):
    """Stateless movement-rule strategy for one piece kind (one instance per
    kind, shared by every piece of that kind on the board - not to be
    confused with model.piece.Piece, which is one instance per actual piece
    sitting on the board). A subclass defines the letter used in board
    tokens (e.g. "K"), its movement shape, and its travel speed. Adding a
    new piece type means adding a new subclass here - nothing else in the
    engine changes."""

    letter: str | None = None
    speed_ms_per_cell: int = 1000

    @abstractmethod
    def can_move(self, d_row: int, d_col: int, color: str) -> bool:
        """Whether a move with these row/col deltas matches this piece's shape."""

    def is_path_clear(self, start: tuple[int, int], end: tuple[int, int], board: TokenBoard, color: str) -> bool:
        """Whether the squares strictly between start and end are empty.
        Non-sliding pieces (king, knight) keep the default: no blockers."""
        return True

    def on_arrival(self, position: tuple[int, int], board: TokenBoard, color: str) -> str | None:
        """Hook for piece-specific end-of-move effects (e.g. pawn promotion).
        Returns the new letter this piece becomes, or None to stay the same."""
        return None

    def travel_time(self, start: tuple[int, int], end: tuple[int, int]) -> int:
        """How many ms this piece takes to travel from start to end."""
        return chebyshev_distance(start, end) * self.speed_ms_per_cell


def _sign(n: int) -> int:
    """-1, 0, or 1 depending on the sign of n."""
    return (n > 0) - (n < 0)


def chebyshev_distance(start: tuple[int, int], end: tuple[int, int]) -> int:
    """The number of king-step moves (the larger of the row/col deltas)
    between two (row, col) points - used to time travel for every piece."""
    return max(abs(end[0] - start[0]), abs(end[1] - start[1]))


def sliding_path_is_clear(start: tuple[int, int], end: tuple[int, int], board: TokenBoard) -> bool:
    """Shared by any piece that moves in a straight line (rook/bishop/queen):
    walks the unit steps between start and end, exclusive of both ends."""
    row_step = _sign(end[0] - start[0])
    col_step = _sign(end[1] - start[1])

    row, col = start[0] + row_step, start[1] + col_step
    while (row, col) != end:
        if board.token_at(row, col) != EMPTY_SQUARE:
            return False
        row, col = row + row_step, col + col_step

    return True


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
