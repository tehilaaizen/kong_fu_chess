from abc import ABC, abstractmethod

EMPTY_SQUARE = "."


class PieceRules(ABC):
    """Stateless movement-rule strategy for one piece kind (one instance per
    kind, shared by every piece of that kind on the board - not to be
    confused with model.piece.Piece, which is one instance per actual piece
    sitting on the board). A subclass defines the letter used in board
    tokens (e.g. "K"), its movement shape, and its travel speed. Adding a
    new piece type means adding a new subclass here - nothing else in the
    engine changes."""

    letter = None
    speed_ms_per_cell = 1000

    @abstractmethod
    def can_move(self, d_row, d_col, color):
        """Whether a move with these row/col deltas matches this piece's shape."""

    def is_path_clear(self, start, end, board, color):
        """Whether the squares strictly between start and end are empty.
        Non-sliding pieces (king, knight) keep the default: no blockers."""
        return True

    def on_arrival(self, position, board, color):
        """Hook for piece-specific end-of-move effects (e.g. pawn promotion).
        Returns the new letter this piece becomes, or None to stay the same."""
        return None

    def travel_time(self, start, end):
        """How many ms this piece takes to travel from start to end."""
        return chebyshev_distance(start, end) * self.speed_ms_per_cell


def _sign(n):
    return (n > 0) - (n < 0)


def chebyshev_distance(start, end):
    return max(abs(end[0] - start[0]), abs(end[1] - start[1]))


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
