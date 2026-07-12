from model.position import Position
from pieces.piece import EMPTY_SQUARE


class BoardPrinter:
    """Text I/O adapter: renders a Board's logical occupancy back to text.
    Ported from Board.to_text()."""

    @staticmethod
    def to_text(board):
        rows = []
        for row in range(board.height):
            cells = [BoardPrinter._token_at(board, row, col) for col in range(board.width)]
            rows.append(" ".join(cells))

        return "\n".join(rows)

    @staticmethod
    def _token_at(board, row, col):
        piece = board.piece_at(Position(row, col))
        return EMPTY_SQUARE if piece is None else piece.color + piece.kind
