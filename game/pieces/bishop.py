from model.board import Board
from model.piece import Piece
from model.position import Position
from pieces.piece import PieceRules, TokenBoard, sliding_destinations, sliding_path_is_clear

DIAGONAL_DIRECTIONS: list[tuple[int, int]] = [(-1, -1), (-1, 1), (1, -1), (1, 1)]


class Bishop(PieceRules):
    letter = "B"

    def can_move(self, d_row: int, d_col: int, color: str) -> bool:
        """A bishop moves along a diagonal (equal row/col deltas)."""
        return abs(d_row) == abs(d_col)

    def is_path_clear(self, start: tuple[int, int], end: tuple[int, int], board: TokenBoard, color: str) -> bool:
        """Reuses the shared straight-line walk - it steps by the sign of
        each delta independently, so it works for diagonals too."""
        return sliding_path_is_clear(start, end, board)

    def legal_destinations(self, board: Board, piece: Piece) -> set[Position]:
        """Every cell reachable by sliding diagonally from piece's cell
        until blocked (capture-eligible on the first enemy piece
        encountered)."""
        return sliding_destinations(board, piece.cell, piece.color, DIAGONAL_DIRECTIONS)
