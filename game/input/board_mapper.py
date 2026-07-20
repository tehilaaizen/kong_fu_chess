from __future__ import annotations

from model.board import Board
from model.position import Position

CELL_SIZE = 100


class BoardMapper:
    """Input adapter: converts pixel coordinates into board cells. This is
    the only place that knows the cell size in pixels - the model layer
    never sees pixels. Ported from the row/col arithmetic that used to
    live inline in GameSession.click.

    cell_size is a mutable instance field (defaulting to CELL_SIZE) so a
    window resize can retune it - the incoming coordinates are already
    board-local (MouseCommandExtractor subtracts the board's origin), so
    this class stays origin-unaware and only ever divides by the current
    cell size."""

    def __init__(self, board: Board, cell_size: int = CELL_SIZE) -> None:
        """board is used only to bounds-check mapped positions; cell_size
        is the current pixel size of one cell (updated on resize)."""
        self._board = board
        self.cell_size = cell_size

    def pixel_to_cell(self, x: int, y: int) -> Position | None:
        """Convert pixel coordinates to a board cell, or None if the
        pixel falls outside the board."""
        position = Position(y // self.cell_size, x // self.cell_size)

        if not self._board.in_bounds(position):
            return None

        return position
