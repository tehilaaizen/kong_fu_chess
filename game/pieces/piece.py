from abc import ABC, abstractmethod

EMPTY_SQUARE = "."


class Piece(ABC):
    """Base class for a piece type. A subclass defines the letter used in
    board tokens (e.g. "K") and its movement shape. Adding a new piece type
    means adding a new subclass here - nothing else in the engine changes."""

    letter = None

    @abstractmethod
    def can_move(self, d_row, d_col):
        """Whether a move with these row/col deltas matches this piece's shape."""

    def is_path_clear(self, start, end, board):
        """Whether the squares strictly between start and end are empty.
        Non-sliding pieces (king, knight, pawn) keep the default: no blockers."""
        return True


def _sign(n):
    return (n > 0) - (n < 0)


def sliding_path_is_clear(start, end, board):
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
