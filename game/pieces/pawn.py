from pieces.piece import EMPTY_SQUARE, PieceRules, TokenBoard
from pieces.queen import Queen

FORWARD_DIRECTION: dict[str, int] = {"w": -1, "b": 1}


def _start_row(color: str, height: int) -> int:
    """The row a pawn of this color starts on, given the board's height."""
    return 0 if FORWARD_DIRECTION[color] == 1 else height - 1


def _promotion_row(color: str, height: int) -> int:
    """The row a pawn of this color promotes on, given the board's height."""
    return height - 1 if FORWARD_DIRECTION[color] == 1 else 0


class Pawn(PieceRules):
    letter = "P"

    def can_move(self, d_row: int, d_col: int, color: str) -> bool:
        """Forward one or two cells (straight), or one cell diagonally
        (capture only) - direction depends on color."""
        direction = FORWARD_DIRECTION[color]

        if d_col == 0:
            return d_row in (direction, 2 * direction)

        return d_row == direction and abs(d_col) == 1

    def is_path_clear(self, start: tuple[int, int], end: tuple[int, int], board: TokenBoard, color: str) -> bool:
        """Diagonal moves are only legal as a capture; a single forward
        step only onto an empty cell; a double forward step only from
        this pawn's own start row, with both the passed-through and
        destination cells empty."""
        d_row = end[0] - start[0]
        d_col = end[1] - start[1]
        destination = board.token_at(end[0], end[1])

        if d_col != 0:
            return destination != EMPTY_SQUARE  # diagonal move: only as a capture

        if abs(d_row) == 1:
            return destination == EMPTY_SQUARE  # single step: only onto an empty cell

        # double step: only from this pawn's own start row, and only if the
        # square it passes through is also empty
        if start[0] != _start_row(color, board.height):
            return False

        direction = FORWARD_DIRECTION[color]
        intermediate = board.token_at(start[0] + direction, start[1])

        return intermediate == EMPTY_SQUARE and destination == EMPTY_SQUARE

    def on_arrival(self, position: tuple[int, int], board: TokenBoard, color: str) -> str | None:
        """A pawn reaching the last row promotes to a queen."""
        if position[0] == _promotion_row(color, board.height):
            return Queen.letter

        return None
