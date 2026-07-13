from model.board import Board
from model.position import Position
from pieces.piece import EMPTY_SQUARE


class BoardPrinter:
    """Text I/O adapter: renders a Board's logical occupancy back to text.
    Ported from Board.to_text()."""

    @staticmethod
    def to_text(board: Board) -> str:
        """Render board's current logical occupancy as row-per-line,
        space-separated token text (the same notation BoardParser reads)."""
        rows = []
        for row in range(board.height):
            cells = [BoardPrinter._token_at(board, row, col) for col in range(board.width)]
            rows.append(" ".join(cells))

        return "\n".join(rows)

    @staticmethod
    def _token_at(board: Board, row: int, col: int) -> str:
        """The notation token for one cell: "." if empty, else color+kind."""
        piece = board.piece_at(Position(row, col))
        return EMPTY_SQUARE if piece is None else piece.color + piece.kind
