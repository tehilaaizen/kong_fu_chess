from model.board import Board
from model.piece import Piece
from model.position import Position
from pieces.piece import PieceRules, fixed_offset_destinations

ADJACENT_OFFSETS: list[tuple[int, int]] = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1), (0, 1),
    (1, -1), (1, 0), (1, 1),
]


class King(PieceRules):
    letter = "K"

    def can_move(self, d_row: int, d_col: int, color: str) -> bool:
        """A king moves exactly one cell in any direction."""
        return abs(d_row) <= 1 and abs(d_col) <= 1

    def legal_destinations(self, board: Board, piece: Piece) -> set[Position]:
        """Every adjacent cell (one step in any direction) from piece's cell."""
        return fixed_offset_destinations(board, piece.cell, piece.color, ADJACENT_OFFSETS)
