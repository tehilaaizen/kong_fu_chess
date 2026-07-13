from model.board import Board
from model.piece import Piece
from model.position import Position
from pieces.piece import PieceRules, TokenBoard, sliding_destinations, sliding_path_is_clear

ORTHOGONAL_DIRECTIONS: list[tuple[int, int]] = [(-1, 0), (1, 0), (0, -1), (0, 1)]


class Rook(PieceRules):
    letter = "R"

    def can_move(self, d_row: int, d_col: int, color: str) -> bool:
        """A rook moves along a single row or a single column."""
        return d_row == 0 or d_col == 0

    def is_path_clear(self, start: tuple[int, int], end: tuple[int, int], board: TokenBoard, color: str) -> bool:
        return sliding_path_is_clear(start, end, board)

    def legal_destinations(self, board: Board, piece: Piece) -> set[Position]:
        """Every cell reachable by sliding horizontally/vertically from
        piece's cell until blocked (capture-eligible on the first enemy
        piece encountered)."""
        return sliding_destinations(board, piece.cell, piece.color, ORTHOGONAL_DIRECTIONS)
