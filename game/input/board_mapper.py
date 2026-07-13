from model.board import Board
from model.position import Position

CELL_SIZE = 100


class BoardMapper:
    """Input adapter: converts pixel coordinates into board cells. This is
    the only place that knows CELL_SIZE - the model layer never sees
    pixels. Ported from the row/col arithmetic that used to live inline in
    GameSession.click."""

    def __init__(self, board: Board) -> None:
        """board is used only to bounds-check mapped positions."""
        self._board = board

    def pixel_to_cell(self, x: int, y: int) -> Position | None:
        """Convert pixel coordinates to a board cell, or None if the
        pixel falls outside the board."""
        position = Position(y // CELL_SIZE, x // CELL_SIZE)

        if not self._board.in_bounds(position):
            return None

        return position
